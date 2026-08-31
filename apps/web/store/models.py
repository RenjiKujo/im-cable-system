"""ジョブ台帳のテーブル定義（SQLAlchemy 2.0 ORM）。テーブルは 1 枚のみ。

配列・PNG・巨大 CSV は入れない（DB は台帳のみ。成果物は ``outputs/`` を
毎回走査する。詳細は ``apps/web/runner_gateway/artifacts.py``）。

``DeclarativeBase`` の継承は、実装継承の禁止
（docs/conventions/2_design_principles.md）に対する境界での例外
（docs/apps/web/0_overview.md 参照）。層外は本モジュールを直接触らず、
``repository.py`` の ``JobRecord``（DTO）越しにのみ台帳を参照する。
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """SQLAlchemy 宣言的ベース（本パッケージ専用）。"""


class Job(Base):
    """1 ジョブの実行台帳。列の意味は docs/apps/web/0_overview.md の表を正とする。"""

    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    mode: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    job_dir: Mapped[str] = mapped_column(Text, nullable=False)
    output_dir: Mapped[str] = mapped_column(Text, nullable=False)
    exit_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_kind: Mapped[str | None] = mapped_column(String, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    pid: Mapped[int | None] = mapped_column(Integer, nullable=True)
