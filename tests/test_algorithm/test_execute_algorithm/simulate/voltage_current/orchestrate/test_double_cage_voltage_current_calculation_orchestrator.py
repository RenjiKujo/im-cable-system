"""電流電圧計算オーケストレーターのテスト（二重かご / Double cage）。

このモジュールは、`input_double_im_cable_system_data` が生成する二重かご向け入力DTOを用いて
`VoltageCurrentCalculationOrchestrator` の最小限の動作を検証します。
"""

from __future__ import annotations

import numpy as np
import pytest

from im_cable_system.engine.algorithm.execute_algorithm.build_model.orchestrate import (  # noqa: E501
    ImCableModelBuildOrchestrator,
)
from im_cable_system.engine.algorithm.execute_algorithm.simulate.voltage_current import (  # noqa: E501
    IVoltageCurrentCalculationOrchestrator,
    VoltageCurrentCalculationOrchestrator,
)
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ImSecondaryCageBranchType,
)
from tests.test_algorithm.test_execute_algorithm.fixtures.input_double_im_cable_system_data import (  # noqa: E501
    make_double_cage_im_series_dtos,
    make_input_im_cable_system_dtos,
)

_INNER = ImSecondaryCageBranchType.INNER
_OUTER = ImSecondaryCageBranchType.OUTER


@pytest.fixture
def double_cage_im_series_dtos():
    """テスト用の二重かご ImSeriesDtos fixture."""
    return make_double_cage_im_series_dtos()


@pytest.fixture
def double_cage_input_im_cable_system_dtos():
    """テスト用の二重かご InputDtos fixture."""
    return make_input_im_cable_system_dtos().get_all()


def _build_model_dto(
    *,
    input_dto,
    build_model_orchestrator: ImCableModelBuildOrchestrator,
):
    """入力DTOからモデルDTOを構築するヘルパー関数。"""
    return build_model_orchestrator.build(input_dto)


