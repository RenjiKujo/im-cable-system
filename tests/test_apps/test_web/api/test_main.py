"""main: healthz・起動時の孤児ジョブ回収（running → failed(interrupted)）。"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from apps.web.api.main import create_app
from apps.web.store import (
    create_job_repository,
    create_session_factory,
    create_sqlite_engine,
    init_db,
)
from tests.test_apps.test_web.api.conftest import make_settings


class TestHealthz:
    """死活監視エンドポイント。"""

    def test_returns_ok(self, client: TestClient) -> None:
        response = client.get("/healthz")

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestOrphanJobRecovery:
    """再起動時、running だったジョブを failed(interrupted) へ倒す。"""

    def test_running_job_is_marked_interrupted_on_startup(
        self, tmp_path: Path
    ) -> None:
        settings = make_settings(tmp_path)

        # 前回プロセスが running のまま落ちた状況を直接 DB へ作る。
        engine = create_sqlite_engine(settings.jobs_root / "jobs.sqlite3")
        init_db(engine)
        session_factory = create_session_factory(engine)
        with session_factory() as session:
            repo = create_job_repository(session)
            repo.create(
                job_id="orphan-1",
                mode="estimate_params",
                job_dir=settings.jobs_root / "orphan-1",
                output_dir=settings.jobs_root / "orphan-1" / "outputs",
                created_at=datetime.now(timezone.utc),
            )
            repo.mark_running(
                "orphan-1", started_at=datetime.now(timezone.utc), pid=999999
            )

        # 新しい app（サーバ再起動を模擬）を同じ jobs_root で起動する。
        app = create_app(settings=settings)
        with TestClient(app) as test_client:
            detail = test_client.get("/api/jobs/orphan-1").json()

        assert detail["status"] == "failed"
        assert detail["error_kind"] == "interrupted"
