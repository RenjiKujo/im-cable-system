"""engine / sessionmaker / create_all。SQLite + SQLAlchemy 2.0 ORM。

スキーマ作成は ``Base.metadata.create_all`` だけで行い、マイグレーションの仕組みは
持たない（``jobs_root`` ごと捨てて作り直せるローカル実行前提。
docs/apps/web/0_overview.md の「store — ジョブ台帳」）。
"""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from apps.web.store.models import Base


def create_sqlite_engine(db_path: Path) -> Engine:
    """``db_path`` に対する SQLite engine を作る（親ディレクトリを作成する）。"""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return create_engine(f"sqlite:///{db_path}", future=True)


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    """``Session`` のファクトリーを作る。"""
    return sessionmaker(bind=engine, expire_on_commit=False, future=True)


def init_db(engine: Engine) -> None:
    """テーブルが無ければ作成する（``jobs`` テーブル 1 枚）。"""
    Base.metadata.create_all(engine)
