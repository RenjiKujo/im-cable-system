"""simulate テスト共通フィクスチャ。

``config`` / ``logger`` は上位 ``test_execute_algorithm/conftest.py`` の
plain なものを継承する。ここでは複数の simulate テストで共有する
``build_model_orchestrator`` を提供する。
"""

from __future__ import annotations

import pytest

from im_cable_system.engine.algorithm.execute_algorithm.build_model import (
    IImCableModelBuildOrchestrator,
)
from im_cable_system.engine.algorithm.execute_algorithm.build_model.orchestrate import (  # noqa: E501
    ImCableModelBuildOrchestrator,
)
from im_cable_system.engine.shared.config import IConfig, ILogger


@pytest.fixture
def build_model_orchestrator(
    config: IConfig,
    logger: ILogger,
) -> IImCableModelBuildOrchestrator:
    """テスト用の ImCableModelBuildOrchestrator フィクスチャ。"""
    return ImCableModelBuildOrchestrator.create(config=config, logger=logger)
