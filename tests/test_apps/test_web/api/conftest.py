"""api テスト共通フィクスチャ。偽 runner を差し込んだ ``RunnerGatewaySettings`` を提供する。"""

from __future__ import annotations

import sys
import time
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from apps.web.api.main import create_app
from apps.web.runner_gateway import RunnerGatewaySettings

_REPO_ROOT = Path(__file__).resolve().parents[4]
_FAKE_RUNNERS_DIR = Path(__file__).resolve().parent / "data" / "fake_runners"


def make_settings(tmp_path: Path) -> RunnerGatewaySettings:
    """偽 runner を指す ``RunnerGatewaySettings`` を作る。"""
    return RunnerGatewaySettings(
        repo_root=_REPO_ROOT,
        python_executable=Path(sys.executable),
        runner_dir=_FAKE_RUNNERS_DIR,
        jobs_root=tmp_path / "jobs",
        max_concurrent_jobs=2,
        job_timeout_seconds=30.0,
    )


@pytest.fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    """lifespan（``create_all`` + 孤児ジョブ回収）まで通した TestClient。"""
    app = create_app(settings=make_settings(tmp_path))
    with TestClient(app) as test_client:
        yield test_client


def poll_until_terminal(
    client: TestClient, job_id: str, timeout: float = 10.0
) -> dict[str, object]:
    """状態が終端（succeeded/failed/cancelled）になるまでポーリングする。"""
    terminal = {"succeeded", "failed", "cancelled"}
    deadline = time.monotonic() + timeout
    detail: dict[str, object] = {}
    while time.monotonic() < deadline:
        response = client.get(f"/api/jobs/{job_id}")
        detail = response.json()
        if detail["status"] in terminal:
            return detail
        time.sleep(0.05)
    raise TimeoutError(f"job did not reach terminal state in time: {detail}")
