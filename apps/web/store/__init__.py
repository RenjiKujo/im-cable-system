"""ジョブ台帳だけを持つ永続化層（SQLAlchemy 2.0 ORM）。

``apps/web/api`` から見た公開窓口。ORM モデル（``Job`` / ``Base``）は
層外非公開とし、``JobRecord``（DTO）と ``IJobRepository`` 越しにのみ台帳へ触る。
生成は ``create_job_repository`` に集約し、具象クラスは公開しない。
"""

from apps.web.store.repository import (
    IJobRepository,
    JobRecord,
    create_job_repository,
)
from apps.web.store.session import (
    create_session_factory,
    create_sqlite_engine,
    init_db,
)

__all__ = [
    "IJobRepository",
    "JobRecord",
    "create_job_repository",
    "create_session_factory",
    "create_sqlite_engine",
    "init_db",
]
