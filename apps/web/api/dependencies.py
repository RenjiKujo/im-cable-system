"""FastAPI の依存性注入群（``Depends``）。

設定・リポジトリ・supervisor はどれも ``app.state`` に載っているが（``main.py``
参照）、ルート側で ``request.app.state.xxx`` を毎回直読みすると依存が暗黙になる。
ここで ``Depends`` 経由に揃えることで、ルートの引数リストを見るだけで
「何に依存しているか」が分かるようにする。

``get_job_repository`` が ``yield`` を使うのは、リクエスト 1 回分のセッションを
「使い終わったら閉じる」ため。``with`` ブロックを
``yield`` の前後に跨がせることで、エンドポイント処理が終わった後（レスポンス
生成後）にセッションが閉じる。
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status

from apps.web.api.supervisor import JobSupervisor
from apps.web.runner_gateway import RunnerGatewaySettings
from apps.web.store import IJobRepository, JobRecord, create_job_repository


def get_settings(request: Request) -> RunnerGatewaySettings:
    """``app.state.settings`` を返す。

    ``request.app.state`` 越しなのは、``create_app`` がテストごとに別の
    ``RunnerGatewaySettings`` を注入できるようにするため（モジュール変数に
    しない理由は ``main.py`` の docstring を参照）。
    """
    return request.app.state.settings


def get_job_repository(request: Request) -> Iterator[IJobRepository]:
    """1 リクエスト分の台帳リポジトリを貸す（レスポンス生成後にセッションを閉じる）。"""
    with request.app.state.session_factory() as session:
        yield create_job_repository(session)


def get_supervisor(request: Request) -> JobSupervisor:
    """``app.state.supervisor`` を返す。"""
    return request.app.state.supervisor


def get_job_record(job_id: str, repo: JobRepository) -> JobRecord:
    """パスの ``job_id`` で 1 件引く。無ければ 404（各ルートの重複を無くす）。"""
    record = repo.get(job_id)
    if record is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="job not found")
    return record


Settings = Annotated[RunnerGatewaySettings, Depends(get_settings)]
JobRepository = Annotated[IJobRepository, Depends(get_job_repository)]
Supervisor = Annotated[JobSupervisor, Depends(get_supervisor)]
ExistingJob = Annotated[JobRecord, Depends(get_job_record)]
