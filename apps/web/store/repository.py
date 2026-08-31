"""ジョブ台帳の CRUD。API はここ越しにしか DB を触らない。

``jobs.status`` / ``jobs.error_kind`` の語彙は
``apps/web/runner_gateway/executor.py`` の ``JobStatus`` / ``ErrorKind`` と
一致させる（依存の一方向性を保つため、本パッケージは runner_gateway を
import しない。値は呼び出し側の api 層が揃える）。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.web.store.models import Job

_DEFAULT_STATUS_ON_CREATE = "queued"
_UNFINISHED_STATUSES = ("queued", "running")


@dataclass(frozen=True)
class JobRecord:
    """ジョブ台帳 1 行のスナップショット（DTO）。ORM モデルを層外へ漏らさない。"""

    id: str
    mode: str
    status: str
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    job_dir: Path
    output_dir: Path
    exit_code: int | None
    error_kind: str | None
    error_message: str | None
    pid: int | None


def _as_utc(value: datetime) -> datetime:
    """SQLite は tzinfo を保持しないため、naive 値を UTC とみなして付け直す。"""
    return (
        value
        if value.tzinfo is not None
        else value.replace(tzinfo=timezone.utc)
    )


def _to_record(job: Job) -> JobRecord:
    return JobRecord(
        id=job.id,
        mode=job.mode,
        status=job.status,
        created_at=_as_utc(job.created_at),
        started_at=(
            None if job.started_at is None else _as_utc(job.started_at)
        ),
        finished_at=(
            None if job.finished_at is None else _as_utc(job.finished_at)
        ),
        job_dir=Path(job.job_dir),
        output_dir=Path(job.output_dir),
        exit_code=job.exit_code,
        error_kind=job.error_kind,
        error_message=job.error_message,
        pid=job.pid,
    )


class IJobRepository(ABC):
    """ジョブ台帳 CRUD の契約。"""

    @abstractmethod
    def create(
        self,
        *,
        job_id: str,
        mode: str,
        job_dir: Path,
        output_dir: Path,
        created_at: datetime,
    ) -> JobRecord:
        """新規ジョブ行を作る（初期 status は ``queued``）。"""
        ...

    @abstractmethod
    def get(self, job_id: str) -> JobRecord | None:
        """1 件取得する。無ければ ``None``。"""
        ...

    @abstractmethod
    def list(
        self,
        *,
        mode: str | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[JobRecord]:
        """一覧する（新しい順）。``mode`` / ``status`` は完全一致フィルタ。"""
        ...

    @abstractmethod
    def list_unfinished(self) -> list[JobRecord]:
        """非終端（``queued`` / ``running``）の行を全件返す（孤児ジョブ回収用）。

        ``running`` だけでは足りない。投入直後・キュー待ちのままサーバが落ちると
        ``queued`` で残り、非終端なので ``DELETE`` も 409 で拒まれて消せなくなる。
        """
        ...

    @abstractmethod
    def mark_running(
        self, job_id: str, *, started_at: datetime, pid: int | None
    ) -> None:
        """``running`` へ遷移させ、開始時刻と pid を記録する。"""
        ...

    @abstractmethod
    def mark_finished(
        self,
        job_id: str,
        *,
        status: str,
        finished_at: datetime,
        exit_code: int | None,
        error_kind: str | None,
        error_message: str | None,
    ) -> None:
        """終端状態（``succeeded`` / ``failed`` / ``cancelled``）へ遷移させる。"""
        ...

    @abstractmethod
    def delete(self, job_id: str) -> None:
        """台帳から 1 行消す。無ければ何もしない。"""
        ...


class SqlAlchemyJobRepository(IJobRepository):
    """SQLAlchemy ``Session`` を使う実装。生成は ``create_job_repository`` 経由。"""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(
        self,
        *,
        job_id: str,
        mode: str,
        job_dir: Path,
        output_dir: Path,
        created_at: datetime,
    ) -> JobRecord:
        job = Job(
            id=job_id,
            mode=mode,
            status=_DEFAULT_STATUS_ON_CREATE,
            created_at=created_at,
            job_dir=str(job_dir),
            output_dir=str(output_dir),
        )
        self._session.add(job)
        self._session.commit()
        self._session.refresh(job)
        return _to_record(job)

    def get(self, job_id: str) -> JobRecord | None:
        job = self._session.get(Job, job_id)
        return _to_record(job) if job is not None else None

    def list(
        self,
        *,
        mode: str | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[JobRecord]:
        stmt = select(Job).order_by(Job.created_at.desc())
        if mode is not None:
            stmt = stmt.where(Job.mode == mode)
        if status is not None:
            stmt = stmt.where(Job.status == status)
        stmt = stmt.limit(limit).offset(offset)
        return [_to_record(job) for job in self._session.scalars(stmt)]

    def list_unfinished(self) -> list[JobRecord]:
        stmt = select(Job).where(Job.status.in_(_UNFINISHED_STATUSES))
        return [_to_record(job) for job in self._session.scalars(stmt)]

    def _get_or_raise(self, job_id: str) -> Job:
        job = self._session.get(Job, job_id)
        if job is None:
            raise ValueError(f"job が見つかりません: {job_id}")
        return job

    def mark_running(
        self, job_id: str, *, started_at: datetime, pid: int | None
    ) -> None:
        job = self._get_or_raise(job_id)
        job.status = "running"
        job.started_at = started_at
        job.pid = pid
        self._session.commit()

    def mark_finished(
        self,
        job_id: str,
        *,
        status: str,
        finished_at: datetime,
        exit_code: int | None,
        error_kind: str | None,
        error_message: str | None,
    ) -> None:
        job = self._get_or_raise(job_id)
        job.status = status
        job.finished_at = finished_at
        job.exit_code = exit_code
        job.error_kind = error_kind
        job.error_message = error_message
        self._session.commit()

    def delete(self, job_id: str) -> None:
        job = self._session.get(Job, job_id)
        if job is None:
            return
        self._session.delete(job)
        self._session.commit()


def create_job_repository(session: Session) -> IJobRepository:
    """台帳リポジトリのファクトリー。戻り値は必ず IF。

    具象名（``SqlAlchemyJobRepository``）を層外へ出さないための唯一の生成窓口
    （docs/conventions/2_design_principles.md の「生成はファクトリーへ集約」）。
    """
    return SqlAlchemyJobRepository(session)
