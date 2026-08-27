"""投入・一覧・詳細・ログ・成果物・fit-summaries・キャンセル・削除。

投入は必ず 202 で即返し、計算を待たない（UI は詳細エンドポイントをポーリングする）。

目安の 200 行は超える（このファイル単体で 8 エンドポイント + `_to_detail`）。
超過分の大半は ``submit_job``（フォーム読み取り → config マテリアライズ →
台帳登録 → supervisor 投入の 4 段オーケストレーション）と、``cancel_job`` の
identity map 回避コメント（正確性のために残す判断。詳細は同関数の docstring）。
どちらも切り詰めると読みにくくなるため、行数より可読性を優先してそのままにしている。
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Annotated, Literal

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Request,
    Response,
    status,
)
from fastapi.responses import FileResponse, PlainTextResponse

from apps.web.api.dependencies import (
    ExistingJob,
    JobRepository,
    Settings,
    Supervisor,
    get_job_repository,
)
from apps.web.api.input_validation import InputContractError
from apps.web.api.schemas import (
    ArtifactListResponse,
    ArtifactResponse,
    FitSummaryListResponse,
    FitSummaryResponse,
    JobDetailResponse,
    JobListResponse,
    JobSubmitResponse,
)
from apps.web.api.submission_form import SubmissionForm
from apps.web.engine_contract import list_fitted_catalogs
from apps.web.runner_gateway import (
    JobLayout,
    JobMode,
    JobStatus,
    build_command,
    delete_job_dir,
    list_artifacts,
    materialize_config,
    read_config_timezone,
    resolve_artifact_path,
    write_cmd_json,
)
from apps.web.store import IJobRepository, JobRecord

router = APIRouter()

_logger = logging.getLogger(__name__)

_DEFAULT_TAIL_LINES = 200
_TERMINAL_STATUSES = frozenset(
    {
        JobStatus.SUCCEEDED.value,
        JobStatus.FAILED.value,
        JobStatus.CANCELLED.value,
    }
)


def _discard_job_dir(settings: Settings, layout: JobLayout) -> None:
    """投入を成立させずに終わるときの後始末。

    ``JobLayout.create`` はフォーム検証より前にディレクトリを作る（保存先が
    決まらないと入力を受け取れないため）。検証で弾いた場合は台帳行も作られない
    ので、消さずに抜けると台帳から辿れないディレクトリが ``jobs_root`` に
    溜まり続け、UI からも API からも消せなくなる。

    後始末自体の失敗で投入エラーを覆い隠さない（ログに留めて元の例外を活かす）。
    """
    try:
        delete_job_dir(settings.jobs_root, layout.job_dir)
    except OSError:
        _logger.exception(
            "could not clean up the rejected job directory (job_dir=%s)",
            layout.job_dir,
        )


def _to_detail(record: JobRecord) -> JobDetailResponse:
    """``timezone`` は ``runner_gateway`` 依存なのでスキーマへ持ち込まず、ここで合成する。"""
    return JobDetailResponse.model_validate(
        {**asdict(record), "timezone": read_config_timezone(record.job_dir)}
    )


@router.post(
    "/api/jobs/{mode}",
    response_model=JobSubmitResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def submit_job(
    mode: str,
    request: Request,
    settings: Settings,
    repo: JobRepository,
    supervisor: Supervisor,
) -> JobSubmitResponse:
    """multipart 投入 → 202 ``{job_id, status: "queued"}``。計算完了は待たない。

    ``await request.form()`` で multipart ボディを読む必要があるため、
    ``Depends`` だけでは足りず ``Request`` を直接受け取る（FastAPI 側の制約）。
    """
    try:
        job_mode = JobMode(mode)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"未知の mode です: {mode}",
        ) from exc

    form = await request.form()
    job_id = uuid.uuid4().hex
    layout = JobLayout.create(settings.jobs_root, job_id)
    submission = SubmissionForm(
        form, mode=job_mode, layout=layout, settings=settings
    )

    try:
        base_yaml_text, overrides = await submission.resolve_config()
        materialize_result = materialize_config(
            layout, base_yaml_text=base_yaml_text, overrides=overrides
        )
        inputs, warnings = await submission.build_inputs()
    except InputContractError as exc:
        # input_validation.py はドメイン例外だけを投げ、HTTPException への
        # 翻訳はここへ集約する（検証側に HTTP を持ち込まない）。
        _discard_job_dir(settings, layout)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    except Exception:
        # SubmissionForm が直接投げる 400（必須欠落・アップロードとプリセットの
        # 同時指定・未知プリセット名・overrides_json の JSON 不正）と想定外も同じ。
        _discard_job_dir(settings, layout)
        raise

    argv = build_command(job_mode, layout, inputs, settings)
    write_cmd_json(layout, argv, {"MPLBACKEND": "Agg"})

    preamble_lines: list[str] = []
    if materialize_result.removed_dump_base_dir:
        preamble_lines.append(
            "[web] removed dump.base_dir from the supplied config.yaml "
            "(using --dump-base-dir instead; see docs/apps/web/0_overview.md)"
        )

    repo.create(
        job_id=job_id,
        mode=job_mode.value,
        job_dir=layout.job_dir,
        output_dir=layout.output_dir,
        created_at=datetime.now(timezone.utc),
    )

    supervisor.submit(
        job_id=job_id,
        argv=argv,
        cwd=settings.repo_root,
        run_log_path=layout.run_log_path,
        timeout_seconds=settings.job_timeout_seconds,
        preamble_lines=preamble_lines,
    )

    return JobSubmitResponse(
        job_id=job_id, status="queued", warnings=list(warnings)
    )


@router.get("/api/jobs", response_model=JobListResponse)
async def list_jobs(
    repo: JobRepository,
    mode: str | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = 50,
    offset: int = 0,
) -> JobListResponse:
    """ジョブ一覧（``mode`` / ``status`` フィルタ、ページング）。"""
    records = repo.list(
        mode=mode, status=status_filter, limit=limit, offset=offset
    )
    return JobListResponse(jobs=[_to_detail(r) for r in records])


@router.get("/api/jobs/{job_id}", response_model=JobDetailResponse)
async def get_job(record: ExistingJob) -> JobDetailResponse:
    """状態・時刻・終了コード・エラー。"""
    return _to_detail(record)


@router.get("/api/jobs/{job_id}/log", response_class=PlainTextResponse)
async def get_job_log(
    record: ExistingJob, tail_lines: int = _DEFAULT_TAIL_LINES
) -> str:
    """``run.log`` の末尾（stdout + stderr マージ済み）。"""
    log_path = record.job_dir / "run.log"
    if not log_path.is_file():
        return ""
    lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
    return "\n".join(lines[-tail_lines:])


@router.get("/api/jobs/{job_id}/artifacts", response_model=ArtifactListResponse)
async def get_job_artifacts(record: ExistingJob) -> ArtifactListResponse:
    """``outputs/`` の実行時走査結果。"""
    infos = list_artifacts(record.output_dir)
    return ArtifactListResponse(
        artifacts=[ArtifactResponse.model_validate(info) for info in infos]
    )


@router.get(
    "/api/jobs/{job_id}/fit-summaries", response_model=FitSummaryListResponse
)
async def get_job_fit_summaries(record: ExistingJob) -> FitSummaryListResponse:
    """全 ``report_model_*.yaml`` を name 昇順で返す。0 件は空リスト。"""
    try:
        views = list_fitted_catalogs(record.output_dir / "reports")
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc
    return FitSummaryListResponse(
        summaries=[FitSummaryResponse.model_validate(view) for view in views]
    )


@router.get("/api/jobs/{job_id}/artifacts/{rel_path:path}")
async def download_job_artifact(
    record: ExistingJob,
    rel_path: str,
    disposition: Literal["inline", "attachment"] = "inline",
) -> FileResponse:
    """成果物ファイル本体（パストラバーサル対策済み）。

    ``disposition`` 省略時は ``inline``（既存契約。PNG は別タブ表示）。
    """
    try:
        resolved = resolve_artifact_path(record.output_dir, rel_path)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    return FileResponse(
        resolved,
        filename=resolved.name,
        content_disposition_type=disposition,
    )


@router.post("/api/jobs/{job_id}/cancel", response_model=JobDetailResponse)
async def cancel_job(
    record: ExistingJob,
    supervisor: Supervisor,
    fresh_repo: Annotated[
        IJobRepository, Depends(get_job_repository, use_cache=False)
    ],
) -> JobDetailResponse:
    """terminate → 猶予後 kill。

    ``fresh_repo`` は ``use_cache=False`` で別セッションを新規に開く。
    SQLAlchemy の identity map は同一セッション内で一度読んだ行を再クエリ
    しないため、キャンセル直後の状態を確実に読み直すには別セッションが要る。
    """
    await supervisor.cancel(record.id)
    updated = fresh_repo.get(record.id)
    if updated is None:
        # ``ExistingJob`` で存在を確認した後、キャンセル中に別リクエストが
        # 消した場合のみ通る。読み直せない以上 404 を返すしかない。
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"job が見つかりません: {record.id}",
        )
    return _to_detail(updated)


@router.delete("/api/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    record: ExistingJob, repo: JobRepository, settings: Settings
) -> Response:
    """終端ジョブのディレクトリと台帳行を消す。非終端は 409。"""
    if record.status not in _TERMINAL_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "実行中のジョブは削除できません。先にキャンセルしてください。"
            ),
        )
    delete_job_dir(settings.jobs_root, record.job_dir)
    repo.delete(record.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
