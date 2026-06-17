"""パラメータ推定オーケストレーター（実行実装）のテスト。"""

from __future__ import annotations

from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params import (
    EstimateParamsOrchestrator,
    IEstimateParamsExecutionOrchestrator,
)
from im_cable_system.engine.shared.config import IConfig, ILogger


class TestEstimateParamsOrchestrator:
    """EstimateParamsOrchestrator の生成テスト。"""

    def test_create_returns_interface(
        self,
        config: IConfig,
        logger: ILogger,
    ) -> None:
        """create がインターフェース型を返すことを確認する。"""
        orchestrator = EstimateParamsOrchestrator.create(
            config=config,
            logger=logger,
        )
        assert isinstance(
            orchestrator,
            IEstimateParamsExecutionOrchestrator,
        )