class TestDoubleCageVoltageCurrentCalculationOrchestrator:
    """二重かご（Double cage）向け VoltageCurrentCalculationOrchestrator のテスト。"""

    def test_create_orchestrator(self, config, logger) -> None:
        """オーケストレーターの生成を確認する。"""
        orchestrator = VoltageCurrentCalculationOrchestrator.create(
            config=config, logger=logger
        )
        assert orchestrator is not None
        assert isinstance(orchestrator, IVoltageCurrentCalculationOrchestrator)

    def test_calculate_creates_correct_voltage_current_dto(
        self,
        config,
        logger,
        double_cage_im_series_dtos,  # noqa: ARG002
        double_cage_input_im_cable_system_dtos,
        build_model_orchestrator,
    ) -> None:
        """二重かごの入力DTOで電圧・電流DTOが生成されることを確認する。"""
        orchestrator = VoltageCurrentCalculationOrchestrator.create(
            config=config, logger=logger
        )

        for input_dto in double_cage_input_im_cable_system_dtos[:3]:
            model_dto = _build_model_dto(
                input_dto=input_dto,
                build_model_orchestrator=build_model_orchestrator,
            )
            result = orchestrator.calculate(model_dto=model_dto)

            assert result is not None
            assert result.im_voltage_current is not None
            assert result.cable_voltage_current is not None

            expected_shape = model_dto.array_layout.shape
            assert (
                result.cable_voltage_current.input_phase_voltage.value.shape
                == expected_shape
            )
            assert (
                result.im_voltage_current.im_input_voltage.value.shape
                == expected_shape
            )

    def test_t_circuit_kcl_holds_for_double_cage(
        self,
        config,
        logger,
        double_cage_im_series_dtos,  # noqa: ARG002
        double_cage_input_im_cable_system_dtos,
        build_model_orchestrator,
    ) -> None:
        """二重かご（T型）で KCL が成り立つことを検証する。"""
        orchestrator = VoltageCurrentCalculationOrchestrator.create(
            config=config, logger=logger
        )

        target_input_dto = None
        for input_dto in double_cage_input_im_cable_system_dtos:
            if input_dto.im.im_series.name.get_value() == "DOUBLE_SLIP_DEP":
                target_input_dto = input_dto
                break

        if target_input_dto is None:
            pytest.skip("二重かご（T型）の入力DTOが見つかりませんでした。")

        model_dto = _build_model_dto(
            input_dto=target_input_dto,
            build_model_orchestrator=build_model_orchestrator,
        )
        result = orchestrator.calculate(model_dto=model_dto)

        assert result.im_voltage_current is not None

        im_input_current = result.im_voltage_current.im_input_current.value
        primary_current = result.im_voltage_current.im_primary_current.value
        excitation_current = (
            result.im_voltage_current.im_excitation_current.value
        )
        secondary_total_current = (
            result.im_voltage_current.get_secondary_total_current().value
        )

        # T型回路: 入力電流=一次電流、一次電流=励磁電流+二次合計電流
        np.testing.assert_allclose(
            im_input_current,
            primary_current,
            rtol=1e-10,
            atol=1e-12,
        )
        np.testing.assert_allclose(
            primary_current,
            excitation_current + secondary_total_current,
            rtol=1e-10,
            atol=1e-12,
        )

    def test_l_circuit_kcl_holds_for_double_cage(
        self,
        config,
        logger,
        double_cage_im_series_dtos,  # noqa: ARG002
        double_cage_input_im_cable_system_dtos,
        build_model_orchestrator,
    ) -> None:
        """二重かご（L型）で KCL が成り立つことを検証する。"""
        orchestrator = VoltageCurrentCalculationOrchestrator.create(
            config=config, logger=logger
        )

        target_input_dto = None
        for input_dto in double_cage_input_im_cable_system_dtos:
            if input_dto.im.im_series.name.get_value() == "DOUBLE_BASIC":
                target_input_dto = input_dto
                break

        if target_input_dto is None:
            pytest.skip("二重かご（L型）の入力DTOが見つかりませんでした。")

        model_dto = _build_model_dto(
            input_dto=target_input_dto,
            build_model_orchestrator=build_model_orchestrator,
        )
        result = orchestrator.calculate(model_dto=model_dto)

        # L型回路: 入力電流 = 励磁電流 + 直列枝電流（= 二次合計電流）
        im_input_current = result.im_voltage_current.im_input_current.value
        excitation_current = (
            result.im_voltage_current.im_excitation_current.value
        )
        series_current = result.im_voltage_current.im_primary_current.value
        secondary_total_current = (
            result.im_voltage_current.get_secondary_total_current().value
        )

        np.testing.assert_allclose(
            im_input_current,
            excitation_current + series_current,
            rtol=1e-10,
            atol=1e-12,
        )
        # L型では一次（直列）電流＝二次合計電流（同一直列枝）。
        # build_model により電流が極小となる退化ケースもあるため、
        # 相対比較が破綻しないよう絶対許容を電流の代表スケールで与える。
        current_scale = float(np.max(np.abs(im_input_current))) + 1.0
        np.testing.assert_allclose(
            series_current,
            secondary_total_current,
            rtol=1e-9,
            atol=current_scale * 1e-9,
        )

    def test_branch_currents_sum_to_secondary_total(
        self,
        config,
        logger,
        double_cage_im_series_dtos,  # noqa: ARG002
        double_cage_input_im_cable_system_dtos,
        build_model_orchestrator,
    ) -> None:
        """INNER+OUTER の枝電流が二次合計電流に一致することを検証する。"""
        orchestrator = VoltageCurrentCalculationOrchestrator.create(
            config=config, logger=logger
        )

        for input_dto in double_cage_input_im_cable_system_dtos[:3]:
            model_dto = _build_model_dto(
                input_dto=input_dto,
                build_model_orchestrator=build_model_orchestrator,
            )
            result = orchestrator.calculate(model_dto=model_dto)
            im_vc = result.im_voltage_current

            inner_current = im_vc.secondary_branch_current[_INNER].value
            outer_current = im_vc.secondary_branch_current[_OUTER].value
            total_current = im_vc.get_secondary_total_current().value

            np.testing.assert_allclose(
                total_current,
                inner_current + outer_current,
                rtol=1e-10,
                atol=1e-12,
            )

    def test_t_circuit_secondary_current_matches_ohms_law(
        self,
        config,
        logger,
        double_cage_im_series_dtos,  # noqa: ARG002
        double_cage_input_im_cable_system_dtos,
        build_model_orchestrator,
    ) -> None:
        """二重かご T型の二次合計電流が KCL とオーム則で一致することを検証する。

        計算器は二次合計電流を KCL（I2 = I1 - I_m）で求める。ロジックが
        正しければ、独立した導出であるオーム則
        （I2 = V_m * (Y_inner + Y_outer)）とも一致するはずなので、両者の
        一致をクロスチェックする。
        """
        orchestrator = VoltageCurrentCalculationOrchestrator.create(
            config=config, logger=logger
        )

        target_input_dto = None
        for input_dto in double_cage_input_im_cable_system_dtos:
            if input_dto.im.im_series.name.get_value() == "DOUBLE_SLIP_DEP":
                target_input_dto = input_dto
                break

        if target_input_dto is None:
            pytest.skip("二重かご（T型）の入力DTOが見つかりませんでした。")

        model_dto = _build_model_dto(
            input_dto=target_input_dto,
            build_model_orchestrator=build_model_orchestrator,
        )
        result = orchestrator.calculate(model_dto=model_dto)
        im_vc = result.im_voltage_current

        # KCL 導出（I2 は I1 から I_m を引いた値）
        secondary_total_kcl = im_vc.get_secondary_total_current().value
        # オーム則導出（I2 は V_m と (Y_inner + Y_outer) の積）
        excitation_voltage = im_vc.im_excitation_voltage.to_base_unit().value
        sec = model_dto.im.secondary_model
        y_inner = sec.admittances[_INNER].to_base_unit().value
        y_outer = sec.admittances[_OUTER].to_base_unit().value
        secondary_total_ohms = excitation_voltage * (y_inner + y_outer)

        current_scale = float(np.max(np.abs(secondary_total_kcl))) + 1.0
        np.testing.assert_allclose(
            secondary_total_kcl,
            secondary_total_ohms,
            rtol=1e-9,
            atol=current_scale * 1e-9,
        )
