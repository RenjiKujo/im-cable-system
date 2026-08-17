"""電力計算オーケストレーター（単一かご / Single cage）の単体テスト。

定義式（線量・相量ベースの三相電力、IM 銅損の加算）に対する契約を、
手組みの ``ItmVoltageCurrentDto`` と最小スタブモデルで検証する。
教科書値（運転点一致）の検証は ``orchestrate/forward`` 側に集約している。
"""

from __future__ import annotations

import numpy as np

from im_cable_system.engine.algorithm.execute_algorithm.simulate.power.orchestrate import (  # noqa: E501
    PowerCalculationOrchestrator,
)
from im_cable_system.engine.domain.physics.electrical import (
    add_power,
    phase_to_line_current_star,
    power_from_voltage_and_current,
    to_three_phase_power_from_phase,
)
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ImCageMultiplicityType,
    ImFrictionWindageModelDto,
    ImFrictionWindageModelType,
    ImSecondaryCageBranchType,
    ImStrayLoadModelDto,
    ImStrayLoadModelType,
    PieCableConductorKey,
    PieCableGroundKey,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexCurrentDto,
    ArrayComplexVoltageDto,
)
from im_cable_system.engine.shared.dto.itm import (
    ItmCableVoltageCurrentDto,
    ItmImVoltageCurrentDto,
    ItmVoltageCurrentDto,
)


class _DummyLogger:
    """@timer 用の最小 ILogger スタブ。"""

    def info(self, _msg: str, *_args: object) -> None:
        pass

    def warning(self, _msg: str, *_args: object) -> None:
        pass

    def error(self, _msg: str, *_args: object) -> None:
        pass


class _DummyConfig:
    config_file_path = "dummy"


# テスト用の数値ガードしきい値（domain 既定値撤廃に伴いテストから明示注入）。
_EPS: float = 1e-12
_MAX_MAG: float = 1.0 / _EPS


