"""特性値計算（im_cable_system）の単体テスト（単一かご / Single cage）。

回転速度・トルク・効率の各計算器と、それらを束ねる
``CharacteristicsCalculationOrchestrator`` の定義式契約を、最小スタブで検証する。
教科書値（運転点一致）の検証は ``orchestrate/forward`` 側に集約している。
"""

from __future__ import annotations

from typing import cast

import numpy as np
import pytest

from im_cable_system.engine.algorithm.execute_algorithm.simulate.characteristic.calculate_efficiency import (  # noqa: E501
    EfficiencyCalculator,
)
from im_cable_system.engine.algorithm.execute_algorithm.simulate.characteristic.calculate_rotational_speed import (  # noqa: E501
    RotationalSpeedCalculator,
)
from im_cable_system.engine.algorithm.execute_algorithm.simulate.characteristic.calculate_torque import (  # noqa: E501
    TorqueCalculator,
)
from im_cable_system.engine.algorithm.execute_algorithm.simulate.characteristic.orchestrate import (  # noqa: E501
    CharacteristicsCalculationOrchestrator,
)
from im_cable_system.engine.shared.config import (
    IConfig,
    ILogger,
)
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ArrayKey,
    ArrayLayoutDto,
    ImCageMultiplicityType,
    ImSecondaryCageBranchType,
    PieCableConductorKey,
    PieCableGroundKey,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexPowerDto,
    ArrayFrequencyDto,
    ArrayRotationalSpeedDto,
    ArraySlipDto,
)
from im_cable_system.engine.shared.dto.itm import (
    ItmCablePowerDto,
    ItmEfficiencyDto,
    ItmImPowerDto,
    ItmPowerDto,
)
from im_cable_system.engine.shared.numerical_stability import (
    event_codes,
    numerical_stability_scope,
)


class _DummyLogger:
    """@timer 用の最小 ILogger スタブ。"""

    def info(self, _msg: str, *_args: object) -> None:
        pass

    def warning(self, _msg: str, *_args: object) -> None:
        pass

    def error(self, _msg: str, *_args: object) -> None:
        pass


class _DummyNumericalGuardConfig:
    """numerical_guard_config の最小スタブ（eps のみ）。"""

    eps = 1e-12


class _DummyConfig:
    config_file_path = "dummy"
    numerical_guard_config = _DummyNumericalGuardConfig()


def _dummy_config() -> IConfig:
    """テスト用 config スタブを IConfig として返す。"""
    return cast(IConfig, _DummyConfig())


def _dummy_logger() -> ILogger:
    """テスト用 logger スタブを ILogger として返す。"""
    return cast(ILogger, _DummyLogger())


def _make_array_layout() -> ArrayLayoutDto:
    """回転速度計算に必要な最小ArrayLayoutDtoを作る。"""
    return ArrayLayoutDto(
        arrays={
            ArrayKey.SLIP: ArraySlipDto(value=np.array([0.0, 0.5]), unit="-"),
            ArrayKey.FREQUENCY: ArrayFrequencyDto(
                value=np.array([50.0]), unit="Hz"
            ),
        },
        reference_axes=[ArrayKey.SLIP, ArrayKey.FREQUENCY],
    )


def _make_power_dto(
    *,
    system_total_input_w: float,
    cable_end_w: float,
    im_input_w: float,
    im_output_w: float,
    shape: tuple[int, ...] = (1, 1),
) -> ItmPowerDto:
    """効率・トルク計算に必要な最小のItmPowerDtoを作る。"""

    def p(v: float) -> ArrayComplexPowerDto:
        return ArrayComplexPowerDto(
            value=np.full(shape, v + 0.0j, dtype=np.complex128),
            unit="VA",
        )

    cable_power = ItmCablePowerDto(
        system_total_input_power=p(system_total_input_w),
        input_phase_power=p(system_total_input_w),
        conductor_loss_power={PieCableConductorKey.SINGLE: p(0.0)},
        ground_loss_power={
            PieCableGroundKey.UPSTREAM: p(0.0),
            PieCableGroundKey.DOWNSTREAM: p(0.0),
        },
        end_point_phase_power=p(cable_end_w),
        total_loss_power=p(system_total_input_w - cable_end_w),
    )

    im_power = ItmImPowerDto(
        input_power=p(im_input_w),
        primary_loss_power=p(0.0),
        excitation_loss_power=p(0.0),
        output_power=p(im_output_w),
        cage_multiplicity=ImCageMultiplicityType.SINGLE_CAGE,
        secondary_base_loss_power={ImSecondaryCageBranchType.SINGLE: p(0.0)},
        secondary_load_power={ImSecondaryCageBranchType.SINGLE: p(im_output_w)},
        secondary_branch_total_power={
            ImSecondaryCageBranchType.SINGLE: p(im_output_w)
        },
        secondary_total_power=p(im_output_w),
        friction_windage_loss_power=p(0.0),
        stray_load_loss_power=p(0.0),
        total_loss_power=p(0.0),
        copper_loss_power=p(0.0),
        iron_loss_power=p(0.0),
    )

    return ItmPowerDto(im_power=im_power, cable_power=cable_power)


