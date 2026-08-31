"""``JobSupervisor`` の開始前キャンセルと、起動そのものに失敗した場合の後始末。

起動失敗（``start_process`` が投げる経路）は API 経由では再現しにくいため、
``JobSupervisor`` を直接組み立てて検証する。``5_testing.md`` の
「内部実装の単体テスト」に当たるリーフ直 import。

``submit`` が ``asyncio.create_task`` を使うため、各シナリオは 1 つの
``asyncio.run`` の中で完結させる（pytest-asyncio は導入していない）。
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Coroutine
from datetime import datetime, timezone
from pathlib import Path
from typing import TypeVar

import pytest
from sqlalchemy.orm import Session, sessionmaker

from apps.web.api.supervisor import JobSupervisor
from apps.web.store import (
    IJobRepository,
    create_job_repository,
    create_session_factory,
    create_sqlite_engine,
    init_db,
)

_T = TypeVar("_T")


@pytest.fixture
def session_factory(tmp_path: Path) -> sessionmaker[Session]:
    engine = create_sqlite_engine(tmp_path / "jobs.sqlite3")
    init_db(engine)
    return create_session_factory(engine)


def _run(scenario: Callable[[], Coroutine[object, object, _T]]) -> _T:
    return asyncio.run(scenario())


async def _drain_background_tasks() -> None:
    """このループ上に残っている裏タスクの完了を待つ。"""
    pending = [
        task
        for task in asyncio.all_tasks()
        if task is not asyncio.current_task()
    ]
    if pending:
        await asyncio.gather(*pending, return_exceptions=True)


def _create_job(
    session_factory: sessionmaker[Session], job_id: str, tmp_path: Path
) -> None:
    with session_factory() as session:
        repo: IJobRepository = create_job_repository(session)
        repo.create(
            job_id=job_id,
            mode="estimate_params",
            job_dir=tmp_path / job_id,
            output_dir=tmp_path / job_id / "outputs",
            created_at=datetime.now(timezone.utc),
        )


def _status_of(
    session_factory: sessionmaker[Session], job_id: str
) -> tuple[str, str | None]:
    with session_factory() as session:
        repo: IJobRepository = create_job_repository(session)
        record = repo.get(job_id)
        assert record is not None
        return record.status, record.error_kind


class TestStartFailure:
    """起動そのものが失敗したときに ``queued`` で固着しない。"""

    def test_unlaunchable_argv_is_recorded_as_failed(
        self, session_factory: sessionmaker[Session], tmp_path: Path
    ) -> None:
        """python 実行パスが壊れている等で起動できない場合も終端まで倒す。

        倒れないと ``cancel``（実行中の登録簿に居ない）・``DELETE``（非終端なので
        409）・起動時回収（次回起動時にしか動かない）のいずれからも触れない行が
        台帳に残り、sqlite を直接編集するしか消す手段が無くなる。
        """

        async def scenario() -> None:
            supervisor = JobSupervisor(
                session_factory=session_factory, max_concurrent_jobs=2
            )
            _create_job(session_factory, "job-unlaunchable", tmp_path)
            supervisor.submit(
                job_id="job-unlaunchable",
                argv=[str(tmp_path / "does-not-exist"), "--input", "x"],
                cwd=tmp_path,
                run_log_path=tmp_path / "job-unlaunchable" / "run.log",
                timeout_seconds=10.0,
            )
            await _drain_background_tasks()

        _run(scenario)

        status, error_kind = _status_of(session_factory, "job-unlaunchable")
        assert status == "failed"
        assert error_kind == "unexpected"

    def test_registries_do_not_leak(
        self, session_factory: sessionmaker[Session], tmp_path: Path
    ) -> None:
        """終端に達した job_id は登録簿に残さない（常駐運用で単調増加させない）。"""

        async def scenario() -> JobSupervisor:
            supervisor = JobSupervisor(
                session_factory=session_factory, max_concurrent_jobs=2
            )
            _create_job(session_factory, "job-leak", tmp_path)
            supervisor.submit(
                job_id="job-leak",
                argv=[str(tmp_path / "does-not-exist")],
                cwd=tmp_path,
                run_log_path=tmp_path / "job-leak" / "run.log",
                timeout_seconds=10.0,
            )
            await _drain_background_tasks()
            return supervisor

        supervisor = _run(scenario)

        assert supervisor._tasks == {}
        assert supervisor._running_jobs == {}
        assert supervisor._cancel_requested == set()


class TestCancelBeforeStart:
    """キュー待ちの間にキャンセルされたジョブは起動しない。"""

    def test_cancelled_before_start_is_not_launched(
        self, session_factory: sessionmaker[Session], tmp_path: Path
    ) -> None:
        async def scenario() -> None:
            supervisor = JobSupervisor(
                session_factory=session_factory, max_concurrent_jobs=1
            )
            _create_job(session_factory, "job-cancel", tmp_path)
            await supervisor.cancel("job-cancel")
            supervisor.submit(
                job_id="job-cancel",
                argv=[str(tmp_path / "never-runs")],
                cwd=tmp_path,
                run_log_path=tmp_path / "job-cancel" / "run.log",
                timeout_seconds=10.0,
            )
            await _drain_background_tasks()

        _run(scenario)

        status, error_kind = _status_of(session_factory, "job-cancel")
        assert status == "cancelled"
        assert error_kind == "cancelled"
        # 起動していないので run.log は作られない。
        assert not (tmp_path / "job-cancel" / "run.log").exists()
