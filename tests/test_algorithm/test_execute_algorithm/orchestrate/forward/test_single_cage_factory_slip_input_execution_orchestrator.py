"""ForwardExecutionOrchestratorFactory のテスト（単カゴ向けデータ前提）。

4_test_strategy.md の「ファクトリーのテスト」-「forward 用ファクトリー」に準拠。
Direct/Iteration の分岐を検証する。ファクトリーは ``im_dto`` / ``cable`` から
モデル種別を導出するため、:mod:`input_single_im_cable_system_data` の命名規則に
合わせた ``InputDto`` を参照する。
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


class TestSingleCageForwardExecutionOrchestratorFactory:
    """単カゴ向け ForwardExecutionOrchestratorFactory のテストクラス。"""

    def test_create_returns_direct_orchestrator_when_no_current_dependent(
        self,
        config,
        logger,
        single_cage_input_im_cable_system_dtos: InputDtos,
    ) -> None:
        """電流依存タイプが含まれないときに Direct 実装が返ることを確認。"""
        input_dto = _input_by_exact_system_name(
            single_cage_input_im_cable_system_dtos,
            "broadcast_TEST1_no_cable",
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
        single_cage_input_im_cable_system_dtos: InputDtos,
    ) -> None:
        """二次電流依存が含まれる Im（TEST3）で Iteration 実装が返ることを確認。"""
        input_dto = _input_by_exact_system_name(
            single_cage_input_im_cable_system_dtos,
            "broadcast_TEST3_no_cable",
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
        single_cage_input_im_cable_system_dtos: InputDtos,
    ) -> None:
        """一次のみ電流依存（TEST6）で Iteration 実装が返ることを確認。"""
        input_dto = _input_by_exact_system_name(
            single_cage_input_im_cable_system_dtos,
            "broadcast_TEST6_no_cable",
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
        single_cage_input_im_cable_system_dtos: InputDtos,
    ) -> None:
        """励磁が電流依存（TEST7）で Iteration 実装が返ることを確認。"""
        input_dto = _input_by_exact_system_name(
            single_cage_input_im_cable_system_dtos,
            "broadcast_TEST7_no_cable",
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
        single_cage_input_im_cable_system_dtos: InputDtos,
    ) -> None:
        """ケーブル導体が電流依存のとき Iteration 実装が返ることを確認。"""
        input_dto = _input_by_exact_system_name(
            single_cage_input_im_cable_system_dtos,
            "broadcast_TEST1_CURRENT_DEP_REAL",
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