def test_rotational_speed_calculator_basic() -> None:
    """回転速度が定義式どおりに計算されること。"""
    calc = RotationalSpeedCalculator.create(
        config=_dummy_config(), logger=_dummy_logger()
    )
    array_layout = _make_array_layout()

    result = calc.calculate(array_layout=array_layout, poles=4)
    value = result.to_base_unit().get_value()

    # shape = (slip=2, frequency=1)
    assert value.shape == (2, 1)

    expected_rpm = np.array([[1500.0], [750.0]])
    expected_rad_s = expected_rpm * (2.0 * np.pi / 60.0)
    assert np.allclose(value, expected_rad_s)


def test_torque_calculator_basic() -> None:
    """トルク=出力有効電力/角速度 で計算されること。"""
    calc = TorqueCalculator.create(
        config=_dummy_config(), logger=_dummy_logger()
    )

    power_dto = _make_power_dto(
        system_total_input_w=2000.0,
        cable_end_w=1800.0,
        im_input_w=1800.0,
        im_output_w=1000.0,
    )
    rotational_speed = ArrayRotationalSpeedDto(
        value=np.array([[100.0]]), unit="rad/s"
    )

    torque = calc.calculate(
        power_dto=power_dto, rotational_speed=rotational_speed
    )
    assert np.allclose(torque.to_base_unit().get_value(), np.array([[10.0]]))


def test_efficiency_calculator_basic() -> None:
    """system/im/cable の3効率が定義通りに計算されること。"""
    calc = EfficiencyCalculator.create(
        config=_dummy_config(), logger=_dummy_logger()
    )

    power_dto = _make_power_dto(
        system_total_input_w=2000.0,
        cable_end_w=1800.0,
        im_input_w=1800.0,
        im_output_w=1700.0,
    )

    eff: ItmEfficiencyDto = calc.calculate(power_dto=power_dto)
    assert np.allclose(eff.system_efficiency.get_value(), np.array([[0.85]]))
    assert np.allclose(
        eff.im_efficiency.get_value(), np.array([[1700.0 / 1800.0]])
    )
    assert np.allclose(eff.cable_efficiency.get_value(), np.array([[0.9]]))


def test_characteristics_calculation_orchestrator_basic() -> None:
    """オーケストレーターが特性値DTOを統合して返すこと。"""
    orchestrator = CharacteristicsCalculationOrchestrator.create(
        config=_dummy_config(),
        logger=_dummy_logger(),
    )

    array_layout = _make_array_layout()
    power_dto = _make_power_dto(
        system_total_input_w=2000.0,
        cable_end_w=1800.0,
        im_input_w=1800.0,
        im_output_w=1700.0,
        shape=array_layout.shape,
    )

    # minimal stub for model_dto (poles only)
    class _Poles:
        value = 4

    class _Im:
        poles = _Poles()

    class _ModelDto:
        def __init__(self, array_layout: ArrayLayoutDto) -> None:
            self.im = _Im()
            self.array_layout = array_layout

    characteristic = orchestrator.calculate(
        model_dto=_ModelDto(array_layout=array_layout),  # type: ignore[arg-type]
        power_dto=power_dto,
    )

    assert (
        characteristic.rotational_speed.rotational_speed.get_value().shape
        == (2, 1)
    )
    assert characteristic.torque.torque.get_value().shape == (2, 1)
    assert characteristic.efficiency.system_efficiency.get_value().shape == (
        2,
        1,
    )


def test_efficiency_raises_when_output_exceeds_input() -> None:
    """P_out>P_in の場合はクランプせず ValueError を送出する。"""
    calc = EfficiencyCalculator.create(
        config=_dummy_config(), logger=_dummy_logger()
    )

    # im_eff のみ P_out が P_in を上回る。
    power_dto = _make_power_dto(
        system_total_input_w=2000.0,
        cable_end_w=1800.0,
        im_input_w=1000.0,
        im_output_w=1000.0 * (1.0 + 1.0e-9),
    )

    with pytest.raises(ValueError, match="1.0を超える"):
        calc.calculate(power_dto=power_dto)