def test_power_calculation_orchestrator_pie_single_cage() -> None:
    """最小ケースで電力計算が構築されることを確認する。

    - system_total_input_power は相量ベース（3 V_φ I_φ*）と複素一致する
      （balanced 規約では線量ベース √3 V_LL I_L* が補正なしで相量ベースに一致）
    - system_total_input_power == input_phase_power（相量基準で一致）
    - input_phase_power / end_point_phase_power は相量ベース（3 V I*）と一致
    - IM銅損は primary_loss + secondary_base_loss の加算で一致
    - IM入力電力は全損失 + 出力の保存則と一致
    """

    # 2x1 の最小配列（slip x frequency を想定）。
    # 相量を基準に置き、線量は balanced 規約で物理的に整合させて作る
    # （v_line = √3 v_phase（同位相）, i_line = i_phase）。これにより
    # system_total_input_power（線量ベース・補正なし）が相量ベースと一致するか
    # を検証できる（任意値だと一致しないため、規約に沿った整合が必須）。
    v_phase = ArrayComplexVoltageDto(
        value=np.array([[60.0 + 0.0j], [61.0 + 0.0j]]),
        unit="V",
    )
    i_phase = ArrayComplexCurrentDto(
        value=np.array([[10.0 - 1.0j], [9.0 - 0.5j]]),
        unit="A",
    )
    # balanced 規約: 線間電圧は相電圧と同位相で大きさ √3 倍。
    v_line = ArrayComplexVoltageDto(
        value=v_phase.value * np.sqrt(3.0),
        unit=v_phase.get_unit(),
    )
    i_line = phase_to_line_current_star(
        phase_current_dto=i_phase, eps=_EPS, max_mag=_MAX_MAG
    )

    cable_vc = ItmCableVoltageCurrentDto(
        input_line_voltage=v_line,
        input_line_current=i_line,
        input_phase_voltage=v_phase,
        input_phase_current=i_phase,
        conductor_voltage={PieCableConductorKey.SINGLE: v_phase},
        conductor_current={PieCableConductorKey.SINGLE: i_phase},
        ground_voltage={
            PieCableGroundKey.UPSTREAM: v_phase,
            PieCableGroundKey.DOWNSTREAM: v_phase,
        },
        ground_current={
            PieCableGroundKey.UPSTREAM: i_phase,
            PieCableGroundKey.DOWNSTREAM: i_phase,
        },
        end_point_phase_voltage=v_phase,
        end_point_phase_current=i_phase,
    )

    im_input_voltage = ArrayComplexVoltageDto(
        value=v_phase.value * 4.0,
        unit=v_phase.get_unit(),
    )
    im_vc = ItmImVoltageCurrentDto(
        im_input_voltage=im_input_voltage,
        im_input_current=i_phase,
        im_primary_voltage=v_phase,
        im_primary_current=i_phase,
        im_excitation_voltage=v_phase,
        im_excitation_current=i_phase,
        cage_multiplicity=ImCageMultiplicityType.SINGLE_CAGE,
        secondary_base_voltage={ImSecondaryCageBranchType.SINGLE: v_phase},
        secondary_load_voltage={ImSecondaryCageBranchType.SINGLE: v_phase},
        secondary_branch_current={ImSecondaryCageBranchType.SINGLE: i_phase},
    )

    vc = ItmVoltageCurrentDto(
        im_voltage_current=im_vc,
        cable_voltage_current=cable_vc,
    )

    # calculate 用に最小スタブを用意
    class _CableModel:
        def __init__(self) -> None:
            self.cable_immittance = object()

    class _SecondaryModel:
        def __init__(self) -> None:
            self.cage_multiplicity = ImCageMultiplicityType.SINGLE_CAGE

    class _ImModel:
        def __init__(self) -> None:
            self.secondary_model = _SecondaryModel()
            self.friction_windage_model = ImFrictionWindageModelDto(
                name=ImFrictionWindageModelType.NONE
            )
            self.stray_load_model = ImStrayLoadModelDto(
                name=ImStrayLoadModelType.NONE
            )

    class _ModelDto:
        def __init__(self) -> None:
            self.cable = _CableModel()
            self.im = _ImModel()

    orchestrator = PowerCalculationOrchestrator.create(
        config=_DummyConfig(),  # type: ignore[arg-type]
        logger=_DummyLogger(),  # type: ignore[arg-type]
    )
    power = orchestrator.calculate(
        model_dto=_ModelDto(),  # type: ignore[arg-type]
        voltage_current_dto=vc,
    )

    # 相量ベースの3相合計複素電力（S = 3 V_φ I_φ*）。
    expected_phase_total = to_three_phase_power_from_phase(
        single_phase_power_dto=power_from_voltage_and_current(
            voltage=v_phase, current=i_phase
        )
    )

    # balanced 規約では線量ベース（補正なし）が相量ベースと複素一致する。
    assert np.allclose(
        power.cable_power.system_total_input_power.value,
        expected_phase_total.value,
    )
    # 同じ入力点を表すため、相量ベースの input_phase_power とも一致する。
    assert np.allclose(
        power.cable_power.system_total_input_power.to_base_unit().value,
        power.cable_power.input_phase_power.to_base_unit().value,
    )

    assert np.allclose(
        power.cable_power.input_phase_power.value,
        expected_phase_total.value,
    )
    assert np.allclose(
        power.cable_power.end_point_phase_power.value,
        expected_phase_total.value,
    )

    expected_copper = expected_phase_total.to_base_unit()
    expected_copper_value = expected_copper.value + expected_copper.value
    assert np.allclose(
        power.im_power.copper_loss_power.to_base_unit().value,
        expected_copper_value,
    )

    im_power = power.im_power
    branch = ImSecondaryCageBranchType.SINGLE

    assert np.allclose(
        im_power.output_power.to_base_unit().value,
        im_power.secondary_load_power[branch].to_base_unit().value,
    )
    assert np.allclose(
        im_power.iron_loss_power.to_base_unit().value,
        im_power.excitation_loss_power.to_base_unit().value,
    )

    expected_total_loss = add_power(
        power1=im_power.copper_loss_power,
        power2=im_power.iron_loss_power,
    )
    assert np.allclose(
        im_power.total_loss_power.to_base_unit().value,
        expected_total_loss.to_base_unit().value,
    )

    expected_input_power = add_power(
        power1=im_power.total_loss_power,
        power2=im_power.output_power,
    )
    assert np.allclose(
        im_power.input_power.to_base_unit().value,
        expected_input_power.to_base_unit().value,
    )
