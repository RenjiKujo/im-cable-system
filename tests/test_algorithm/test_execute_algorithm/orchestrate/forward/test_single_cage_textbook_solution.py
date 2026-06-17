"""単カゴ forward 実行の教科書値検証（A:インピーダンス〜D:特性値）。

代表 InputDto（``broadcast_TEST1_ALL_BASIC_IDEAL``: 全 BASIC・理想ケーブル・
L 型回路）を ``DirectForwardExecutionOrchestrator.execute`` に通し、教科書
（``test_simulate.py`` 由来）の解と一致することを 1 つの実行結果で検証する。

運転点はすべり 0.036 / 周波数 50 Hz / 線間電圧 200 V（大きさ）。
個別計算器の数値的正しさは ``simulate`` 配下の単体テストで担保済みのため、
ここでは「実行系を通した最終結果」が教科書と一致することのみを確認する。
"""

from __future__ import annotations

import numpy as np

from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.forward.direct_forward_execution_orchestrator import (  # noqa: E501
    DirectForwardExecutionOrchestrator,
)
from im_cable_system.engine.domain.physics import (
    calculate_power_factor,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ImSecondaryCageBranchType,
)
from im_cable_system.engine.shared.dto.input import InputDtos
from im_cable_system.engine.shared.dto.itm import ItmDto
from tests.test_algorithm.test_execute_algorithm.fixtures.textbook_single_cage import (  # noqa: E501
    find_textbook_input,
    resolve_operating_point_index,
)

_SC = ImSecondaryCageBranchType.SINGLE
_RTOL = 1e-2


def _execute_textbook(
    config: IConfig,
    logger: ILogger,
    input_dtos: InputDtos,
) -> ItmDto:
    """教科書ケースを Direct 実行し ItmDto を返す。"""
    input_dto = find_textbook_input(input_dtos)
    orchestrator = DirectForwardExecutionOrchestrator.create(
        config=config,
        logger=logger,
    )
    return orchestrator.execute(input_dto=input_dto)


