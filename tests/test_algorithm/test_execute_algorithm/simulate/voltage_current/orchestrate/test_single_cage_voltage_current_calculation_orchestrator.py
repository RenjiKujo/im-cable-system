"""電流電圧計算オーケストレーターのテスト。

このモジュールは、VoltageCurrentCalculationOrchestratorのテストを提供します。
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
    ImCircuitType,
    ImSecondaryCageBranchType,
    PieCableConductorKey,
    PieCableGroundKey,
)
from tests.test_algorithm.test_execute_algorithm.fixtures.input_single_im_cable_system_data import (  # noqa: E501
    make_cable_series_dtos,
    make_input_im_cable_system_dtos,
    make_single_cage_im_series_dtos,
)


@pytest.fixture
def im_series_dtos():
    """テスト用のImSeriesDtos fixture."""
    return make_single_cage_im_series_dtos()


@pytest.fixture
def cable_series_dtos():
    """テスト用のCableSeriesDtos fixture."""
    return make_cable_series_dtos()


@pytest.fixture
def input_im_cable_system_dtos():
    """テスト用のInputDtos fixture."""
    return make_input_im_cable_system_dtos().get_all()


def _build_model_dto(
    input_dto,
    im_series_dtos,  # noqa: ARG001
    cable_series_dtos,  # noqa: ARG001
    build_model_orchestrator: ImCableModelBuildOrchestrator,
):
    """入力DTOからモデルDTOを構築するヘルパー関数。"""
    return build_model_orchestrator.build(input_dto)


class TestSingleCageVoltageCurrentCalculationOrchestrator:
    """単一かご（Single cage）向け VoltageCurrentCalculationOrchestrator のテスト。"""

    def test_create_orchestrator(self, config, logger) -> None:
        """オーケストレーターの生成を確認する。"""
        orchestrator = VoltageCurrentCalculationOrchestrator.create(
            config=config, logger=logger
        )
        assert orchestrator is not None
        assert isinstance(orchestrator, IVoltageCurrentCalculationOrchestrator)

    def test_calculate_with_ideal_cable(
        self,
        config,
        logger,
        im_series_dtos,
        cable_series_dtos,
        input_im_cable_system_dtos,
        build_model_orchestrator,
    ) -> None:
        """理想ケーブル（完全絶縁かつ理想導体）の場合の動作を確認する。"""
        orchestrator = VoltageCurrentCalculationOrchestrator.create(
            config=config, logger=logger
        )

        # 理想ケーブル（MAIN_IDEAL + MLE_IDEAL）を使用する入力DTOを探す
        ideal_cable_input_dto = None
        for input_dto in input_im_cable_system_dtos:
            if (
                input_dto.cable is not None
                and input_dto.cable.name.get_value() == "ALL_BASIC_IDEAL"
            ):
                ideal_cable_input_dto = input_dto
                break

        if ideal_cable_input_dto is None:
            pytest.skip("理想ケーブルの入力DTOが見つかりませんでした。")

        model_dto = _build_model_dto(
            input_dto=ideal_cable_input_dto,
            im_series_dtos=im_series_dtos,
            cable_series_dtos=cable_series_dtos,
            build_model_orchestrator=build_model_orchestrator,
        )

        result = orchestrator.calculate(model_dto=model_dto)

        # 理想ケーブルの場合、ケーブル終点の電圧・電流が入力電圧・電流と一致すること
        # （ケーブルによる影響がない）
        input_phase_voltage = result.cable_voltage_current.input_phase_voltage
        end_point_phase_voltage = (
            result.cable_voltage_current.end_point_phase_voltage
        )
        input_phase_current = result.cable_voltage_current.input_phase_current
        end_point_phase_current = (
            result.cable_voltage_current.end_point_phase_current
        )

        np.testing.assert_allclose(
            end_point_phase_voltage.value,
            input_phase_voltage.value,
            rtol=1e-10,
            atol=1e-12,
        )
        np.testing.assert_allclose(
            end_point_phase_current.value,
            input_phase_current.value,
            rtol=1e-10,
            atol=1e-12,
        )

    def test_calculate_phase_voltage_conversion(
        self,
        config,
        logger,
        im_series_dtos,
        cable_series_dtos,
        input_im_cable_system_dtos,
        build_model_orchestrator,
    ) -> None:
        """線間電圧から相電圧への変換を検証する。"""
        orchestrator = VoltageCurrentCalculationOrchestrator.create(
            config=config, logger=logger
        )

        input_dto = input_im_cable_system_dtos[0]
        model_dto = _build_model_dto(
            input_dto=input_dto,
            im_series_dtos=im_series_dtos,
            cable_series_dtos=cable_series_dtos,
            build_model_orchestrator=build_model_orchestrator,
        )

        result = orchestrator.calculate(model_dto=model_dto)

        # 入力線間電圧から相電圧への変換が正しく行われること（スター結線を想定）
        input_line_voltage = result.cable_voltage_current.input_line_voltage
        input_phase_voltage = result.cable_voltage_current.input_phase_voltage

        # 相電圧の大きさが線間電圧の大きさの1/√3倍であること
        line_voltage_magnitude = np.abs(input_line_voltage.value)
        phase_voltage_magnitude = np.abs(input_phase_voltage.value)
        expected_phase_voltage_magnitude = line_voltage_magnitude / np.sqrt(3.0)

        np.testing.assert_allclose(
            phase_voltage_magnitude,
            expected_phase_voltage_magnitude,
            rtol=1e-10,
            atol=1e-12,
        )

    def test_calculate_input_current_calculation(
        self,
        config,
        logger,
        im_series_dtos,
        cable_series_dtos,
        input_im_cable_system_dtos,
        build_model_orchestrator,
    ) -> None:
        """入力相電流の計算を検証する。"""
        orchestrator = VoltageCurrentCalculationOrchestrator.create(
            config=config, logger=logger
        )

        input_dto = input_im_cable_system_dtos[0]
        model_dto = _build_model_dto(
            input_dto=input_dto,
            im_series_dtos=im_series_dtos,
            cable_series_dtos=cable_series_dtos,
            build_model_orchestrator=build_model_orchestrator,
        )

        result = orchestrator.calculate(model_dto=model_dto)

        # システムアドミタンスから入力相電流が正しく計算されること
        # オームの法則（I = V * Y）が成り立つこと
        input_phase_voltage = result.cable_voltage_current.input_phase_voltage
        input_phase_current = result.cable_voltage_current.input_phase_current
        system_admittance = model_dto.system.system_phase_admittance

        # I = V * Y の関係を検証
        calculated_current = input_phase_voltage.value * system_admittance.value
        np.testing.assert_allclose(
            input_phase_current.value,
            calculated_current,
            rtol=1e-10,
            atol=1e-12,
        )

    def test_calculate_with_insulated_cable(
        self,
        config,
        logger,
        im_series_dtos,
        cable_series_dtos,
        input_im_cable_system_dtos,
        build_model_orchestrator,
    ) -> None:
        """完全絶縁ケーブルの場合の動作を確認する。"""
        orchestrator = VoltageCurrentCalculationOrchestrator.create(
            config=config, logger=logger
        )

        # 完全絶縁ケーブル（MAIN_INSULATED + MLE_INSULATED）を使用する入力DTOを探す
        insulated_cable_input_dto = None
        for input_dto in input_im_cable_system_dtos:
            if (
                input_dto.cable is not None
                and input_dto.cable.name.get_value() == "INSULATED"
            ):
                insulated_cable_input_dto = input_dto
                break

        if insulated_cable_input_dto is None:
            pytest.skip("完全絶縁ケーブルの入力DTOが見つかりませんでした。")

        model_dto = _build_model_dto(
            input_dto=insulated_cable_input_dto,
            im_series_dtos=im_series_dtos,
            cable_series_dtos=cable_series_dtos,
            build_model_orchestrator=build_model_orchestrator,
        )

        result = orchestrator.calculate(model_dto=model_dto)

        # 完全絶縁ケーブルの場合、地絡電流が0であること
        ground_current = result.cable_voltage_current.ground_current
        ground_current_up = ground_current[PieCableGroundKey.UPSTREAM]
        ground_current_down = ground_current[PieCableGroundKey.DOWNSTREAM]

        np.testing.assert_allclose(
            ground_current_up.value, 0.0, rtol=1e-10, atol=1e-12
        )
        np.testing.assert_allclose(
            ground_current_down.value, 0.0, rtol=1e-10, atol=1e-12
        )

        # 導線電流が入力電流と一致すること
        input_phase_current = result.cable_voltage_current.input_phase_current
        conductor_current = result.cable_voltage_current.conductor_current[
            PieCableConductorKey.SINGLE
        ]

        np.testing.assert_allclose(
            conductor_current.value,
            input_phase_current.value,
            rtol=1e-10,
            atol=1e-12,
        )

    def test_calculate_with_ideal_conductor(
        self,
        config,
        logger,
        im_series_dtos,
        cable_series_dtos,
        input_im_cable_system_dtos,
        build_model_orchestrator,
    ) -> None:
        """理想導体ケーブルの場合の動作を確認する。"""
        orchestrator = VoltageCurrentCalculationOrchestrator.create(
            config=config, logger=logger
        )

        # 理想導体ケーブル（MAIN_CONDUCTOR_IDEAL + MLE_CONDUCTOR_IDEAL）を使用する入力DTOを探す
        ideal_conductor_input_dto = None
        for input_dto in input_im_cable_system_dtos:
            if (
                input_dto.cable is not None
                and input_dto.cable.name.get_value() == "CONDUCTOR_IDEAL"
            ):
                ideal_conductor_input_dto = input_dto
                break

        if ideal_conductor_input_dto is None:
            pytest.skip("理想導体ケーブルの入力DTOが見つかりませんでした。")

        model_dto = _build_model_dto(
            input_dto=ideal_conductor_input_dto,
            im_series_dtos=im_series_dtos,
            cable_series_dtos=cable_series_dtos,
            build_model_orchestrator=build_model_orchestrator,
        )

        result = orchestrator.calculate(model_dto=model_dto)

        # 理想導体ケーブルの場合、導線電圧降下が0であること
        input_phase_voltage = result.cable_voltage_current.input_phase_voltage
        end_point_phase_voltage = (
            result.cable_voltage_current.end_point_phase_voltage
        )

        # ケーブル終点の電圧が入力電圧と一致すること
        np.testing.assert_allclose(
            end_point_phase_voltage.value,
            input_phase_voltage.value,
            rtol=1e-10,
            atol=1e-12,
        )

    def test_calculate_l_circuit(
        self,
        config,
        logger,
        im_series_dtos,
        cable_series_dtos,
        input_im_cable_system_dtos,
        build_model_orchestrator,
    ) -> None:
        """L型等価回路の計算を検証する。"""
        orchestrator = VoltageCurrentCalculationOrchestrator.create(
            config=config, logger=logger
        )

        # L型等価回路を使用する入力DTOを探す（TEST1はL型）
        l_circuit_input_dto = None
        for input_dto in input_im_cable_system_dtos:
            if input_dto.im.im_series.name.get_value() == "TEST1":
                l_circuit_input_dto = input_dto
                break

        if l_circuit_input_dto is None:
            pytest.skip("L型等価回路の入力DTOが見つかりませんでした。")

        model_dto = _build_model_dto(
            input_dto=l_circuit_input_dto,
            im_series_dtos=im_series_dtos,
            cable_series_dtos=cable_series_dtos,
            build_model_orchestrator=build_model_orchestrator,
        )

        result = orchestrator.calculate(model_dto=model_dto)

        # L型等価回路の場合、正しく電圧・電流が計算されること
        assert result.im_voltage_current is not None
        assert result.im_voltage_current.im_excitation_current is not None
        assert result.im_voltage_current.im_primary_current is not None
        assert (
            result.im_voltage_current.get_secondary_total_current() is not None
        )

        # KCL（キルヒホッフの電流則）が成り立つこと
        im_input_current = result.im_voltage_current.im_input_current.value
        excitation_current = (
            result.im_voltage_current.im_excitation_current.value
        )
        series_current = result.im_voltage_current.im_primary_current.value

        # 入力電流 = 励磁電流 + 直列枝電流（L型回路の場合）
        calculated_input_current = excitation_current + series_current
        np.testing.assert_allclose(
            im_input_current,
            calculated_input_current,
            rtol=1e-10,
            atol=1e-12,
        )

    def test_calculate_t_circuit(
        self,
        config,
        logger,
        im_series_dtos,
        cable_series_dtos,
        input_im_cable_system_dtos,
        build_model_orchestrator,
    ) -> None:
        """T型等価回路の計算を検証する。"""
        orchestrator = VoltageCurrentCalculationOrchestrator.create(
            config=config, logger=logger
        )

        # T型等価回路を使用する入力DTOを探す（TEST2はT型）
        t_circuit_input_dto = None
        for input_dto in input_im_cable_system_dtos:
            if input_dto.im.im_series.name.get_value() == "TEST2":
                t_circuit_input_dto = input_dto
                break

        if t_circuit_input_dto is None:
            pytest.skip("T型等価回路の入力DTOが見つかりませんでした。")

        model_dto = _build_model_dto(
            input_dto=t_circuit_input_dto,
            im_series_dtos=im_series_dtos,
            cable_series_dtos=cable_series_dtos,
            build_model_orchestrator=build_model_orchestrator,
        )

        result = orchestrator.calculate(model_dto=model_dto)

        # T型等価回路の場合、正しく電圧・電流が計算されること
        assert result.im_voltage_current is not None
        assert result.im_voltage_current.im_excitation_current is not None
        assert result.im_voltage_current.im_primary_current is not None
        assert (
            result.im_voltage_current.get_secondary_total_current() is not None
        )

        # KCL（キルヒホッフの電流則）が成り立つこと
        im_input_current = result.im_voltage_current.im_input_current.value
        excitation_current = (
            result.im_voltage_current.im_excitation_current.value
        )
        primary_current = result.im_voltage_current.im_primary_current.value
        secondary_current = (
            result.im_voltage_current.get_secondary_total_current().value
        )

        # T型回路の場合:
        # - 入力電流 = 一次電流（一次側の電流は入力電流と同じ）
        # - 一次電流 = 励磁電流 + 二次電流
        np.testing.assert_allclose(
            im_input_current,
            primary_current,
            rtol=1e-10,
            atol=1e-12,
        )
        calculated_primary_current = excitation_current + secondary_current
        np.testing.assert_allclose(
            primary_current,
            calculated_primary_current,
            rtol=1e-10,
            atol=1e-12,
        )

    def test_t_circuit_secondary_current_matches_ohms_law(
        self,
        config,
        logger,
        im_series_dtos,
        cable_series_dtos,
        input_im_cable_system_dtos,
        build_model_orchestrator,
    ) -> None:
        """T型二次電流が KCL 導出とオーム則導出で一致することを検証する。

        計算器は二次電流を KCL（I2 = I1 - I_m）で求める。ロジックが
        正しければ、独立した導出であるオーム則（I2 = V_m * Y2）とも
        一致するはずなので、両者の一致をクロスチェックする。
        """
        orchestrator = VoltageCurrentCalculationOrchestrator.create(
            config=config, logger=logger
        )

        # T型等価回路を使用する入力DTOを探す（TEST2はT型）
        t_circuit_input_dto = None
        for input_dto in input_im_cable_system_dtos:
            if input_dto.im.im_series.name.get_value() == "TEST2":
                t_circuit_input_dto = input_dto
                break

        if t_circuit_input_dto is None:
            pytest.skip("T型等価回路の入力DTOが見つかりませんでした。")

        model_dto = _build_model_dto(
            input_dto=t_circuit_input_dto,
            im_series_dtos=im_series_dtos,
            cable_series_dtos=cable_series_dtos,
            build_model_orchestrator=build_model_orchestrator,
        )

        result = orchestrator.calculate(model_dto=model_dto)
        im_vc = result.im_voltage_current

        # KCL 導出（I2 は I1 から I_m を引いた値）
        secondary_current_kcl = im_vc.get_secondary_total_current().value
        # オーム則導出（I2 は V_m と Y2 の積）
        excitation_voltage = im_vc.im_excitation_voltage.to_base_unit().value
        secondary_admittance = (
            model_dto.im.secondary_model.admittances[
                ImSecondaryCageBranchType.SINGLE
            ]
            .to_base_unit()
            .value
        )
        secondary_current_ohms = excitation_voltage * secondary_admittance

        # 退化ケースで相対比較が破綻しないよう、絶対許容を電流スケールで与える
        current_scale = float(np.max(np.abs(secondary_current_kcl))) + 1.0
        np.testing.assert_allclose(
            secondary_current_kcl,
            secondary_current_ohms,
            rtol=1e-9,
            atol=current_scale * 1e-9,
        )

    def test_calculate_kirchhoff_laws(
        self,
        config,
        logger,
        im_series_dtos,
        cable_series_dtos,
        input_im_cable_system_dtos,
        build_model_orchestrator,
    ) -> None:
        """キルヒホッフの法則を検証する。"""
        orchestrator = VoltageCurrentCalculationOrchestrator.create(
            config=config, logger=logger
        )

        input_dto = input_im_cable_system_dtos[0]
        model_dto = _build_model_dto(
            input_dto=input_dto,
            im_series_dtos=im_series_dtos,
            cable_series_dtos=cable_series_dtos,
            build_model_orchestrator=build_model_orchestrator,
        )

        result = orchestrator.calculate(model_dto=model_dto)

        # KCL: 入力電流 = 励磁電流 + 一次電流（または直列枝電流）
        im_input_current = result.im_voltage_current.im_input_current.value
        excitation_current = (
            result.im_voltage_current.im_excitation_current.value
        )

        # 回路タイプに応じて検証
        circuit_type = model_dto.im.circuit_type
        if circuit_type == ImCircuitType.L:
            series_current = result.im_voltage_current.im_primary_current.value
            calculated_input_current = excitation_current + series_current
        else:  # T型
            secondary_current = (
                result.im_voltage_current.get_secondary_total_current().value
            )
            calculated_input_current = excitation_current + secondary_current

        np.testing.assert_allclose(
            im_input_current,
            calculated_input_current,
            rtol=1e-10,
            atol=1e-12,
        )

        # KVL: 各地点の電圧関係が正しいこと  # noqa: ERA001
        # ケーブル終点の電圧 = IM入力電圧  # noqa: ERA001
        cable_end_voltage = (
            result.cable_voltage_current.end_point_phase_voltage.value
        )
        im_input_voltage = result.im_voltage_current.im_input_voltage.value

        np.testing.assert_allclose(
            cable_end_voltage,
            im_input_voltage,
            rtol=1e-10,
            atol=1e-12,
        )

    def test_calculate_ohms_law(
        self,
        config,
        logger,
        im_series_dtos,
        cable_series_dtos,
        input_im_cable_system_dtos,
        build_model_orchestrator,
    ) -> None:
        """オームの法則を検証する。"""
        orchestrator = VoltageCurrentCalculationOrchestrator.create(
            config=config, logger=logger
        )

        input_dto = input_im_cable_system_dtos[0]
        model_dto = _build_model_dto(
            input_dto=input_dto,
            im_series_dtos=im_series_dtos,
            cable_series_dtos=cable_series_dtos,
            build_model_orchestrator=build_model_orchestrator,
        )

        result = orchestrator.calculate(model_dto=model_dto)

        # I = V * Y の関係が成り立つこと（励磁電流の計算）
        excitation_voltage = (
            result.im_voltage_current.im_excitation_voltage.value
        )
        excitation_current = (
            result.im_voltage_current.im_excitation_current.value
        )
        excitation_admittance = model_dto.im.excitation_admittance.value

        calculated_excitation_current = (
            excitation_voltage * excitation_admittance
        )
        np.testing.assert_allclose(
            excitation_current,
            calculated_excitation_current,
            rtol=1e-10,
            atol=1e-12,
        )

        # V = I * Z の関係が成り立つこと（一次側電圧降下の計算）
        # 回路タイプに応じて検証
        circuit_type = model_dto.im.circuit_type
        im_primary_current = result.im_voltage_current.im_primary_current.value
        im_primary_impedance = model_dto.im.primary_impedance.value

        if circuit_type == ImCircuitType.L:
            # L型回路の場合、im_primary_voltageは一次側の電圧降下
            # ただし、L型回路では一次側の電圧降下は直列枝電流と一次インピーダンスの積
            # 実際には、im_primary_voltageは一次側の電圧降下を表す
            primary_voltage = result.im_voltage_current.im_primary_voltage.value
            calculated_primary_voltage = (
                im_primary_current * im_primary_impedance
            )
            np.testing.assert_allclose(
                primary_voltage,
                calculated_primary_voltage,
                rtol=1e-10,
                atol=1e-12,
            )
        else:  # T型回路
            # T型回路の場合、im_primary_voltageは一次側の電圧降下
            # 一次側の電圧降下 = 入力電流 * 一次インピーダンス  # noqa: ERA001
            primary_voltage = result.im_voltage_current.im_primary_voltage.value
            im_input_current = result.im_voltage_current.im_input_current.value
            calculated_primary_voltage = im_input_current * im_primary_impedance
            np.testing.assert_allclose(
                primary_voltage,
                calculated_primary_voltage,
                rtol=1e-10,
                atol=1e-12,
            )

    def test_calculate_array_shapes_consistency(
        self,
        config,
        logger,
        im_series_dtos,
        cable_series_dtos,
        input_im_cable_system_dtos,
        build_model_orchestrator,
    ) -> None:
        """代表 InputDto で配列形状の一貫性を検証する。"""
        orchestrator = VoltageCurrentCalculationOrchestrator.create(
            config=config, logger=logger
        )

        input_dto = input_im_cable_system_dtos[0]
        model_dto = _build_model_dto(
            input_dto=input_dto,
            im_series_dtos=im_series_dtos,
            cable_series_dtos=cable_series_dtos,
            build_model_orchestrator=build_model_orchestrator,
        )

        result = orchestrator.calculate(model_dto=model_dto)

        expected_shape = model_dto.array_layout.shape

        # 全ての電圧・電流配列がモデルの配列形状と一致すること
        assert (
            result.cable_voltage_current.input_phase_voltage.value.shape
            == expected_shape
        )
        assert (
            result.im_voltage_current.im_input_voltage.value.shape
            == expected_shape
        )

        # ケーブル終点とIM入力で配列形状が一致すること
        assert (
            result.cable_voltage_current.end_point_phase_voltage.value.shape
            == result.im_voltage_current.im_input_voltage.value.shape
        )
