"""Streamlit UI。HTTP クライアント（``api_client``）以外の依存を持たない。

engine・``apps.web.api``・``apps.web.runner_gateway``・``apps.web.store`` の
いずれも import しない。ジョブ投入と成果物閲覧は、すべて FastAPI 窓口への
HTTP 経由で行う。
"""