class TestSingleCageTextbookSolution:
    """forward 実行結果が教科書解と一致することの検証。"""

    def test_impedance_matches_textbook(
        self,
        config,
        logger,
        single_cage_input_im_cable_system_dtos: InputDtos,
    ) -> None:
        """A: 励磁・一次・二次インピーダンスが教科書解と一致する。"""
        itm = _execute_textbook(
            config, logger, single_cage_input_im_cable_system_dtos
        )
        im_model = itm.model.im
        index = resolve_operating_point_index(itm.model.array_layout)

        excitation_z = im_model.excitation_impedance.to_base_unit().value[index]
        assert round(float(np.real(excitation_z)), 2) == 1.87
        assert round(float(np.imag(excitation_z)), 2) == 20.91
        assert round(float(np.abs(excitation_z)), 2) == 20.99

        primary_z = im_model.primary_impedance.to_base_unit().value[index]
        assert round(float(np.real(primary_z)), 2) == 0.4
        assert round(float(np.imag(primary_z)), 2) == 0.56

        secondary_base_z = (
            im_model.secondary_model.base_impedances[_SC]
            .to_base_unit()
            .value[index]
        )
        assert round(float(np.real(secondary_base_z)), 2) == 0.34
        assert round(float(np.imag(secondary_base_z)), 2) == 0.56

        # 二次合成インピーダンス: R2/s = 0.3398 / 0.036 ≈ 9.44
        secondary_z = (
            im_model.secondary_model.impedances[_SC].to_base_unit().value[index]
        )
        assert round(float(np.real(secondary_z)), 2) == 9.44
        assert round(float(np.imag(secondary_z)), 2) == 0.56

    def test_voltage_current_matches_textbook(
        self,
        config,
        logger,
        single_cage_input_im_cable_system_dtos: InputDtos,
    ) -> None:
        """B: 相電圧・各電流の大きさ／有効・無効分が教科書解と一致する。"""
        itm = _execute_textbook(
            config, logger, single_cage_input_im_cable_system_dtos
        )
        assert itm.simulation_result is not None
        vc = itm.simulation_result.voltage_current
        array_layout = itm.model.array_layout
        index = resolve_operating_point_index(array_layout)

        phase_voltage = vc.cable_voltage_current.input_phase_voltage.value[
            index
        ]
        assert np.isclose(np.abs(phase_voltage), 115.5, rtol=_RTOL)

        input_current = vc.cable_voltage_current.input_phase_current.value[
            index
        ]
        assert np.isclose(np.abs(input_current), 13.86, rtol=_RTOL)
        assert np.isclose(abs(np.real(input_current)), 12.08, rtol=_RTOL)
        assert np.isclose(abs(np.imag(input_current)), 6.79, rtol=_RTOL)
        power_factor = abs(np.real(input_current)) / np.abs(input_current)
        assert np.isclose(power_factor, 0.872, rtol=_RTOL)

        im_input_current = vc.im_voltage_current.im_input_current.value[index]
        assert np.isclose(np.abs(im_input_current), 13.86, rtol=_RTOL)

        # 始動電流（すべり 1）
        start_index = resolve_operating_point_index(array_layout, slip=1.0)
        starting_current = vc.im_voltage_current.im_input_current.value[
            start_index
        ]
        assert np.isclose(np.abs(starting_current), 90.9, rtol=_RTOL)

        excitation_current = vc.im_voltage_current.im_excitation_current.value[
            index
        ]
        assert np.isclose(abs(np.real(excitation_current)), 0.49, rtol=_RTOL)
        assert np.isclose(abs(np.imag(excitation_current)), 5.47, rtol=_RTOL)

        secondary_current = (
            vc.im_voltage_current.get_secondary_total_current().value[index]
        )
        assert np.isclose(np.abs(secondary_current), 11.66, rtol=_RTOL)

    def test_power_matches_textbook(
        self,
        config,
        logger,
        single_cage_input_im_cable_system_dtos: InputDtos,
    ) -> None:
        """C: 二次入力・損失・出力・システム力率が教科書解と一致する。"""
        itm = _execute_textbook(
            config, logger, single_cage_input_im_cable_system_dtos
        )
        assert itm.simulation_result is not None
        power = itm.simulation_result.power
        assert power is not None
        index = resolve_operating_point_index(itm.model.array_layout)

        secondary_total = (
            power.im_power.secondary_total_power.to_active_power_array(
                unit="W"
            ).get_value()[index]
        )
        assert np.isclose(secondary_total, 3850.0, rtol=_RTOL)

        secondary_loss = (
            power.im_power.secondary_base_loss_power[_SC]
            .to_active_power_array(unit="W")
            .get_value()[index]
        )
        assert np.isclose(secondary_loss, 139.0, rtol=_RTOL)

        output = (
            power.im_power.secondary_load_power[_SC]
            .to_active_power_array(unit="W")
            .get_value()[index]
        )
        assert np.isclose(output, 3711.0, rtol=_RTOL)

        # NOTE: 力率は相量（スター等価）ベースで検証する。
        system_power_factor = calculate_power_factor(
            power.cable_power.input_phase_power,
            eps=config.numerical_guard_config.eps,
        ).get_value()[index]
        assert np.isclose(system_power_factor, 0.872, rtol=_RTOL)

    def test_characteristics_match_textbook(
        self,
        config,
        logger,
        single_cage_input_im_cable_system_dtos: InputDtos,
    ) -> None:
        """D: 回転速度・トルク・効率が教科書解と一致する。"""
        itm = _execute_textbook(
            config, logger, single_cage_input_im_cable_system_dtos
        )
        assert itm.simulation_result is not None
        characteristic = itm.simulation_result.characteristic
        assert characteristic is not None
        index = resolve_operating_point_index(itm.model.array_layout)

        rotational_speed = (
            characteristic.rotational_speed.rotational_speed.convert_to_unit(
                "rpm"
            ).get_value()[index]
        )
        assert np.isclose(rotational_speed, 1446.0, rtol=_RTOL)

        torque = characteristic.torque.torque.convert_to_unit("Nm").get_value()[
            index
        ]
        assert np.isclose(torque, 24.51, rtol=_RTOL)

        system_efficiency = (
            characteristic.efficiency.system_efficiency.convert_to_unit(
                "%"
            ).get_value()[index]
        )
        im_efficiency = characteristic.efficiency.im_efficiency.convert_to_unit(
            "%"
        ).get_value()[index]
        assert np.isclose(im_efficiency, 88.7, rtol=_RTOL)
        assert np.isclose(system_efficiency, 88.7, rtol=_RTOL)
