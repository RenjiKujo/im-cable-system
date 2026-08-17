"""``single_cage_im_power_calculator`` / ``double_cage_im_power_calculator`` の
軸出力控除（摩擦・風損／漂遊負荷損）反映に関する単体テスト。

検証観点（Plan「テスト」節）:
    ① 両方 ``NONE`` で既存と完全一致（回帰の要）
    ② 片方だけ有効 × 2
    ③ 両方有効で ``output = load - FW - stray``、``total_loss`` に両項、虚部不変
"""

from __future__ import annotations

import numpy as np
import pytest

from im_cable_system.engine.algorithm.execute_algorithm.simulate.power.calculate_im_power.double_cage_im_power_calculator import (  # noqa: E501
    DoubleCageImPowerCalculator,
)
from im_cable_system.engine.algorithm.execute_algorithm.simulate.power.calculate_im_power.single_cage_im_power_calculator import (  # noqa: E501
    SingleCageImPowerCalculator,
)
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    FloatParamDto,
    FloatParamDtos,
    ImCageMultiplicityType,
    ImCircuitType,
    ImConnectionType,
    ImExcitationModelDto,
    ImExcitationModelType,
    ImFrictionWindageModelDto,
    ImFrictionWindageModelType,
    ImName,
    ImPoles,
    ImPrimaryModelDto,
    ImPrimaryModelType,
    ImSecondaryCageBranchType,
    ImSecondaryModelDto,
    ImSecondaryModelType,
    ImSeriesName,
    ImStrayLoadModelDto,
    ImStrayLoadModelType,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexAdmittanceDto,
    ArrayComplexCurrentDto,
    ArrayComplexImpedanceDto,
    ArrayComplexVoltageDto,
    FloatActivePowerDto,
    FloatCurrentDto,
    FloatFrequencyDto,
    FloatInductanceDto,
    FloatResistanceDto,
    FloatVoltageDto,
)
from im_cable_system.engine.shared.dto.itm import (
    ItmImBasicDto,
    ItmImCircuitDto,
    ItmImExcitationDto,
    ItmImModelDto,
    ItmImPrimaryDto,
    ItmImSecondaryDto,
    ItmImTotalDto,
    ItmImVoltageCurrentDto,
)

_SINGLE = ImSecondaryCageBranchType.SINGLE
_INNER = ImSecondaryCageBranchType.INNER
_OUTER = ImSecondaryCageBranchType.OUTER


class _DummyLogger:
    def info(self, _msg: str, *_args: object) -> None:
        pass

    def warning(self, _msg: str, *_args: object) -> None:
        pass

    def error(self, _msg: str, *_args: object) -> None:
        pass


class _DummyConfig:
    class _NumericalGuardConfig:
        eps: float = 1.0e-9

    numerical_guard_config = _NumericalGuardConfig()


def _v(value: complex) -> ArrayComplexVoltageDto:
    return ArrayComplexVoltageDto(value=np.array([value]), unit="V")


def _i(value: complex) -> ArrayComplexCurrentDto:
    return ArrayComplexCurrentDto(value=np.array([value]), unit="A")


def _impedance() -> ArrayComplexImpedanceDto:
    return ArrayComplexImpedanceDto(value=np.array([1.0 + 1.0j]), unit="Ω")


def _admittance() -> ArrayComplexAdmittanceDto:
    return ArrayComplexAdmittanceDto(value=np.array([0.5 - 0.5j]), unit="S")


