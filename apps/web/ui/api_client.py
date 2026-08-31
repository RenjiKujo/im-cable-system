"""FastAPI 窓口への HTTP 呼び出しをここに閉じ込める。

``apps/web/ui`` から engine / ``apps.web.api`` / ``apps.web.runner_gateway`` への
import は行わない（UI は HTTP クライアント以外の依存を持たない）。
単一実装の薄いアダプタのため、インターフェース化はしない
（docs/apps/web/0_overview.md の境界での例外）。

``streamlit`` に依存する: ``st.cache_resource`` でプロセス内共有の
``httpx.Client``（接続プール）を保持する。``ApiClient`` 自体はリラン毎に
作り直す薄いラッパーとし、メソッド追加がキャッシュに残らないようにする。
"""

from __future__ import annotations

import os
from typing import Any

import httpx
import streamlit as st

_DEFAULT_BASE_URL = "http://127.0.0.1:8000"
_DEFAULT_TIMEOUT_SECONDS = 10.0


def resolve_api_base_url() -> str:
    """UI が向く FastAPI のベース URL を決める（環境変数優先）。"""
    return os.environ.get("IM_CABLE_SYSTEM_API_BASE_URL", _DEFAULT_BASE_URL)


@st.cache_resource(show_spinner=False)
def _get_http_client(base_url: str, timeout_seconds: float) -> httpx.Client:
    """プロセス内で共有する接続プール。引数は文字列・数値のみなのでキー化できる。"""
    return httpx.Client(base_url=base_url, timeout=timeout_seconds)


class ApiClient:
    """ジョブ投入型 Web API への薄いラッパー。"""

    def __init__(
        self,
        base_url: str | None = None,
        *,
        timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self._client = _get_http_client(
            base_url or resolve_api_base_url(), timeout_seconds
        )

    def healthz(self) -> dict[str, Any]:
        response = self._client.get("/healthz")
        response.raise_for_status()
        return response.json()

    def list_config_presets(self, mode: str) -> list[dict[str, Any]]:
        response = self._client.get(
            "/api/config-presets", params={"mode": mode}
        )
        response.raise_for_status()
        return response.json()["presets"]

    def list_input_presets(self, mode: str) -> dict[str, list[dict[str, Any]]]:
        response = self._client.get("/api/input-presets", params={"mode": mode})
        response.raise_for_status()
        return response.json()["presets_by_field"]

    def submit_job(
        self,
        mode: str,
        *,
        files: dict[str, tuple[str, bytes, str]],
        data: dict[str, str],
    ) -> dict[str, Any]:
        response = self._client.post(
            f"/api/jobs/{mode}", files=files, data=data
        )
        response.raise_for_status()
        return response.json()

    def list_jobs(
        self,
        *,
        mode: str | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        params: dict[str, str | int] = {"limit": limit, "offset": offset}
        if mode:
            params["mode"] = mode
        if status:
            params["status"] = status
        response = self._client.get("/api/jobs", params=params)
        response.raise_for_status()
        return response.json()["jobs"]

    def get_job(self, job_id: str) -> dict[str, Any]:
        response = self._client.get(f"/api/jobs/{job_id}")
        response.raise_for_status()
        return response.json()

    def list_fit_summaries(self, job_id: str) -> list[dict[str, Any]]:
        response = self._client.get(f"/api/jobs/{job_id}/fit-summaries")
        response.raise_for_status()
        return response.json()["summaries"]

    def get_job_log(self, job_id: str, *, tail_lines: int = 200) -> str:
        response = self._client.get(
            f"/api/jobs/{job_id}/log", params={"tail_lines": tail_lines}
        )
        response.raise_for_status()
        return response.text

    def list_artifacts(self, job_id: str) -> list[dict[str, Any]]:
        response = self._client.get(f"/api/jobs/{job_id}/artifacts")
        response.raise_for_status()
        return response.json()["artifacts"]

    def cancel_job(self, job_id: str) -> dict[str, Any]:
        response = self._client.post(f"/api/jobs/{job_id}/cancel")
        response.raise_for_status()
        return response.json()

    def delete_job(self, job_id: str) -> None:
        response = self._client.delete(f"/api/jobs/{job_id}")
        response.raise_for_status()


def get_api_client(base_url: str | None = None) -> ApiClient:
    """リラン毎に薄いラッパーを作り直す（接続プールは cache_resource で共有）。

    ``st.fragment(run_every=...)`` の単体再実行はスクリプト末尾を通らないため、
    ページ側でリラン毎にプールを生成／``close()`` すると閉じたクライアントを掴む。
    プールは ``_get_http_client`` で共有し、``close()`` しない。
    """
    return ApiClient(base_url)
