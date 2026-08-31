"""ジョブ一覧・詳細（dataframe 単一行選択・削除・組み合わせ選択・ポーリング）。"""

from __future__ import annotations

import sys
from pathlib import Path

# sys.path 事情は apps/web/ui/app.py の同ブロックのコメントを参照。
_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import httpx  # noqa: E402
import streamlit as st  # noqa: E402

from apps.web.ui.api_client import get_api_client  # noqa: E402
from apps.web.ui.views.job_views import (  # noqa: E402
    JOBS_TABLE_NONCE_KEY,
    PENDING_DELETE_KEY,
    PENDING_SELECT_JOB_ID_KEY,
    SELECTED_JOB_ID_KEY,
    TERMINAL_STATUSES,
    has_non_terminal_job,
    job_rows,
    jobs_signature,
    render_delete_confirmation,
    render_job_detail_body,
    render_job_detail_polling,
    render_jobs_refresh_watcher,
    resolve_selected_job_id,
    resolve_status_for_polling,
)

_MODES = (
    "",
    "estimate_params",
    "forward_by_cartesian_grid",
    "forward_by_operating_points",
)
_STATUSES = ("", "queued", "running", "succeeded", "failed", "cancelled")

st.title("Jobs")

client = get_api_client()

with st.sidebar:
    st.subheader("一覧フィルタ")
    mode_filter = st.selectbox("mode", _MODES)
    status_filter = st.selectbox("status", _STATUSES)

mode_arg = mode_filter or None
status_arg = status_filter or None

try:
    jobs = client.list_jobs(mode=mode_arg, status=status_arg)
except httpx.HTTPError as exc:
    st.error(f"一覧を取得できません: {exc}")
    jobs = []

st.subheader("一覧")

selected_rows: list[int] = []
if jobs:
    nonce = int(st.session_state.get(JOBS_TABLE_NONCE_KEY, 0))
    event = st.dataframe(
        job_rows(jobs),
        hide_index=True,
        width="stretch",
        on_select="rerun",
        selection_mode="single-row",
        key=f"jobs-table-{mode_filter}-{status_filter}-{nonce}",
    )
    selection = event.get("selection", {})
    selected_rows = list(selection.get("rows", []))
else:
    st.info("ジョブがありません。")

pending_select = str(st.session_state.pop(PENDING_SELECT_JOB_ID_KEY, "") or "")
st.session_state[SELECTED_JOB_ID_KEY] = resolve_selected_job_id(
    jobs=jobs,
    selected_rows=selected_rows,
    pending_select_job_id=pending_select,
    current_selected_job_id=str(
        st.session_state.get(SELECTED_JOB_ID_KEY, "") or ""
    ),
)

if has_non_terminal_job(jobs):
    render_jobs_refresh_watcher(
        jobs_signature(jobs),
        mode=mode_arg,
        status=status_arg,
    )

selected_job_id = st.session_state.get(SELECTED_JOB_ID_KEY, "")
if selected_job_id and st.button("選択中のジョブを削除", key="delete-selected"):
    st.session_state[PENDING_DELETE_KEY] = selected_job_id
    st.rerun()
render_delete_confirmation(client)

st.subheader("詳細")
selected_job_id = st.session_state.get(SELECTED_JOB_ID_KEY, "")
if selected_job_id:
    status_for_poll = resolve_status_for_polling(client, jobs, selected_job_id)
    if status_for_poll is not None and status_for_poll not in TERMINAL_STATUSES:
        render_job_detail_polling(selected_job_id)
    else:
        render_job_detail_body(selected_job_id)
