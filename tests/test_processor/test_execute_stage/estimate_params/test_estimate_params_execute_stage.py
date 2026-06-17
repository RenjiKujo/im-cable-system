"""EstimateParamsExecuteStage の単体テスト。

ステージ固有の責務（InputDtos→分割→execute 写像→ItmDtos 化、戦略への委譲）
を fake で隔離して検証する。フィット計算は algorithm 層
（``tests/test_algorithm``）と all stage 結合テストでカバーする。
"""

from __future__ import annotations

from typing import Any, cast

from im_cable_system.engine.processor.execute_stage import (
    EstimateParamsExecuteStage,
)
from im_cable_system.engine.processor.i_stage import IStage
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.itm import ItmDtos


class TestEstimateParamsExecuteStageCreate:
    """``create`` の契約テスト。"""

    def test_create_returns_estimate_params_execute_stage_as_istage(
        self,
        config: IConfig,
        logger: ILogger,
    ) -> None:
        """create は IStage 実装（EstimateParamsExecuteStage）を返す。"""
        stage = EstimateParamsExecuteStage.create(
            config=config,
            logger=logger,
        )
        assert isinstance(stage, EstimateParamsExecuteStage)
        assert isinstance(stage, IStage)


class TestEstimateParamsExecuteStageProcess:
    """``process`` の契約テスト（fake 隔離）。"""

    def _build_stage(
        self,
        dump_disabled_config: IConfig,
        noop_logger: ILogger,
        fake_orchestrator: Any,
        recording_strategy: Any,
    ) -> EstimateParamsExecuteStage:
        """fake を注入した EstimateParamsExecuteStage を組み立てる。"""
        return EstimateParamsExecuteStage(
            config=dump_disabled_config,
            logger=noop_logger,
            orchestrator=fake_orchestrator,  # type: ignore[arg-type]
            strategy=recording_strategy,  # type: ignore[arg-type]
        )

    def test_process_returns_itm_dtos_with_one_result_per_input(
        self,
        dump_disabled_config: IConfig,
        noop_logger: ILogger,
        fake_orchestrator: Any,
        recording_strategy: Any,
    ) -> None:
        """1 入力につき 1 結果、入力順序を保持して ItmDtos を返す。"""
        stage = self._build_stage(
            dump_disabled_config,
            noop_logger,
            fake_orchestrator,
            recording_strategy,
        )
        inputs = _StubInputs(["p", "q", "r"])

        result = stage.process(inputs)  # type: ignore[arg-type]

        assert isinstance(result, ItmDtos)
        result_items = cast(list[Any], result.get_all())
        sources = [item.source for item in result_items]
        assert sources == ["p", "q", "r"]

    def test_process_delegates_execute_to_strategy(
        self,
        dump_disabled_config: IConfig,
        noop_logger: ILogger,
        fake_orchestrator: Any,
        recording_strategy: Any,
    ) -> None:
        """戦略へ items=get_all()、process_func=orchestrator.execute を渡す。"""
        stage = self._build_stage(
            dump_disabled_config,
            noop_logger,
            fake_orchestrator,
            recording_strategy,
        )

        stage.process(_StubInputs(["m"]))  # type: ignore[arg-type]

        assert recording_strategy.received_items == ["m"]
        assert recording_strategy.received_func == fake_orchestrator.execute
        assert fake_orchestrator.executed == ["m"]

    def test_process_returns_empty_for_empty_inputs(
        self,
        dump_disabled_config: IConfig,
        noop_logger: ILogger,
        fake_orchestrator: Any,
        recording_strategy: Any,
    ) -> None:
        """空入力では空 ItmDtos を返す。"""
        stage = self._build_stage(
            dump_disabled_config,
            noop_logger,
            fake_orchestrator,
            recording_strategy,
        )

        result = stage.process(_StubInputs([]))  # type: ignore[arg-type]

        assert isinstance(result, ItmDtos)
        assert result.get_all() == []


class _StubInputs:
    """``get_all`` のみを提供する InputDtos 代用（順序検証用）。"""

    def __init__(self, items: list[object]) -> None:
        self._items = list(items)

    def get_all(self) -> list[object]:
        return list(self._items)
