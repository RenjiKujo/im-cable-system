"""ForwardExecutionOrchestratorFactory のテスト（二重かご向けラベル）。

ファクトリー本体はかご重数に依存しないが、単カゴ用モジュールと対になるよう
クラス名に DoubleCage を付与する。
4_test_strategy.md の「ファクトリーのテスト」-「forward 用ファクトリー」に準拠。
``input_double_im_cable_system_data`` のシステム名（broadcast_...）で入力を特定する。
"""

from __future__ import annotations

from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.forward.direct_forward_execution_orchestrator import (  # noqa: E501
    DirectForwardExecutionOrchestrator,
)
from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.forward.factory_forward_execution_orchestrator import (  # noqa: E501
    ForwardExecutionOrchestratorFactory,
)
from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.forward.iteration_forward_execution_orchestrator import (  # noqa: E501
    IterationForwardExecutionOrchestrator,
)
from im_cable_system.engine.shared.dto.input import (
    InputDto,
    InputDtos,
)


def _input_by_exact_system_name(
    dtos: InputDtos,
    name_value: str,
) -> InputDto:
    """``name.get_value()`` が ``name_value`` と一致する入力を返す。"""
    for dto in dtos.get_all():
        if dto.name.get_value() == name_value:
            return dto
    msg = f"InputDto not found: {name_value!r}"
    raise AssertionError(msg)


class TestDoubleCageForwardExecutionOrchestratorFactory:
    """二重かご向けラベルの forward-by-cartesian-grid ファクトリーテストクラス。"""

    def test_create_returns_direct_orchestrator_when_no_current_dependent(
        self,
        config,
        logger,
        double_cage_input_im_cable_system_dtos: InputDtos,
    ) -> None:
        """電流依存が無い DOUBLE_BASIC で Direct 実装が返ることを確認。"""
        input_dto = _input_by_exact_system_name(
            double_cage_input_im_cable_system_dtos,
            "broadcast_DOUBLE_BASIC_no_cable",
        )
        orchestrator = ForwardExecutionOrchestratorFactory.create(
            config=config,
            logger=logger,
            im_dto=input_dto.im,
            cable=input_dto.cable,
        )
        assert isinstance(
            orchestrator,
            DirectForwardExecutionOrchestrator,
        )

    def test_create_returns_iteration_orchestrator_when_secondary_current_dependent(
        self,
        config,
        logger,
        double_cage_input_im_cable_system_dtos: InputDtos,
    ) -> None:
        """二次に電流依存を含む DOUBLE_CURRENT_DEP で Iteration が返ることを確認。"""
        input_dto = _input_by_exact_system_name(
            double_cage_input_im_cable_system_dtos,
            "broadcast_DOUBLE_CURRENT_DEP_no_cable",
        )
        orchestrator = ForwardExecutionOrchestratorFactory.create(
            config=config,
            logger=logger,
            im_dto=input_dto.im,
            cable=input_dto.cable,
        )
        assert isinstance(
            orchestrator,
            IterationForwardExecutionOrchestrator,
        )

    def test_create_returns_iteration_orchestrator_when_primary_current_dependent(
        self,
        config,
        logger,
        double_cage_input_im_cable_system_dtos: InputDtos,
    ) -> None:
        """一次に電流依存を含む DOUBLE_CURRENT_DEP で Iteration が返ることを確認。"""
        input_dto = _input_by_exact_system_name(
            double_cage_input_im_cable_system_dtos,
            "broadcast_DOUBLE_CURRENT_DEP_no_cable",
        )
        orchestrator = ForwardExecutionOrchestratorFactory.create(
            config=config,
            logger=logger,
            im_dto=input_dto.im,
            cable=input_dto.cable,
        )
        assert isinstance(
            orchestrator,
            IterationForwardExecutionOrchestrator,
        )

    def test_create_returns_iteration_orchestrator_when_excitation_current_dependent(
        self,
        config,
        logger,
        double_cage_input_im_cable_system_dtos: InputDtos,
    ) -> None:
        """励磁に電流依存を含む DOUBLE_CURRENT_DEP で Iteration が返ることを確認。"""
        input_dto = _input_by_exact_system_name(
            double_cage_input_im_cable_system_dtos,
            "broadcast_DOUBLE_CURRENT_DEP_no_cable",
        )
        orchestrator = ForwardExecutionOrchestratorFactory.create(
            config=config,
            logger=logger,
            im_dto=input_dto.im,
            cable=input_dto.cable,
        )
        assert isinstance(
            orchestrator,
            IterationForwardExecutionOrchestrator,
        )

    def test_create_returns_iteration_orchestrator_when_cable_current_dependent(
        self,
        config,
        logger,
        double_cage_input_im_cable_system_dtos: InputDtos,
    ) -> None:
        """二重かご BASIC + 電流依存ケーブルで Iteration が返ることを確認。"""
        input_dto = _input_by_exact_system_name(
            double_cage_input_im_cable_system_dtos,
            "broadcast_DOUBLE_BASIC_DOUBLE_MAIN_CURRENT_DEP",
        )
        orchestrator = ForwardExecutionOrchestratorFactory.create(
            config=config,
            logger=logger,
            im_dto=input_dto.im,
            cable=input_dto.cable,
        )
        assert isinstance(
            orchestrator,
            IterationForwardExecutionOrchestrator,
        )
