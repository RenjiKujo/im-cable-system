"""app 生成・lifespan（起動時の孤児ジョブ回収）。

``create_app`` はモジュール import 時点で DB へ触らないファクトリー。
起動には ``uvicorn apps.web.api.main:create_app --factory`` を使う
（module-level に ``app = create_app()`` を置くと import するだけで既定の
``jobs_root`` にディレクトリが作られてしまうため、あえて置かない）。
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from sqlalchemy.orm import Session, sessionmaker

from apps.web.api.routes_jobs import router as jobs_router
from apps.web.api.routes_presets import router as presets_router
from apps.web.api.supervisor import JobSupervisor
from apps.web.runner_gateway import ErrorKind, RunnerGatewaySettings
from apps.web.store import (
    IJobRepository,
    create_job_repository,
    create_session_factory,
    create_sqlite_engine,
    init_db,
)

_logger = logging.getLogger(__name__)


def _recover_orphan_jobs(session_factory: sessionmaker[Session]) -> None:
    """起動時に非終端だったジョブを ``failed(interrupted)`` へ倒す（嘘をつかない）。

    ``running`` だけでなく ``queued`` も対象にする。プロセスが落ちればキュー待ちの
    タスクも道連れで消えるため、``queued`` のまま残った行を放置すると、非終端ゆえ
    ``DELETE`` が 409 になり UI からも API からも消せない行になる。
    自動で再実行はしない（利用者が投入し直すか判断する）。
    """
    with session_factory() as session:
        repo: IJobRepository = create_job_repository(session)
        for record in repo.list_unfinished():
            _logger.warning(
                "recovering orphan job as interrupted (job_id=%s status=%s)",
                record.id,
                record.status,
            )
            repo.mark_finished(
                record.id,
                status="failed",
                finished_at=datetime.now(timezone.utc),
                exit_code=None,
                error_kind=ErrorKind.INTERRUPTED.value,
                error_message=(
                    f"server restarted while this job was {record.status}"
                ),
            )


def create_app(settings: RunnerGatewaySettings | None = None) -> FastAPI:
    """FastAPI app を生成する（テストからも同じ経路で作れるようファクトリー化）。"""
    resolved_settings = settings or RunnerGatewaySettings.from_env()
    engine = create_sqlite_engine(resolved_settings.jobs_root / "jobs.sqlite3")
    session_factory = create_session_factory(engine)

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        init_db(engine)
        _recover_orphan_jobs(session_factory)
        yield

    app = FastAPI(title="im-cable-system web", lifespan=lifespan)
    app.state.settings = resolved_settings
    app.state.session_factory = session_factory
    app.state.supervisor = JobSupervisor(
        session_factory=session_factory,
        max_concurrent_jobs=resolved_settings.max_concurrent_jobs,
    )

    app.include_router(jobs_router)
    app.include_router(presets_router)

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    return app
