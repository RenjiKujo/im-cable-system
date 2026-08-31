"""Streamlit エントリポイント（``streamlit run apps/web/ui/app.py``）。

ページ一覧は ``pages/`` 配下から自動検出される
（``1_Submit_Job.py`` → 投入フォーム、``2_Jobs.py`` → 一覧・詳細）。
"""

from __future__ import annotations

import sys
from pathlib import Path

# sys.path ブートストラップ（apps/web/ui/{app.py, pages/*.py} の 3 箇所で同形）。
# ``apps`` は配布物に入れない方針のため console_scripts が無く、
# `streamlit run <このファイル>` はスクリプト単体として実行される
# （リポジトリを editable/site-packages としてインストールしない）。
# そのままでは `from apps.web...` が解決できないため、各ページで自分の
# ファイル位置からリポジトリルートを逆算して sys.path へ足す。
# 3 ファイルとも `parents[N]` の N はそのファイルの `apps/` からの深さに合わせる。
_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import httpx  # noqa: E402
import streamlit as st  # noqa: E402

from apps.web.ui.api_client import (  # noqa: E402
    get_api_client,
    resolve_api_base_url,
)

st.set_page_config(page_title="im-cable-system", layout="wide")

st.title("im-cable-system — ジョブ投入型 Web 面")
st.markdown(
    "エンジン（`src/im_cable_system/`）を subprocess で回し、成果物を"
    "あとから確認できるようにする Web 面です。左のサイドバーから"
    "「Submit Job」で投入、「Jobs」で一覧・成果物の確認ができます。"
)

api_base_url = resolve_api_base_url()
st.caption(f"API base URL: `{api_base_url}`")

client = get_api_client(api_base_url)
try:
    client.healthz()
    st.success("API に接続できました。")
except httpx.HTTPError as exc:
    st.error(f"API に接続できません: {exc}")
