"""OutputDtoConverter（ItmDto → OutputDto 変換）のテスト。

検証観点:
    - ``_resolve_input_im``: 構築済み ``ItmImModelDto`` から入力原値 ``ImDto`` を
      復元できる（銘板・結線/回路種別・一次/励磁/二次の R/L）。
    - ``_resolve_input_cable``: 擬似ケーブル（``name is None``）は ``None``、
      実ケーブルは ``CableDto`` に復元する。
    - ``_build_result``: power / characteristic / voltage_current から出力用生量を
      正しく抽出する。
    - ガード: ``simulation_result`` が None、または power / characteristic を欠く
      （電流電圧のみ計算）場合は ``ValueError``。

本テストは ``build_model`` / ``simulate`` を走らせず、convert が読むフィールドだけを
手組みした ItmDto を入力する。抽出経路を区別できるよう、ルーティング先ごとに
異なる定数値を埋める。
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any, cast

import numpy as np
import pytest

from im_cable_system.engine.algorithm.output_algorithm.convert.output_dto_converter import (  # noqa: E501
    OutputDtoConverter,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ArrayKey,
    ArrayLayoutDto,
    CableConductorModelDto,
    CableName,
    CableSectionName,
    CableSeriesName,
    CableShapeTypeDto,
    ConductorModelType,
    ImCableSystemName,
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
    PieCableConductorKey,
    PieCableGroundKey,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexAdmittanceDto,
    ArrayComplexCurrentDto,
    ArrayComplexImpedanceDto,
    ArrayComplexPowerDto,
    ArrayComplexVoltageDto,
    ArrayEfficiencyDto,
    ArrayRotationalSpeedDto,
    ArraySlipDto,
    ArrayTorqueDto,
    FloatActivePowerDto,
    FloatCapacitancePerLengthDto,
    FloatCurrentDto,
    FloatFrequencyDto,
    FloatInductanceDto,
    FloatInductancePerLengthDto,
    FloatLengthDto,
    FloatResistanceDto,
    FloatResistanceLengthDto,
    FloatResistancePerLengthDto,
    FloatVoltageDto,
)
from im_cable_system.engine.shared.dto.itm import (
    ItmCableBasicDto,
    ItmCableImmittanceDto,
    ItmCableLineDensityDto,
    ItmCableModelDto,
    ItmCablePowerDto,
    ItmCableSectionDto,
    ItmCableSectionDtos,
    ItmCableVoltageCurrentDto,
    ItmCharacteristicDto,
    ItmDto,
    ItmEfficiencyDto,
    ItmImBasicDto,
    ItmImCircuitDto,
    ItmImExcitationDto,
    ItmImModelDto,
    ItmImPowerDto,
    ItmImPrimaryDto,
    ItmImSecondaryDto,
    ItmImTotalDto,
    ItmImVoltageCurrentDto,
    ItmModelDto,
    ItmPowerDto,
    ItmRotationalSpeedDto,
    ItmSimulationDto,
    ItmSystemModelDto,
    ItmTorqueDto,
    ItmVoltageCurrentDto,
)

_N: int = 2
_SINGLE: ImSecondaryCageBranchType = ImSecondaryCageBranchType.SINGLE
_SINGLE_CAGE: ImCageMultiplicityType = ImCageMultiplicityType.SINGLE_CAGE

# 抽出経路ごとに区別できるルーティング先の定数。
_OUTPUT_POWER: complex = 10.0 + 2.0j
_CABLE_INPUT_PHASE_POWER: complex = 13.0 + 3.0j
_INPUT_LINE_CURRENT: complex = 7.0 + 1.0j
_SYSTEM_EFFICIENCY: float = 0.9
_TORQUE: float = 5.0
_ROTATIONAL_SPEED: float = 150.0

# IM 復元の照合用定数。
_PRIMARY_RESISTANCE: float = 1.5
_PRIMARY_INDUCTANCE: float = 2.5
_NAMEPLATE_VOLTAGE: float = 200.0
_NAMEPLATE_CURRENT: float = 10.0


def _power(value: complex) -> ArrayComplexPowerDto:
    return ArrayComplexPowerDto(
        value=np.full(_N, value, dtype=np.complex128),
        unit="VA",
    )


def _voltage(value: complex) -> ArrayComplexVoltageDto:
    return ArrayComplexVoltageDto(
        value=np.full(_N, value, dtype=np.complex128),
        unit="V",
    )


def _current(value: complex) -> ArrayComplexCurrentDto:
    return ArrayComplexCurrentDto(
        value=np.full(_N, value, dtype=np.complex128),
        unit="A",
    )


def _impedance() -> ArrayComplexImpedanceDto:
    return ArrayComplexImpedanceDto(
        value=np.full(_N, 1.0 + 1.0j, dtype=np.complex128),
        unit="Ω",
    )


def _admittance() -> ArrayComplexAdmittanceDto:
    return ArrayComplexAdmittanceDto(
        value=np.full(_N, 0.5 - 0.5j, dtype=np.complex128),
        unit="S",
    )


def _build_im_model() -> ItmImModelDto:
    """単一かごの IM モデル DTO を生成する（復元照合用の値を埋める）。"""
    basic_info = ItmImBasicDto(
        series_name=ImSeriesName.create("TEST_IM"),
        poles=ImPoles.P4,
        nameplate_voltage=FloatVoltageDto(value=_NAMEPLATE_VOLTAGE, unit="V"),
        nameplate_current=FloatCurrentDto(value=_NAMEPLATE_CURRENT, unit="A"),
        nameplate_power=FloatActivePowerDto(value=1000.0, unit="W"),
        nameplate_frequency=FloatFrequencyDto(value=50.0, unit="Hz"),
    )
    circuit_info = ItmImCircuitDto(
        connection_type=ImConnectionType.STAR,
        circuit_type=ImCircuitType.T,
    )
    impedance = _impedance()
    admittance = _admittance()
    inductance = FloatInductanceDto(value=_PRIMARY_INDUCTANCE, unit="H")
    primary_model = ItmImPrimaryDto(
        model=ImPrimaryModelDto(name=ImPrimaryModelType.BASIC),
        resistance=FloatResistanceDto(value=_PRIMARY_RESISTANCE, unit="Ω"),
        inductance=inductance,
        impedance=impedance,
        admittance=admittance,
    )
    excitation_model = ItmImExcitationDto(
        model=ImExcitationModelDto(name=ImExcitationModelType.BASIC),
        resistance=FloatResistanceDto(value=3.0, unit="Ω"),
        inductance=FloatInductanceDto(value=4.0, unit="H"),
        impedance=impedance,
        admittance=admittance,
    )
    secondary_resistance = FloatResistanceDto(value=5.0, unit="Ω")
    secondary_inductance = FloatInductanceDto(value=6.0, unit="H")
    secondary_model = ItmImSecondaryDto(
        cage_multiplicity=_SINGLE_CAGE,
        resistances={_SINGLE: secondary_resistance},
        inductances={_SINGLE: secondary_inductance},
        models={_SINGLE: ImSecondaryModelDto(name=ImSecondaryModelType.BASIC)},
        impedances={_SINGLE: impedance},
        admittances={_SINGLE: admittance},
        base_impedances={_SINGLE: impedance},
        base_admittances={_SINGLE: admittance},
        load_impedances={_SINGLE: impedance},
        load_admittances={_SINGLE: admittance},
    )
    total_model = ItmImTotalDto(impedance=impedance, admittance=admittance)
    return ItmImModelDto(
        name=ImName(value="SINGLE"),
        basic_info=basic_info,
        circuit_info=circuit_info,
        primary_model=primary_model,
        excitation_model=excitation_model,
        secondary_model=secondary_model,
        total_model=total_model,
        friction_windage_model=ImFrictionWindageModelDto(
            name=ImFrictionWindageModelType.NONE
        ),
        stray_load_model=ImStrayLoadModelDto(name=ImStrayLoadModelType.NONE),
    )


def _build_cable_immittance() -> ItmCableImmittanceDto:
    impedance = _impedance()
    admittance = _admittance()
    return ItmCableImmittanceDto(
        conductor_model=CableConductorModelDto(name=ConductorModelType.BASIC),
        conductor_impedance={PieCableConductorKey.SINGLE: impedance},
        conductor_admittance={PieCableConductorKey.SINGLE: admittance},
        ground_impedance={
            PieCableGroundKey.UPSTREAM: impedance,
            PieCableGroundKey.DOWNSTREAM: impedance,
        },
        ground_admittance={
            PieCableGroundKey.UPSTREAM: admittance,
            PieCableGroundKey.DOWNSTREAM: admittance,
        },
        is_ground_insulated=False,
        is_ground_shorted=False,
        is_conductor_ideal=False,
    )


def _build_pseudo_cable_model() -> ItmCableModelDto:
    """擬似ケーブル（cable=None 入力相当、name/cable_info が None）。"""
    return ItmCableModelDto(
        name=None,
        cable_info=None,
        cable_immittance=_build_cable_immittance(),
    )


def _build_real_cable_model() -> ItmCableModelDto:
    """実ケーブル（1 セクション）のモデル DTO を生成する。"""
    basic_info = ItmCableBasicDto(
        name=CableSectionName(value="MAIN"),
        series_name=CableSeriesName(value="MAIN_REAL"),
        shape_type=CableShapeTypeDto(value="ROUND"),
        length=FloatLengthDto(value=100.0, unit="m"),
    )
    line_density_info = ItmCableLineDensityDto(
        conductor_resistance_per_length=FloatResistancePerLengthDto(
            value=0.01,
            unit="Ω/m",
        ),
        conductor_inductance_per_length=FloatInductancePerLengthDto(
            value=1e-6,
            unit="H/m",
        ),
        ground_resistance_length=FloatResistanceLengthDto(
            value=1e6,
            unit="Ω*m",
        ),
        ground_capacitance_per_length=FloatCapacitancePerLengthDto(
            value=1e-9,
            unit="F/m",
        ),
    )
    section = ItmCableSectionDto(
        basic_info=basic_info,
        line_density_info=line_density_info,
    )
    return ItmCableModelDto(
        name=CableName(value="SINGLE"),
        cable_info=ItmCableSectionDtos(objects=[section]),
        cable_immittance=_build_cable_immittance(),
    )


def _build_array_layout() -> ArrayLayoutDto:
    slip = ArraySlipDto(value=np.array([0.1, 0.5]), unit="-")
    return ArrayLayoutDto(
        arrays={ArrayKey.SLIP: slip},
        reference_axes=[ArrayKey.SLIP],
    )


def _build_power() -> ItmPowerDto:
    branch_power = _power(1.0 + 0.0j)
    im_power = ItmImPowerDto(
        input_power=_power(20.0 + 5.0j),
        primary_loss_power=_power(0.5 + 0.0j),
        excitation_loss_power=_power(0.5 + 0.0j),
        cage_multiplicity=_SINGLE_CAGE,
        secondary_base_loss_power={_SINGLE: branch_power},
        secondary_load_power={_SINGLE: branch_power},
        secondary_branch_total_power={_SINGLE: branch_power},
        secondary_total_power=_power(1.0 + 0.0j),
        friction_windage_loss_power=_power(0.0 + 0.0j),
        stray_load_loss_power=_power(0.0 + 0.0j),
        output_power=_power(_OUTPUT_POWER),
        total_loss_power=_power(2.0 + 0.5j),
        copper_loss_power=_power(1.0 + 0.0j),
        iron_loss_power=_power(1.0 + 0.0j),
    )
    cable_power = ItmCablePowerDto(
        system_total_input_power=_power(20.0 + 5.0j),
        input_phase_power=_power(_CABLE_INPUT_PHASE_POWER),
        conductor_loss_power={PieCableConductorKey.SINGLE: _power(0.5 + 0.0j)},
        ground_loss_power={
            PieCableGroundKey.UPSTREAM: _power(0.25 + 0.0j),
            PieCableGroundKey.DOWNSTREAM: _power(0.25 + 0.0j),
        },
        end_point_phase_power=_power(11.0 + 2.0j),
        total_loss_power=_power(1.0 + 0.5j),
    )
    return ItmPowerDto(im_power=im_power, cable_power=cable_power)


def _build_characteristic() -> ItmCharacteristicDto:
    efficiency = _N * [_SYSTEM_EFFICIENCY]
    return ItmCharacteristicDto(
        rotational_speed=ItmRotationalSpeedDto(
            rotational_speed=ArrayRotationalSpeedDto(
                value=np.full(_N, _ROTATIONAL_SPEED, dtype=np.float64),
                unit="rad/s",
            ),
        ),
        torque=ItmTorqueDto(
            torque=ArrayTorqueDto(
                value=np.full(_N, _TORQUE, dtype=np.float64),
                unit="Nm",
            ),
        ),
        efficiency=ItmEfficiencyDto(
            system_efficiency=ArrayEfficiencyDto(
                value=np.array(efficiency, dtype=np.float64),
                unit="-",
            ),
            im_efficiency=ArrayEfficiencyDto(
                value=np.full(_N, 0.95, dtype=np.float64),
                unit="-",
            ),
            cable_efficiency=ArrayEfficiencyDto(
                value=np.full(_N, 0.95, dtype=np.float64),
                unit="-",
            ),
        ),
    )


def _build_voltage_current() -> ItmVoltageCurrentDto:
    voltage = _voltage(100.0 + 0.0j)
    current = _current(5.0 + 0.0j)
    im_vc = ItmImVoltageCurrentDto(
        im_input_voltage=voltage,
        im_input_current=current,
        im_primary_voltage=voltage,
        im_primary_current=current,
        im_excitation_voltage=voltage,
        im_excitation_current=current,
        cage_multiplicity=_SINGLE_CAGE,
        secondary_base_voltage={_SINGLE: voltage},
        secondary_load_voltage={_SINGLE: voltage},
        secondary_branch_current={_SINGLE: current},
    )
    cable_vc = ItmCableVoltageCurrentDto(
        input_line_voltage=voltage,
        input_line_current=_current(_INPUT_LINE_CURRENT),
        input_phase_voltage=voltage,
        input_phase_current=current,
        conductor_voltage={PieCableConductorKey.SINGLE: voltage},
        conductor_current={PieCableConductorKey.SINGLE: current},
        ground_voltage={
            PieCableGroundKey.UPSTREAM: voltage,
            PieCableGroundKey.DOWNSTREAM: voltage,
        },
        ground_current={
            PieCableGroundKey.UPSTREAM: current,
            PieCableGroundKey.DOWNSTREAM: current,
        },
        end_point_phase_voltage=voltage,
        end_point_phase_current=current,
    )
    return ItmVoltageCurrentDto(
        im_voltage_current=im_vc,
        cable_voltage_current=cable_vc,
    )


def _build_simulation(
    *,
    with_power: bool = True,
    with_characteristic: bool = True,
) -> ItmSimulationDto:
    return ItmSimulationDto(
        voltage_current=_build_voltage_current(),
        power=_build_power() if with_power else None,
        characteristic=(
            _build_characteristic() if with_characteristic else None
        ),
    )


def _build_itm(
    *,
    cable_model: ItmCableModelDto | None = None,
    simulation: ItmSimulationDto | None = None,
    discriminator: str | None = None,
) -> ItmDto:
    model = ItmModelDto(
        array_layout=_build_array_layout(),
        im=_build_im_model(),
        cable=cable_model
        if cable_model is not None
        else (_build_pseudo_cable_model()),
        system=ItmSystemModelDto(
            system_phase_impedance=_impedance(),
            system_phase_admittance=_admittance(),
        ),
    )
    return ItmDto(
        name=ImCableSystemName(base="test_system", discriminator=discriminator),
        model=model,
        simulation_result=(
            simulation if simulation is not None else _build_simulation()
        ),
    )


def _converter() -> OutputDtoConverter:
    return OutputDtoConverter(
        config=cast(IConfig, object()),
        logger=cast(ILogger, object()),
    )


class TestResolveInputIm:
    def test_reconstructs_nameplate_and_circuit(self) -> None:
        output_dto = _converter().convert(_build_itm())
        im_series = output_dto.im.im_series
        assert im_series.poles == ImPoles.P4
        assert im_series.connection_type == ImConnectionType.STAR
        assert im_series.circuit_type == ImCircuitType.T
        assert im_series.nameplate_voltage.get_value() == _NAMEPLATE_VOLTAGE
        assert im_series.nameplate_current.get_value() == _NAMEPLATE_CURRENT

    def test_reconstructs_branch_parameters(self) -> None:
        output_dto = _converter().convert(_build_itm())
        im_series = output_dto.im.im_series
        assert im_series.primary_resistance.get_value() == _PRIMARY_RESISTANCE
        assert im_series.primary_inductance.get_value() == _PRIMARY_INDUCTANCE
        assert im_series.cage_multiplicity == _SINGLE_CAGE
        assert set(im_series.secondary_resistances.keys()) == {_SINGLE}


class TestResolveInputCable:
    def test_pseudo_cable_returns_none(self) -> None:
        output_dto = _converter().convert(_build_itm())
        assert output_dto.cable is None

    def test_real_cable_reconstructed(self) -> None:
        itm = _build_itm(cable_model=_build_real_cable_model())
        output_dto = _converter().convert(itm)
        cable = output_dto.cable
        assert cable is not None
        assert cable.name.get_value() == "SINGLE"
        sections = cable.sections.get_all()
        assert len(sections) == 1
        assert sections[0].name.get_value() == "MAIN"
        assert sections[0].series.name.get_value() == "MAIN_REAL"


class TestBuildResult:
    def test_extracts_simulation_quantities(self) -> None:
        output_dto = _converter().convert(_build_itm())
        result = output_dto.result
        assert result.output_power.get_value()[0] == _OUTPUT_POWER
        assert (
            result.cable_input_phase_power.get_value()[0]
            == _CABLE_INPUT_PHASE_POWER
        )
        assert result.input_line_current.get_value()[0] == _INPUT_LINE_CURRENT
        assert result.system_efficiency.get_value()[0] == _SYSTEM_EFFICIENCY
        assert result.torque.get_value()[0] == _TORQUE
        # 回転数のみ rpm へ換算される（入力は rad/s）。
        expected_rpm = _ROTATIONAL_SPEED * 60.0 / (2.0 * np.pi)
        assert result.rotational_speed.get_value()[0] == pytest.approx(
            expected_rpm
        )
        assert result.rotational_speed.get_unit() == "rpm"

    def test_raises_when_simulation_result_none(self) -> None:
        itm = _build_itm()
        itm_no_sim: Any = replace(itm, simulation_result=None)
        with pytest.raises(ValueError, match="simulation_result"):
            _converter().convert(itm_no_sim)

    def test_raises_when_power_missing(self) -> None:
        itm = _build_itm(simulation=_build_simulation(with_power=False))
        with pytest.raises(ValueError, match="完全計算済み"):
            _converter().convert(itm)

    def test_raises_when_characteristic_missing(self) -> None:
        itm = _build_itm(
            simulation=_build_simulation(with_characteristic=False),
        )
        with pytest.raises(ValueError, match="完全計算済み"):
            _converter().convert(itm)


class TestPassThrough:
    def test_name_layout_and_reports(self) -> None:
        output_dto = _converter().convert(_build_itm())
        assert output_dto.name.get_value() == "test_system"
        assert output_dto.array_layout.reference_axes == [ArrayKey.SLIP]
        assert output_dto.numerical_stability_report is None
        assert output_dto.estimate_params_fit_summary is None

    def test_name_is_carried_through_from_itm_dto(self) -> None:
        """``name``（``base`` / ``discriminator`` とも）は ``ItmDto.name`` をそのまま引き継ぐ。"""
        output_dto = _converter().convert(
            _build_itm(discriminator="1_1_1_0_0_1_1_0")
        )
        assert output_dto.name.get_base() == "test_system"
        assert output_dto.name.get_value() == "test_system_1_1_1_0_0_1_1_0"
        assert output_dto.name.get_value() != output_dto.name.get_base()
