"""実行中タスクの登録簿と並行数制限。``runner_gateway`` と ``store`` の橋渡し。

``asyncio.create_subprocess_exec`` + ``asyncio.Semaphore(N)`` + タスク登録簿
（FastAPI と同じイベントループに乗せる。ローカル単一ホストで十分）。
ジョブ実行を別プロセス・別ホストのキューへ外出しする場合も、api 層が触るのは
``JobSupervisor`` の ``submit`` / ``cancel`` だけなので差し替え点はここに閉じる。
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session, sessionmaker

from apps.web.runner_gateway import (
    ErrorKind,
    JobStatus,
    RunningJob,
    start_process,
    terminate,
    wait_for_completion,
)
from apps.web.store import IJobRepository, create_job_repository

_logger = logging.getLogger(__name__)

_LOG_TAIL_LINES_FOR_ERROR_MESSAGE = 20


def _tail_text(path: Path, n_lines: int) -> str | None:
    if not path.is_file():
        return None
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    return "\n".join(lines[-n_lines:]) if lines else None


class JobSupervisor:
    """並行数制限・実行中タスクの登録・キャンセルの仲介。HTTP ルーティングは持たない。

    IF を切らずに具象のまま置く（``RunnerGatewaySettings`` / ``ApiClient`` と同じ
    扱い）。差し替え先が「実行基盤を外出しした版」の 1 つしか想定になく、
    抽象を 1 枚挟んでも実装が 1 つのままになるため。
    """

    def __init__(
        self,
        *,
        session_factory: sessionmaker[Session],
        max_concurrent_jobs: int,
    ) -> None:
        self._session_factory = session_factory
        self._semaphore = asyncio.Semaphore(max_concurrent_jobs)
        self._running_jobs: dict[str, RunningJob] = {}
        self._cancel_requested: set[str] = set()
        self._tasks: dict[str, asyncio.Task[None]] = {}

    def submit(
        self,
        *,
        job_id: str,
        argv: list[str],
        cwd: Path,
        run_log_path: Path,
        timeout_seconds: float,
        preamble_lines: list[str] | None = None,
    ) -> None:
        """バックグラウンドタスクとしてジョブを登録する（即時リターン。計算完了を待たない）。"""
        self._tasks[job_id] = asyncio.create_task(
            self._run(
                job_id=job_id,
                argv=argv,
                cwd=cwd,
                run_log_path=run_log_path,
                timeout_seconds=timeout_seconds,
                preamble_lines=preamble_lines,
            )
        )

    async def cancel(self, job_id: str) -> bool:
        """実行中ジョブへキャンセルを要求する。

        Returns:
            実行中だった場合 ``True``。キュー待ち／未実行の場合でも
            以降の起動を抑止する（``_cancel_requested`` へ登録する）ため、
            戻り値は「即時に kill シグナルを送ったか」の目安として扱う。
        """
        self._cancel_requested.add(job_id)
        job = self._running_jobs.get(job_id)
        if job is None:
            return False
        await terminate(job)
        return True

    async def _run(
        self,
        *,
        job_id: str,
        argv: list[str],
        cwd: Path,
        run_log_path: Path,
        timeout_seconds: float,
        preamble_lines: list[str] | None,
    ) -> None:
        """セマフォを取得し、開始前キャンセル済みなら起動せず ``_execute`` へ渡す。

        ``_execute`` が投げた場合は ``failed(unexpected)`` へ倒す。倒さずに抜けると
        台帳が ``queued`` のまま残り、``cancel``（``_running_jobs`` に居ないので
        何もしない）・``DELETE``（非終端なので 409）・起動時回収のいずれからも
        触れない行になり、sqlite を直接編集するしか消す手段が無くなる。
        とくに ``start_process`` は ``_execute`` の try の外側にあたるため、
        python 実行パスが無い・実行権限が無い・fork に失敗した場合はここでしか
        捕まえられない。
        """
        try:
            async with self._semaphore:
                if job_id in self._cancel_requested:
                    self._finish(
                        job_id,
                        status=JobStatus.CANCELLED,
                        exit_code=None,
                        error_kind=ErrorKind.CANCELLED,
                        error_message="cancelled before start",
                    )
                    return
                try:
                    await self._execute(
                        job_id=job_id,
                        argv=argv,
                        cwd=cwd,
                        run_log_path=run_log_path,
                        timeout_seconds=timeout_seconds,
                        preamble_lines=preamble_lines,
                    )
                except Exception as exc:  # noqa: BLE001
                    _logger.exception(
                        "job task failed outside the process lifecycle "
                        "(job_id=%s)",
                        job_id,
                    )
                    self._finish_quietly(
                        job_id,
                        status=JobStatus.FAILED,
                        exit_code=None,
                        error_kind=ErrorKind.UNEXPECTED,
                        error_message=f"{type(exc).__name__}: {exc}",
                    )
        finally:
            # 登録簿は終端に達した時点で捨てる（常駐運用で単調増加させない）。
            self._cancel_requested.discard(job_id)
            self._tasks.pop(job_id, None)

    async def _execute(
        self,
        *,
        job_id: str,
        argv: list[str],
        cwd: Path,
        run_log_path: Path,
        timeout_seconds: float,
        preamble_lines: list[str] | None,
    ) -> None:
        """起動 → 完了待ち → 終了記録（セマフォ確保後の本体）。"""
        job = await start_process(
            argv,
            cwd=cwd,
            run_log_path=run_log_path,
            preamble_lines=preamble_lines,
        )
        self._running_jobs[job_id] = job
        self._mark_running(job_id, pid=job.process.pid)
        try:
            result = await wait_for_completion(job, timeout_seconds)
        finally:
            # ``_tasks`` / ``_cancel_requested`` は ``_run`` の finally が捨てる
            # （起動自体に失敗した経路もそちらで拾うため、1 箇所に寄せる）。
            self._running_jobs.pop(job_id, None)

        if job_id in self._cancel_requested:
            self._finish(
                job_id,
                status=JobStatus.CANCELLED,
                exit_code=result.exit_code,
                error_kind=ErrorKind.CANCELLED,
                error_message="cancelled by user",
            )
            return

        error_message = (
            _tail_text(run_log_path, _LOG_TAIL_LINES_FOR_ERROR_MESSAGE)
            if result.status == JobStatus.FAILED
            else None
        )
        self._finish(
            job_id,
            status=result.status,
            exit_code=result.exit_code,
            error_kind=result.error_kind,
            error_message=error_message,
        )

    @contextmanager
    def _repository(self) -> Iterator[IJobRepository]:
        """バックグラウンドタスク用の台帳リポジトリ。

        ``JobSupervisor`` はリクエスト外（イベントループ上の裏タスク）で動くため
        ``api/dependencies.py`` の ``Depends`` は使えない（``Depends`` は FastAPI が
        リクエストごとに解決する仕組みで、ここには「リクエスト」自体が無い）。
        セッションは呼び出しごとに開いて閉じる。裏タスクは寿命が長く、
        1 本を保持し続けると identity map が古い行を返し続けるため。
        """
        with self._session_factory() as session:
            yield create_job_repository(session)

    def _mark_running(self, job_id: str, *, pid: int | None) -> None:
        with self._repository() as repo:
            repo.mark_running(
                job_id, started_at=datetime.now(timezone.utc), pid=pid
            )

    def _finish(
        self,
        job_id: str,
        *,
        status: JobStatus,
        exit_code: int | None,
        error_kind: ErrorKind | None,
        error_message: str | None,
    ) -> None:
        with self._repository() as repo:
            repo.mark_finished(
                job_id,
                status=status.value,
                finished_at=datetime.now(timezone.utc),
                exit_code=exit_code,
                error_kind=error_kind.value if error_kind is not None else None,
                error_message=error_message,
            )

    def _finish_quietly(
        self,
        job_id: str,
        *,
        status: JobStatus,
        exit_code: int | None,
        error_kind: ErrorKind | None,
        error_message: str | None,
    ) -> None:
        """既に失敗を処理している最中の ``_finish``。二重障害でも例外を出さない。

        台帳行が既に消えている場合（``mark_finished`` は ``ValueError``）にここで
        投げ返すと、呼び出し元の except 節から例外が抜けて「タスクが黙って死ぬ」
        元の壊れ方に戻る。倒す先が無いこと自体は異常ではないのでログに留める。
        """
        try:
            self._finish(
                job_id,
                status=status,
                exit_code=exit_code,
                error_kind=error_kind,
                error_message=error_message,
            )
        except Exception:  # noqa: BLE001
            _logger.exception(
                "could not record the failure in the ledger (job_id=%s)", job_id
            )
