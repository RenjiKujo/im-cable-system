"""ForwardExecuteStage の単体テスト。

ステージ固有の責務（InputDtos→分割→execute 写像→ItmDtos 化、戦略への委譲）
を fake で隔離して検証する。各 InputDto に対する Direct/Iteration の選択は
:class:`ForwardExecutionOrchestratorFactory` の責務であり、本テストでは
ファクトリーを fake に差し替えて隔離する。選択ロジックや数値計算は
algorithm 層（``tests/test_algorithm``）と all stage 結合テストでカバーする。
"""

from __future__ import annotations

from typing import Any, cast

import pytest

from im_cable_system.engine.processor.execute_stage import (
    ForwardExecuteStage,
    forward_execute_stage,
)
from im_cable_system.engine.processor.i_stage import IStage
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.itm import ItmDtos


class TestForwardExecuteStageCreate:
    """``create`` の契約テスト。"""

    def test_create_returns_forward_execute_stage_as_istage(
        self,
        config: IConfig,
        logger: ILogger,
    ) -> None:
        """create は IStage 実装（ForwardExecuteStage）を返す。"""
        stage = ForwardExecuteStage.create(config=config, logger=logger)
        assert isinstance(stage, ForwardExecuteStage)
        assert isinstance(stage, IStage)


class TestForwardExecuteStageProcess:
    """``process`` の契約テスト（fake 隔離）。"""

    def _build_stage(
        self,
        dump_disabled_config: IConfig,
        noop_logger: ILogger,
        recording_strategy: Any,
    ) -> ForwardExecuteStage:
        """fake 戦略を注入した ForwardExecuteStage を組み立てる。"""
        return ForwardExecuteStage(
            config=dump_disabled_config,
            logger=noop_logger,
            strategy=recording_strategy,  # type: ignore[arg-type]
        )

    def _patch_factory(
        self,
        monkeypatch: pytest.MonkeyPatch,
        fake_orchestrator: Any,
    ) -> None:
        """ファクトリーが常に fake オーケストレーターを返すよう差し替える。"""

        def _fake_create(**kwargs: object) -> object:
            _ = kwargs
            return fake_orchestrator

        monkeypatch.setattr(
            forward_execute_stage.ForwardExecutionOrchestratorFactory,
            "create",
            _fake_create,
        )

    def test_process_returns_itm_dtos_with_one_result_per_input(
        self,
        monkeypatch: pytest.MonkeyPatch,
        dump_disabled_config: IConfig,
        noop_logger: ILogger,
        fake_orchestrator: Any,
        recording_strategy: Any,
    ) -> None:
        """1 入力につき 1 結果、入力順序を保持して ItmDtos を返す。"""
        self._patch_factory(monkeypatch, fake_orchestrator)
        stage = self._build_stage(
            dump_disabled_config,
            noop_logger,
            recording_strategy,
        )
        inputs = _StubInputs([_StubInput("a"), _StubInput("b")])

        result = stage.process(inputs)  # type: ignore[arg-type]

        assert isinstance(result, ItmDtos)
        result_items = cast(list[Any], result.get_all())
        sources = [item.source.label for item in result_items]
        assert sources == ["a", "b"]

    def test_process_delegates_execute_to_strategy(
        self,
        monkeypatch: pytest.MonkeyPatch,
        dump_disabled_config: IConfig,
        noop_logger: ILogger,
        fake_orchestrator: Any,
        recording_strategy: Any,
    ) -> None:
        """戦略へ items=get_all()、process_func=stage._execute_one を渡す。"""
        self._patch_factory(monkeypatch, fake_orchestrator)
        stage = self._build_stage(
            dump_disabled_config,
            noop_logger,
            recording_strategy,
        )
        items: list[object] = [_StubInput("x"), _StubInput("y")]
        inputs = _StubInputs(items)

        stage.process(inputs)  # type: ignore[arg-type]

        assert recording_strategy.received_items == items
        assert recording_strategy.received_func == stage._execute_one
        assert fake_orchestrator.executed == items

    def test_process_returns_empty_for_empty_inputs(
        self,
        monkeypatch: pytest.MonkeyPatch,
        dump_disabled_config: IConfig,
        noop_logger: ILogger,
        fake_orchestrator: object,
        recording_strategy: object,
    ) -> None:
        """空入力では空 ItmDtos を返す。"""
        self._patch_factory(monkeypatch, fake_orchestrator)
        stage = self._build_stage(
            dump_disabled_config,
            noop_logger,
            recording_strategy,
        )

        result = stage.process(_StubInputs([]))  # type: ignore[arg-type]

        assert isinstance(result, ItmDtos)
        assert result.get_all() == []


class _StubInput:
    """``im`` / ``cable`` のみ持つ InputDto 代用（ファクトリー引数の検証用）。"""

    def __init__(self, label: str) -> None:
        self.label: str = label
        self.im: object = None
        self.cable: object = None


class _StubInputs:
    """``get_all`` のみを提供する InputDtos 代用（順序検証用）。"""

    def __init__(self, items: list[object]) -> None:
        self._items = list(items)

    def get_all(self) -> list[object]:
        return list(self._items)
