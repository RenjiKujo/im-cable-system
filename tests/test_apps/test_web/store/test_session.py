"""session: engine 生成・親ディレクトリ作成・create_all によるテーブル作成。"""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import inspect

from apps.web.store import create_session_factory, create_sqlite_engine, init_db


class TestCreateSqliteEngine:
    """SQLite engine の生成。"""

    def test_creates_parent_directory(self, tmp_path: Path) -> None:
        db_path = tmp_path / "nested" / "jobs.sqlite3"

        create_sqlite_engine(db_path)

        assert db_path.parent.is_dir()


class TestInitDb:
    """テーブル作成。"""

    def test_creates_jobs_table(self, tmp_path: Path) -> None:
        engine = create_sqlite_engine(tmp_path / "jobs.sqlite3")

        init_db(engine)

        assert inspect(engine).has_table("jobs")

    def test_is_idempotent(self, tmp_path: Path) -> None:
        engine = create_sqlite_engine(tmp_path / "jobs.sqlite3")

        init_db(engine)
        init_db(engine)  # 2 回目も例外にならない

        assert inspect(engine).has_table("jobs")


class TestCreateSessionFactory:
    """Session ファクトリーの生成。"""

    def test_produces_usable_sessions(self, tmp_path: Path) -> None:
        engine = create_sqlite_engine(tmp_path / "jobs.sqlite3")
        init_db(engine)
        session_factory = create_session_factory(engine)

        with session_factory() as session:
            assert session.is_active
