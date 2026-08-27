"""repository: ジョブ台帳の CRUD 契約。"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from sqlalchemy.orm import Session, sessionmaker

from apps.web.store import (
    IJobRepository,
    create_job_repository,
    create_session_factory,
    create_sqlite_engine,
    init_db,
)


@pytest.fixture
def session_factory(tmp_path: Path) -> sessionmaker[Session]:
    engine = create_sqlite_engine(tmp_path / "jobs.sqlite3")
    init_db(engine)
    return create_session_factory(engine)


def _repo(session_factory: sessionmaker[Session]) -> IJobRepository:
    return create_job_repository(session_factory())


class TestCreateAndGet:
    """新規作成と単体取得。"""

    def test_create_returns_queued_record(
        self, session_factory: sessionmaker[Session]
    ) -> None:
        repo = _repo(session_factory)
        created_at = datetime.now(timezone.utc)

        record = repo.create(
            job_id="job-1",
            mode="estimate_params",
            job_dir=Path("/jobs/job-1"),
            output_dir=Path("/jobs/job-1/outputs"),
            created_at=created_at,
        )

        assert record.id == "job-1"
        assert record.status == "queued"
        assert record.mode == "estimate_params"
        assert record.job_dir == Path("/jobs/job-1")
        assert record.exit_code is None

    def test_get_returns_none_for_missing_job(
        self, session_factory: sessionmaker[Session]
    ) -> None:
        repo = _repo(session_factory)
        assert repo.get("does-not-exist") is None

    def test_get_returns_created_job(
        self, session_factory: sessionmaker[Session]
    ) -> None:
        repo = _repo(session_factory)
        repo.create(
            job_id="job-1",
            mode="estimate_params",
            job_dir=Path("/jobs/job-1"),
            output_dir=Path("/jobs/job-1/outputs"),
            created_at=datetime.now(timezone.utc),
        )

        found = repo.get("job-1")

        assert found is not None
        assert found.id == "job-1"

    def test_get_restores_naive_datetimes_as_utc(
        self, session_factory: sessionmaker[Session]
    ) -> None:
        repo = _repo(session_factory)
        created_at = datetime.now(timezone.utc)
        repo.create(
            job_id="job-1",
            mode="estimate_params",
            job_dir=Path("/jobs/job-1"),
            output_dir=Path("/jobs/job-1/outputs"),
            created_at=created_at,
        )

        found = repo.get("job-1")

        assert found is not None
        assert found.created_at.tzinfo is not None
        assert found.created_at.utcoffset() == timedelta(0)
        assert found.created_at == created_at


class TestList:
    """一覧・フィルタ・ページング。"""

    def _seed(self, session_factory: sessionmaker[Session]) -> None:
        repo = _repo(session_factory)
        base_time = datetime.now(timezone.utc)
        repo.create(
            job_id="job-old",
            mode="estimate_params",
            job_dir=Path("/jobs/job-old"),
            output_dir=Path("/jobs/job-old/outputs"),
            created_at=base_time - timedelta(minutes=5),
        )
        repo.create(
            job_id="job-new",
            mode="forward_by_cartesian_grid",
            job_dir=Path("/jobs/job-new"),
            output_dir=Path("/jobs/job-new/outputs"),
            created_at=base_time,
        )

    def test_orders_newest_first(
        self, session_factory: sessionmaker[Session]
    ) -> None:
        self._seed(session_factory)
        repo = _repo(session_factory)

        records = repo.list()

        assert [r.id for r in records] == ["job-new", "job-old"]

    def test_filters_by_mode(
        self, session_factory: sessionmaker[Session]
    ) -> None:
        self._seed(session_factory)
        repo = _repo(session_factory)

        records = repo.list(mode="estimate_params")

        assert [r.id for r in records] == ["job-old"]

    def test_filters_by_status(
        self, session_factory: sessionmaker[Session]
    ) -> None:
        self._seed(session_factory)
        repo = _repo(session_factory)
        repo.mark_running(
            "job-new", started_at=datetime.now(timezone.utc), pid=123
        )

        records = repo.list(status="running")

        assert [r.id for r in records] == ["job-new"]

    def test_limit_and_offset(
        self, session_factory: sessionmaker[Session]
    ) -> None:
        self._seed(session_factory)
        repo = _repo(session_factory)

        records = repo.list(limit=1, offset=1)

        assert [r.id for r in records] == ["job-old"]


class TestMarkRunningAndFinished:
    """状態遷移。"""

    def test_mark_running_sets_status_started_at_pid(
        self, session_factory: sessionmaker[Session]
    ) -> None:
        repo = _repo(session_factory)
        repo.create(
            job_id="job-1",
            mode="estimate_params",
            job_dir=Path("/jobs/job-1"),
            output_dir=Path("/jobs/job-1/outputs"),
            created_at=datetime.now(timezone.utc),
        )
        started_at = datetime.now(timezone.utc)

        repo.mark_running(job_id="job-1", started_at=started_at, pid=4242)

        record = repo.get("job-1")
        assert record is not None
        assert record.status == "running"
        assert record.pid == 4242

    def test_mark_finished_sets_terminal_fields(
        self, session_factory: sessionmaker[Session]
    ) -> None:
        repo = _repo(session_factory)
        repo.create(
            job_id="job-1",
            mode="estimate_params",
            job_dir=Path("/jobs/job-1"),
            output_dir=Path("/jobs/job-1/outputs"),
            created_at=datetime.now(timezone.utc),
        )
        finished_at = datetime.now(timezone.utc)

        repo.mark_finished(
            job_id="job-1",
            status="failed",
            finished_at=finished_at,
            exit_code=2,
            error_kind="validation",
            error_message="bad input",
        )

        record = repo.get("job-1")
        assert record is not None
        assert record.status == "failed"
        assert record.exit_code == 2
        assert record.error_kind == "validation"
        assert record.error_message == "bad input"

    def test_mark_running_on_missing_job_raises(
        self, session_factory: sessionmaker[Session]
    ) -> None:
        repo = _repo(session_factory)

        with pytest.raises(ValueError, match="job が見つかりません"):
            repo.mark_running(
                job_id="does-not-exist",
                started_at=datetime.now(timezone.utc),
                pid=None,
            )


class TestListUnfinished:
    """孤児ジョブ回収用の一覧。"""

    def _create(self, repo: IJobRepository, job_id: str) -> None:
        repo.create(
            job_id=job_id,
            mode="estimate_params",
            job_dir=Path(f"/jobs/{job_id}"),
            output_dir=Path(f"/jobs/{job_id}/outputs"),
            created_at=datetime.now(timezone.utc),
        )

    def test_returns_queued_and_running_jobs(
        self, session_factory: sessionmaker[Session]
    ) -> None:
        """``queued`` も対象。キュー待ちのまま落ちた行を回収できないと消せなくなる。"""
        repo = _repo(session_factory)
        self._create(repo, "job-queued")
        self._create(repo, "job-running")
        repo.mark_running(
            "job-running", started_at=datetime.now(timezone.utc), pid=1
        )

        unfinished = repo.list_unfinished()

        assert sorted(r.id for r in unfinished) == [
            "job-queued",
            "job-running",
        ]

    def test_excludes_terminal_jobs(
        self, session_factory: sessionmaker[Session]
    ) -> None:
        repo = _repo(session_factory)
        for job_id, terminal_status in (
            ("job-succeeded", "succeeded"),
            ("job-failed", "failed"),
            ("job-cancelled", "cancelled"),
        ):
            self._create(repo, job_id)
            repo.mark_finished(
                job_id,
                status=terminal_status,
                finished_at=datetime.now(timezone.utc),
                exit_code=0,
                error_kind=None,
                error_message=None,
            )

        assert repo.list_unfinished() == []


class TestDelete:
    """台帳行の削除。"""

    def test_delete_removes_row(
        self, session_factory: sessionmaker[Session]
    ) -> None:
        repo = _repo(session_factory)
        repo.create(
            job_id="job-1",
            mode="estimate_params",
            job_dir=Path("/jobs/job-1"),
            output_dir=Path("/jobs/job-1/outputs"),
            created_at=datetime.now(timezone.utc),
        )

        repo.delete("job-1")

        assert repo.get("job-1") is None
        assert repo.list() == []

    def test_delete_missing_id_is_noop(
        self, session_factory: sessionmaker[Session]
    ) -> None:
        repo = _repo(session_factory)

        repo.delete("does-not-exist")