def _build_im_model(
    *,
    cage_multiplicity: ImCageMultiplicityType,
    friction_windage_model: ImFrictionWindageModelDto,
    stray_load_model: ImStrayLoadModelDto,
    nameplate_power: float = 1000.0,
    nameplate_current: float = 10.0,
) -> ItmImModelDto:
    resistance = FloatResistanceDto(1.0, "Ω")
    inductance = FloatInductanceDto(1.0, "H")
    impedance = _impedance()
    admittance = _admittance()

    if cage_multiplicity == ImCageMultiplicityType.SINGLE_CAGE:
        branches = (_SINGLE,)
    else:
        branches = (_INNER, _OUTER)

    secondary_model = ItmImSecondaryDto(
        cage_multiplicity=cage_multiplicity,
        resistances=dict.fromkeys(branches, resistance),
        inductances=dict.fromkeys(branches, inductance),
        models={
            b: ImSecondaryModelDto(name=ImSecondaryModelType.BASIC)
            for b in branches
        },
        impedances=dict.fromkeys(branches, impedance),
        admittances=dict.fromkeys(branches, admittance),
        base_impedances=dict.fromkeys(branches, impedance),
        base_admittances=dict.fromkeys(branches, admittance),
        load_impedances=dict.fromkeys(branches, impedance),
        load_admittances=dict.fromkeys(branches, admittance),
    )
    return ItmImModelDto(
        name=ImName(value="SINGLE"),
        basic_info=ItmImBasicDto(
            series_name=ImSeriesName.create("TEST_IM"),
            poles=ImPoles.P4,
            nameplate_voltage=FloatVoltageDto(200.0, "V"),
            nameplate_current=FloatCurrentDto(nameplate_current, "A"),
            nameplate_power=FloatActivePowerDto(nameplate_power, "W"),
            nameplate_frequency=FloatFrequencyDto(50.0, "Hz"),
        ),
        circuit_info=ItmImCircuitDto(
            connection_type=ImConnectionType.STAR,
            circuit_type=ImCircuitType.T,
        ),
        primary_model=ItmImPrimaryDto(
            model=ImPrimaryModelDto(name=ImPrimaryModelType.BASIC),
            resistance=resistance,
            inductance=inductance,
            impedance=impedance,
            admittance=admittance,
        ),
        excitation_model=ItmImExcitationDto(
            model=ImExcitationModelDto(name=ImExcitationModelType.BASIC),
            resistance=resistance,
            inductance=inductance,
            impedance=impedance,
            admittance=admittance,
        ),
        secondary_model=secondary_model,
        total_model=ItmImTotalDto(impedance=impedance, admittance=admittance),
        friction_windage_model=friction_windage_model,
        stray_load_model=stray_load_model,
    )


def _build_single_cage_voltage_current() -> ItmImVoltageCurrentDto:
    return ItmImVoltageCurrentDto(
        im_input_voltage=_v(100.0),
        im_input_current=_i(5.0),
        im_primary_voltage=_v(2.0),
        im_primary_current=_i(5.0),
        im_excitation_voltage=_v(1.0),
        im_excitation_current=_i(1.0),
        cage_multiplicity=ImCageMultiplicityType.SINGLE_CAGE,
        secondary_base_voltage={_SINGLE: _v(1.0)},
        secondary_load_voltage={_SINGLE: _v(10.0)},
        secondary_branch_current={_SINGLE: _i(5.0)},
    )


def _build_double_cage_voltage_current() -> ItmImVoltageCurrentDto:
    return ItmImVoltageCurrentDto(
        im_input_voltage=_v(100.0),
        im_input_current=_i(8.0),
        im_primary_voltage=_v(2.0),
        im_primary_current=_i(8.0),
        im_excitation_voltage=_v(1.0),
        im_excitation_current=_i(1.0),
        cage_multiplicity=ImCageMultiplicityType.DOUBLE_CAGE,
        # 枝電圧の合計（base+load）は INNER/OUTER で一致させる必要がある
        # （get_secondary_voltage() の物理制約）。
        secondary_base_voltage={_INNER: _v(1.0), _OUTER: _v(2.0)},
        secondary_load_voltage={_INNER: _v(10.0), _OUTER: _v(9.0)},
        secondary_branch_current={_INNER: _i(3.0), _OUTER: _i(2.0)},
    )


_NONE_FW = ImFrictionWindageModelDto(name=ImFrictionWindageModelType.NONE)
_NONE_STRAY = ImStrayLoadModelDto(name=ImStrayLoadModelType.NONE)
_CONST_FW = ImFrictionWindageModelDto(
    name=ImFrictionWindageModelType.CONSTANT_V1,
    params=FloatParamDtos(
        objects=[FloatParamDto(name="k_friction_windage", value=0.02)]
    ),
)
_QUADRATIC_STRAY = ImStrayLoadModelDto(
    name=ImStrayLoadModelType.CURRENT_DEPENDENT_QUADRATIC_V1,
    params=FloatParamDtos(
        objects=[FloatParamDto(name="k_stray_load", value=0.01)]
    ),
)