def test_efficiency_warns_on_reversed_power_flow() -> None:
    """入出力で有効電力の符号が反転する場合、警告を出しつつ計算継続する。"""

    class _RecordingLogger(_DummyLogger):
        """warning 呼び出しを記録するロガースタブ。"""

        def __init__(self) -> None:
            self.warnings: list[str] = []

        def warning(self, msg: str, *_args: object) -> None:
            self.warnings.append(msg)

    logger = _RecordingLogger()
    calc = EfficiencyCalculator.create(
        config=_dummy_config(),
        logger=cast(ILogger, logger),
    )

    # im_output のみ符号反転（逆潮流）。|out| < |in| なので効率自体は valid。
    power_dto = _make_power_dto(
        system_total_input_w=2000.0,
        cable_end_w=1800.0,
        im_input_w=1800.0,
        im_output_w=-1000.0,
    )

    eff: ItmEfficiencyDto = calc.calculate(power_dto=power_dto)

    # 効率は絶対値ベースで計算される（im: 1000/1800）。
    assert np.allclose(
        eff.im_efficiency.get_value(), np.array([[1000.0 / 1800.0]])
    )
    # system(2000 vs -1000) と im(1800 vs -1000) で符号反転を検出。
    assert any("逆潮流" in msg for msg in logger.warnings)
    assert sum("逆潮流" in msg for msg in logger.warnings) == 2


def test_torque_returns_nan_and_records_event_at_omega_eps_boundary() -> None:
    """角速度が eps ちょうど（<=eps 境界）の要素は NaN になりイベント記録。"""
    calc = TorqueCalculator.create(
        config=_dummy_config(), logger=_dummy_logger()
    )

    power_dto = _make_power_dto(
        system_total_input_w=2000.0,
        cable_end_w=1800.0,
        im_input_w=1800.0,
        im_output_w=1000.0,
    )
    rotational_speed = ArrayRotationalSpeedDto(
        value=np.array([[1e-12]]), unit="rad/s"
    )

    with numerical_stability_scope() as accumulator:
        torque = calc.calculate(
            power_dto=power_dto, rotational_speed=rotational_speed
        )

    assert np.isnan(torque.to_base_unit().get_value()).all()
    assert accumulator.to_sorted_items() == (
        (event_codes.OMEGA_NEAR_ZERO_TORQUE, 1),
    )


def test_rotational_speed_raises_when_slip_axis_missing() -> None:
    """slip 軸が無い ArrayLayout では ValueError を送出する。"""
    calc = RotationalSpeedCalculator.create(
        config=_dummy_config(), logger=_dummy_logger()
    )
    array_layout = ArrayLayoutDto(
        arrays={
            ArrayKey.FREQUENCY: ArrayFrequencyDto(
                value=np.array([50.0]), unit="Hz"
            ),
        },
        reference_axes=[ArrayKey.FREQUENCY],
    )

    with pytest.raises(ValueError, match="存在しません"):
        calc.calculate(array_layout=array_layout, poles=4)


def test_rotational_speed_raises_when_slip_dto_type_mismatch() -> None:
    """slip 軸の DTO 型が ArraySlipDto でない場合は ValueError を送出する。"""
    calc = RotationalSpeedCalculator.create(
        config=_dummy_config(), logger=_dummy_logger()
    )
    array_layout = ArrayLayoutDto(
        arrays={
            ArrayKey.SLIP: ArrayFrequencyDto(value=np.array([1.0]), unit="Hz"),
            ArrayKey.FREQUENCY: ArrayFrequencyDto(
                value=np.array([50.0]), unit="Hz"
            ),
        },
        reference_axes=[ArrayKey.SLIP, ArrayKey.FREQUENCY],
    )

    with pytest.raises(ValueError, match="ArraySlipDto"):
        calc.calculate(array_layout=array_layout, poles=4)


@pytest.mark.parametrize("poles", [0, -2, 3])
def test_rotational_speed_raises_when_poles_invalid(poles: int) -> None:
    """poles が正の偶数でない場合は ValueError を送出する。"""
    calc = RotationalSpeedCalculator.create(
        config=_dummy_config(), logger=_dummy_logger()
    )
    array_layout = _make_array_layout()

    with pytest.raises(ValueError, match="正の偶数"):
        calc.calculate(array_layout=array_layout, poles=poles)
