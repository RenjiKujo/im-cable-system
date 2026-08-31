"""ジョブ投入フォーム（モード別、入力ファイルはプリセット選択かアップロード）。"""

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
from apps.web.ui.views.job_views import PENDING_SELECT_JOB_ID_KEY  # noqa: E402
from apps.web.ui.views.submit_views import (  # noqa: E402
    ESTIMATE_PARAMS_FIELDS,
    FORWARD_FIELDS,
    render_input_file_field,
)

_MODES = (
    "forward_by_cartesian_grid",
    "estimate_params",
    "forward_by_operating_points",
)

st.title("Submit Job")

client = get_api_client()

mode = st.selectbox("mode", _MODES, key="mode")

st.subheader("config")
config_source = st.radio(
    "config の渡し方",
    ["プリセット選択", "config.yaml を丸ごとアップロード"],
    key="config-source",
)

data: dict[str, str] = {}
config_yaml_bytes: bytes | None = None

if config_source == "プリセット選択":
    try:
        presets = client.list_config_presets(mode)
    except httpx.HTTPError as exc:
        st.error(f"プリセット一覧を取得できません: {exc}")
        presets = []
    selected_preset = st.selectbox(
        "base_config",
        presets,
        format_func=lambda p: f"{p['name']} — {p['description']}",
        key=f"{mode}-base_config",
    )
    if selected_preset:
        data["base_config"] = selected_preset["name"]
        with st.expander("プリセットの中身"):
            st.caption(
                "`catalog` / `bounds` / `dump.base_dir` はこの画面では"
                "使いません（実行時に CLI 引数で上書きします）。"
            )
            st.code(selected_preset["yaml_text"], language="yaml")
    overrides_json = st.text_area(
        "主要キー上書き（JSON。空なら上書きなし）",
        value="",
        help='例: {"calculation": {"execute": {"data_processing": {"max_workers": 4}}}}',
    )
    if overrides_json.strip():
        data["overrides_json"] = overrides_json
else:
    uploaded_config = st.file_uploader("config.yaml", type=["yaml", "yml"])
    if uploaded_config is not None:
        config_yaml_bytes = uploaded_config.getvalue()

st.subheader("入力ファイル")
files: dict[str, tuple[str, bytes, str]] = {}

try:
    presets_by_field = client.list_input_presets(mode)
except httpx.HTTPError as exc:
    st.error(f"入力ファイルプリセットを取得できません: {exc}")
    presets_by_field = {}

field_specs = (
    ESTIMATE_PARAMS_FIELDS if mode == "estimate_params" else FORWARD_FIELDS
)
for spec in field_specs:
    render_input_file_field(
        mode=mode,
        spec=spec,
        presets=presets_by_field.get(spec.field, []),
        files=files,
        data=data,
    )

if config_yaml_bytes is not None:
    files["config_yaml"] = (
        "config.yaml",
        config_yaml_bytes,
        "application/x-yaml",
    )

if st.button("投入する", type="primary"):
    try:
        result = client.submit_job(mode, files=files, data=data)
    except httpx.HTTPStatusError as exc:
        detail = exc.response.json().get("detail", exc.response.text)
        st.error(f"投入に失敗しました（{exc.response.status_code}）: {detail}")
    except httpx.HTTPError as exc:
        st.error(f"API に接続できません: {exc}")
    else:
        st.session_state[PENDING_SELECT_JOB_ID_KEY] = result["job_id"]
        st.success(
            f"投入しました。job_id = `{result['job_id']}`"
            "（状態は Jobs ページで確認できます）"
        )
        st.page_link("pages/2_Jobs.py", label="Jobs で状態を見る")
        for warning in result.get("warnings", []):
            st.warning(warning)