class TestSingleCageImPowerCalculatorShaftOutputDeduction:
    """単一かご: NONE/NONE 回帰・片側有効・両側有効の 4 パターン。"""

    def _calculate(
        self,
        friction_windage_model: ImFrictionWindageModelDto,
        stray_load_model: ImStrayLoadModelDto,
    ) -> tuple[complex, complex, complex, complex, complex]:
        calculator = SingleCageImPowerCalculator.create(
            config=_DummyConfig(),  # type: ignore[arg-type]
            logger=_DummyLogger(),  # type: ignore[arg-type]
        )
        im_model = _build_im_model(
            cage_multiplicity=ImCageMultiplicityType.SINGLE_CAGE,
            friction_windage_model=friction_windage_model,
            stray_load_model=stray_load_model,
        )
        power = calculator.calculate(
            im_model=im_model,
            im_voltage_current=_build_single_cage_voltage_current(),
        )
        secondary_load = power.secondary_load_power[_SINGLE].get_value()[0]
        return (
            power.output_power.get_value()[0],
            power.total_loss_power.get_value()[0],
            power.friction_windage_loss_power.get_value()[0],
            power.stray_load_loss_power.get_value()[0],
            secondary_load,  # type: ignore[return-value]
        )

    def test_both_none_matches_existing_formula(self) -> None:
        (output, total_loss, fw, stray, secondary_load) = self._calculate(
            _NONE_FW, _NONE_STRAY
        )
        # 既存式どおり、軸出力は二次負荷支路電力の合計と一致するはず。
        assert output == secondary_load
        assert fw == 0.0 + 0.0j
        assert stray == 0.0 + 0.0j

    def test_friction_windage_only(self) -> None:
        (output, total_loss, fw, stray, secondary_load) = self._calculate(
            _CONST_FW, _NONE_STRAY
        )
        # P_FW = 0.02 * 1000 = 20
        assert fw == pytest.approx(20.0 + 0.0j)
        assert stray == 0.0 + 0.0j
        assert output == pytest.approx(secondary_load - fw)

    def test_stray_load_only(self) -> None:
        (output, total_loss, fw, stray, secondary_load) = self._calculate(
            _NONE_FW, _QUADRATIC_STRAY
        )
        # I2 = 5A, I_N = 10A -> r=0.5, P_stray = 0.01*1000*0.25 = 2.5
        assert stray == pytest.approx(2.5 + 0.0j)
        assert fw == 0.0 + 0.0j
        assert output == pytest.approx(secondary_load - stray)

    def test_both_enabled(self) -> None:
        (output, total_loss, fw, stray, secondary_load) = self._calculate(
            _CONST_FW, _QUADRATIC_STRAY
        )
        assert output == pytest.approx(secondary_load - fw - stray)
        assert np.imag(output) == pytest.approx(np.imag(secondary_load))
        assert np.imag(total_loss) == pytest.approx(np.imag(secondary_load) * 0)


class TestDoubleCageImPowerCalculatorShaftOutputDeduction:
    """二重かご: NONE/NONE 回帰と両側有効。"""

    def _calculate(
        self,
        friction_windage_model: ImFrictionWindageModelDto,
        stray_load_model: ImStrayLoadModelDto,
    ) -> tuple[complex, complex, complex, complex, complex]:
        calculator = DoubleCageImPowerCalculator.create(
            config=_DummyConfig(),  # type: ignore[arg-type]
            logger=_DummyLogger(),  # type: ignore[arg-type]
        )
        im_model = _build_im_model(
            cage_multiplicity=ImCageMultiplicityType.DOUBLE_CAGE,
            friction_windage_model=friction_windage_model,
            stray_load_model=stray_load_model,
        )
        power = calculator.calculate(
            im_model=im_model,
            im_voltage_current=_build_double_cage_voltage_current(),
        )
        secondary_load_total = (
            power.secondary_load_power[_INNER].get_value()[0]
            + power.secondary_load_power[_OUTER].get_value()[0]
        )
        return (
            power.output_power.get_value()[0],
            power.total_loss_power.get_value()[0],
            power.friction_windage_loss_power.get_value()[0],
            power.stray_load_loss_power.get_value()[0],
            secondary_load_total,  # type: ignore[return-value]
        )

    def test_both_none_matches_existing_formula(self) -> None:
        (output, total_loss, fw, stray, secondary_load_total) = self._calculate(
            _NONE_FW, _NONE_STRAY
        )
        assert output == secondary_load_total
        assert fw == 0.0 + 0.0j
        assert stray == 0.0 + 0.0j

    def test_both_enabled(self) -> None:
        (output, total_loss, fw, stray, secondary_load_total) = self._calculate(
            _CONST_FW, _QUADRATIC_STRAY
        )
        assert output == pytest.approx(secondary_load_total - fw - stray)
        assert fw == pytest.approx(20.0 + 0.0j)
        # I2_total = 3 + 2 = 5A, I_N = 10A -> r=0.5, P_stray = 2.5
        assert stray == pytest.approx(2.5 + 0.0j)
