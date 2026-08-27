"""Jobs ページ（``pages/2_Jobs.py``）の描画関数群。

ページ本体（``pages/2_Jobs.py``）はここを呼ぶだけの「画面の流れが上から読める
スクリプト」にし、個々の描画ロジックはこちらへ寄せる。
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote
from zoneinfo import ZoneInfo

import httpx
import streamlit as st

from apps.web.ui.api_client import (
    ApiClient,
    get_api_client,
    resolve_api_base_url,
)

TERMINAL_STATUSES = {"succeeded", "failed", "cancelled"}
POLL_INTERVAL = "2s"
SELECTED_JOB_ID_KEY = "selected_job_id"
PENDING_SELECT_JOB_ID_KEY = "pending_select_job_id"
PENDING_DELETE_KEY = "pending_delete_job_id"
JOBS_TABLE_NONCE_KEY = "jobs_table_nonce"

_TIME_FORMAT = "%Y-%m-%d %H:%M:%S %Z"


def format_time(iso_text: str | None, tz_name: str) -> str:
    """API の UTC ISO 文字列を、そのジョブの Config TZ で表示用に整える。"""
    if not iso_text:
        return ""
    parsed = datetime.fromisoformat(iso_text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(ZoneInfo(tz_name)).strftime(_TIME_FORMAT)


def resolve_selected_job_id(
    *,
    jobs: list[dict[str, object]],
    selected_rows: list[int],
    pending_select_job_id: str,
    current_selected_job_id: str,
) -> str:
    """一覧の選択・投入直後の引き継ぎ・現在値から、表示する job_id を決める。

    優先順位は行選択 > 引き継ぎ > 現在値 > 空。``rows[0]`` が範囲外なら
    行選択は無視する（dataframe の選択 index が一覧とずれたときのガード）。
    """
    if selected_rows and selected_rows[0] < len(jobs):
        return str(jobs[selected_rows[0]]["id"])
    if pending_select_job_id:
        return pending_select_job_id
    return current_selected_job_id


def jobs_signature(
    jobs: list[dict[str, object]],
) -> tuple[tuple[str, str], ...]:
    """一覧監視用の指紋。``(id, status)`` の並びだけを見る。"""
    return tuple((str(job["id"]), str(job["status"])) for job in jobs)


def has_non_terminal_job(jobs: list[dict[str, object]]) -> bool:
    """一覧に終端前のジョブが1件でもあれば True。"""
    return any(
        str(job.get("status", "")) not in TERMINAL_STATUSES for job in jobs
    )


def job_rows(jobs: list[dict[str, object]]) -> list[dict[str, object]]:
    """一覧用の dataframe 行を作る。"""
    rows: list[dict[str, object]] = []
    for job in jobs:
        rows.append(
            {
                "job_id": str(job["id"]),
                "mode": str(job["mode"]),
                "status": str(job["status"]),
                "created_at": format_time(
                    str(job["created_at"]), str(job["timezone"])
                ),
                "exit": (
                    "" if job["exit_code"] is None else str(job["exit_code"])
                ),
                "error": (
                    "" if job["error_kind"] is None else str(job["error_kind"])
                ),
            }
        )
    return rows


def _artifact_url(job_id: str, rel_path: str, *, disposition: str) -> str:
    quoted = quote(rel_path, safe="/")
    return (
        f"{resolve_api_base_url()}/api/jobs/{job_id}/artifacts/{quoted}"
        f"?disposition={disposition}"
    )


def _http_error_detail(exc: httpx.HTTPStatusError) -> str:
    try:
        payload = exc.response.json()
    except ValueError:
        return exc.response.text or str(exc)
    detail = payload.get("detail") if isinstance(payload, dict) else None
    return str(detail) if detail else str(exc)


def _status_from_jobs(jobs: list[dict[str, object]], job_id: str) -> str | None:
    for job in jobs:
        if job["id"] == job_id:
            status = job["status"]
            return status if isinstance(status, str) else None
    return None


def resolve_status_for_polling(
    client: ApiClient, jobs: list[dict[str, object]], job_id: str
) -> str | None:
    """一覧にあればその status。無ければ 1 回だけ詳細を取る。失敗したら None。"""
    listed = _status_from_jobs(jobs, job_id)
    if listed is not None:
        return listed
    try:
        detail = client.get_job(job_id)
    except httpx.HTTPError:
        return None
    status = detail.get("status")
    return status if isinstance(status, str) else None


def _render_selected_summary(summary: dict[str, Any]) -> None:
    labels = summary["model_labels"]
    highlight = [
        f"`{key}` = `{labels.get(key, '')}`"
        for key in ("im_friction_windage", "im_stray_load")
        if labels.get(key) and labels.get(key) != "NONE"
    ]
    if highlight:
        st.markdown("**軸出力控除が有効です:** " + " / ".join(highlight))
    st.dataframe(
        [{"axis": key, "model": value} for key, value in labels.items()],
        width="stretch",
    )
    params = summary.get("fitted_parameters", [])
    if params:
        st.dataframe(params, width="stretch")
        if any(p.get("bound_status") in ("lower", "upper") for p in params):
            st.warning(
                "境界に張り付いています。探索範囲の見直しを検討してください"
            )
    st.write(summary.get("fit_metrics", {}))


def _render_fit_summaries(
    client: ApiClient, job_id: str
) -> tuple[str | None, int]:
    """組み合わせ比較・選択・詳細。

    Returns:
        ``(選択中の組み合わせ名, 件数)``。空なら ``(None, 0)``。
    """
    st.markdown("**推定結果サマリ**")
    try:
        summaries = client.list_fit_summaries(job_id)
    except httpx.HTTPError as exc:
        st.error(f"推定結果サマリを取得できません: {exc}")
        return None, 0

    if not summaries:
        st.info("推定結果サマリはまだありません。")
        return None, 0

    if len(summaries) >= 2:
        comparison_rows: list[dict[str, object]] = []
        for summary in summaries:
            # 列は API 応答の model_labels のキー順に従う（apps 側で軸を
            # 決め打ちしない。_render_selected_summary と同じ考え方）。
            labels = summary["model_labels"]
            metrics = summary["fit_metrics"]
            row: dict[str, object] = {"name": summary["name"], **labels}
            row["optimizer_success"] = metrics.get("optimizer_success")
            row["overall_rmse_weighted_residual"] = metrics.get(
                "overall_rmse_weighted_residual"
            )
            row["least_squares_cost"] = metrics.get("least_squares_cost")
            comparison_rows.append(row)
        st.dataframe(comparison_rows, width="stretch")
        best = min(
            summaries,
            key=lambda item: float(
                item["fit_metrics"]["overall_rmse_weighted_residual"]
            ),
        )
        st.caption(
            f"RMSE 最小: `{best['name']}` "
            f"（{best['fit_metrics']['overall_rmse_weighted_residual']}）"
        )

    names = [str(summary["name"]) for summary in summaries]
    selected_name = st.selectbox(
        "モデル組み合わせ", names, key=f"fit-combo-{job_id}"
    )
    selected = next(s for s in summaries if s["name"] == selected_name)
    _render_selected_summary(selected)
    return str(selected_name), len(summaries)


def _render_artifacts(
    job_id: str,
    artifacts: list[dict[str, object]],
    selected_name: str | None,
) -> None:
    st.markdown("**成果物**")
    visible = artifacts
    # 表示層のヒューリスティック: 成果物名は組み合わせ name を含む
    # （fig_*_{name}_{ts}.png / tbl_* / report_*）。API は走査結果を絞らない。
    if selected_name is not None:
        filter_on = st.checkbox(
            "選択中の組み合わせのみ表示",
            value=True,
            key=f"artifacts-filter-{job_id}",
        )
        if filter_on:
            visible = [
                a for a in artifacts if selected_name in str(a["rel_path"])
            ]
            if not visible:
                st.caption("選択中の組み合わせに該当する成果物はありません。")
                return

    for artifact in visible:
        rel_path = str(artifact["rel_path"])
        cols = st.columns([3, 1, 1])
        cols[0].write(f"`{rel_path}` ({artifact['size_bytes']} bytes)")
        if rel_path.lower().endswith(".png"):
            cols[1].link_button(
                "表示", _artifact_url(job_id, rel_path, disposition="inline")
            )
        cols[2].link_button(
            "DL", _artifact_url(job_id, rel_path, disposition="attachment")
        )


def render_job_detail_body(job_id: str) -> str | None:
    """ジョブ詳細を描画し、取得できた status を返す（失敗時は None）。"""
    client = get_api_client()
    try:
        detail = client.get_job(job_id)
    except httpx.HTTPStatusError as exc:
        st.error(
            f"job が見つかりません（{exc.response.status_code}）: {job_id}"
        )
        return None
    except httpx.HTTPError as exc:
        st.error(f"API に接続できません: {exc}")
        return None

    tz_name = str(detail["timezone"])
    st.markdown(
        f"**`{detail['id']}`** / `{detail['mode']}` / `{detail['status']}`"
    )
    st.dataframe(
        [
            {
                "item": "created_at",
                "value": format_time(detail.get("created_at"), tz_name),
            },
            {
                "item": "started_at",
                "value": format_time(detail.get("started_at"), tz_name),
            },
            {
                "item": "finished_at",
                "value": format_time(detail.get("finished_at"), tz_name),
            },
            {"item": "exit_code", "value": detail.get("exit_code")},
            {"item": "error_kind", "value": detail.get("error_kind")},
        ],
        hide_index=True,
        width="stretch",
    )
    error_message = detail.get("error_message")
    if error_message:
        st.error(error_message)

    selected_name: str | None = None
    if (
        detail.get("mode") == "estimate_params"
        and detail.get("status") == "succeeded"
    ):
        selected_name, n_summaries = _render_fit_summaries(client, job_id)
        if n_summaries < 2:
            selected_name = None

    if detail["status"] not in TERMINAL_STATUSES and st.button(
        "キャンセル", key=f"cancel-{job_id}"
    ):
        client.cancel_job(job_id)
        st.rerun()

    with st.expander("run.log（末尾 200 行）"):
        try:
            st.code(client.get_job_log(job_id, tail_lines=200))
        except httpx.HTTPError as exc:
            st.error(f"ログを取得できません: {exc}")

    try:
        artifacts = client.list_artifacts(job_id)
    except httpx.HTTPError as exc:
        st.error(f"成果物一覧を取得できません: {exc}")
        artifacts = []
    _render_artifacts(job_id, artifacts, selected_name)

    status = detail.get("status")
    return status if isinstance(status, str) else None


@st.fragment(run_every=POLL_INTERVAL)
def render_job_detail_polling(job_id: str) -> None:
    """終端になるまで 2 秒ごとに詳細を更新する。終端でアプリ全体へ戻す。"""
    if render_job_detail_body(job_id) in TERMINAL_STATUSES:
        st.rerun(scope="app")


@st.fragment(run_every=POLL_INTERVAL)
def render_jobs_refresh_watcher(
    signature: tuple[tuple[str, str], ...],
    *,
    mode: str | None,
    status: str | None,
) -> None:
    """非終端ジョブがある間だけ一覧を監視し、変化したらアプリ全体を再実行する。"""
    st.caption("一覧を自動更新しています…")
    try:
        jobs = get_api_client().list_jobs(mode=mode, status=status)
    except httpx.HTTPError:
        return
    if jobs_signature(jobs) != signature:
        st.rerun(scope="app")


def render_delete_confirmation(client: ApiClient) -> None:
    pending_id = st.session_state.get(PENDING_DELETE_KEY, "")
    if not pending_id:
        return
    st.warning(
        f"`{pending_id}` を削除します（成果物ごと消えます。元に戻せません）"
    )
    cols = st.columns(2)
    if cols[0].button("削除する", type="primary", key="confirm-delete"):
        try:
            client.delete_job(pending_id)
        except httpx.HTTPStatusError as exc:
            st.error(_http_error_detail(exc))
            return
        except httpx.HTTPError as exc:
            st.error(f"削除に失敗しました: {exc}")
            return
        st.session_state.pop(PENDING_DELETE_KEY, None)
        if st.session_state.get(SELECTED_JOB_ID_KEY) == pending_id:
            st.session_state.pop(SELECTED_JOB_ID_KEY, None)
        if st.session_state.get(PENDING_SELECT_JOB_ID_KEY) == pending_id:
            st.session_state.pop(PENDING_SELECT_JOB_ID_KEY, None)
        nonce = int(st.session_state.get(JOBS_TABLE_NONCE_KEY, 0))
        st.session_state[JOBS_TABLE_NONCE_KEY] = nonce + 1
        st.rerun()
    if cols[1].button("やめる", key="cancel-delete"):
        st.session_state.pop(PENDING_DELETE_KEY, None)
        st.rerun()
