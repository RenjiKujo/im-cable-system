"""新 ``OutputDto``（Input 由来 × Simulation 結果）の構築・属性保持テスト。"""

from __future__ import annotations

import numpy as np

from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ArrayKey,
    ArrayLayoutDto,
    ImCableSystemName,
    ImCageMultiplicityType,
    ImCircuitType,
    ImConnectionType,
    ImDto,
    ImExcitationModelDto,
    ImExcitationModelType,
    ImFrictionWindageModelDto,
    ImFrictionWindageModelType,
    ImName,
    ImPerformanceCurveCatalogDtos,
    ImPoles,
    ImPrimaryModelDto,
    ImPrimaryModelType,
    ImSecondaryCageBranchType,
    ImSecondaryModelDto,
    ImSecondaryModelType,
    ImSeriesDto,
    ImSeriesName,
    ImStrayLoadModelDto,
    ImStrayLoadModelType,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexCurrentDto,
    ArrayComplexPowerDto,
    ArrayComplexVoltageDto,
    ArrayEfficiencyDto,
    ArrayFrequencyDto,
    ArrayRotationalSpeedDto,
    ArraySlipDto,
    ArrayTorqueDto,
    FloatActivePowerDto,
    FloatCurrentDto,
    FloatFrequencyDto,
    FloatInductanceDto,
    FloatResistanceDto,
    FloatVoltageDto,
)
from im_cable_system.engine.shared.dto.generic.reporting import (
    NumericalStabilityReportDto,
)
from im_cable_system.engine.shared.dto.output import (
    OutputDto,
    OutputSimulationResultDto,
)


def _make_im_dto(name: str = "M1") -> ImDto:
    branch = ImSecondaryCageBranchType.SINGLE
    series = ImSeriesDto(
        name=ImSeriesName.create(value=name),
        poles=ImPoles.P4,
        nameplate_voltage=FloatVoltageDto(value=200.0, unit="V"),
        nameplate_current=FloatCurrentDto(value=10.0, unit="A"),
        nameplate_power=FloatActivePowerDto(value=3.0, unit="kW"),
        nameplate_frequency=FloatFrequencyDto(value=50.0, unit="Hz"),
        connection_type=ImConnectionType.STAR,
        circuit_type=ImCircuitType.T,
        primary_model=ImPrimaryModelDto(name=ImPrimaryModelType.BASIC),
        primary_resistance=FloatResistanceDto(value=0.4, unit="Ω"),
        primary_inductance=FloatInductanceDto(value=2.0, unit="mH"),
        excitation_model=ImExcitationModelDto(name=ImExcitationModelType.BASIC),
        excitation_resistance=FloatResistanceDto(value=200.0, unit="Ω"),
        excitation_inductance=FloatInductanceDto(value=60.0, unit="mH"),
        cage_multiplicity=ImCageMultiplicityType.SINGLE_CAGE,
        secondary_models={
            branch: ImSecondaryModelDto(name=ImSecondaryModelType.BASIC),
        },
        secondary_resistances={
            branch: FloatResistanceDto(value=0.3, unit="Ω"),
        },
        secondary_inductances={
            branch: FloatInductanceDto(value=2.0, unit="mH"),
        },
        friction_windage_model=ImFrictionWindageModelDto(
            name=ImFrictionWindageModelType.NONE
        ),
        stray_load_model=ImStrayLoadModelDto(name=ImStrayLoadModelType.NONE),
    )
    return ImDto(name=ImName(value=name), im_series=series)


def _make_slip_grid_layout() -> ArrayLayoutDto:
    return ArrayLayoutDto(
        arrays={
            ArrayKey.SLIP: ArraySlipDto(
                value=np.array([0.0, 0.05, 1.0]),
                unit="-",
            ),
            ArrayKey.FREQUENCY: ArrayFrequencyDto(
                value=np.array([50.0]),
                unit="Hz",
            ),
            ArrayKey.INPUT_LINE_VOLTAGE: ArrayComplexVoltageDto(
                value=np.array([200.0 + 0j]),
                unit="V",
            ),
        },
        reference_axes=[
            ArrayKey.SLIP,
            ArrayKey.FREQUENCY,
            ArrayKey.INPUT_LINE_VOLTAGE,
        ],
    )


def _make_result() -> OutputSimulationResultDto:
    shape = (3, 1, 1)
    return OutputSimulationResultDto(
        output_power=ArrayComplexPowerDto(
            value=np.zeros(shape, dtype=np.complex128),
            unit="VA",
        ),
        cable_input_phase_power=ArrayComplexPowerDto(
            value=np.zeros(shape, dtype=np.complex128),
            unit="VA",
        ),
        input_line_current=ArrayComplexCurrentDto(
            value=np.zeros(shape, dtype=np.complex128),
            unit="A",
        ),
        system_efficiency=ArrayEfficiencyDto(
            value=np.zeros(shape, dtype=np.float64),
            unit="-",
        ),
        torque=ArrayTorqueDto(
            value=np.zeros(shape, dtype=np.float64),
            unit="Nm",
        ),
        rotational_speed=ArrayRotationalSpeedDto(
            value=np.zeros(shape, dtype=np.float64),
            unit="rad/s",
        ),
    )


class TestOutputDto:
    def test_minimal_construction(self) -> None:
        dto = OutputDto(
            name=ImCableSystemName(base="SYS"),
            array_layout=_make_slip_grid_layout(),
            im=_make_im_dto(),
            cable=None,
            result=_make_result(),
        )
        assert dto.name.get_value() == "SYS"
        assert dto.cable is None
        assert dto.estimate_params_fit_summary is None
        assert ArrayKey.SLIP in dto.array_layout.reference_axes

    def test_defaults_optional_fields(self) -> None:
        dto = OutputDto(
            name=ImCableSystemName(base="SYS"),
            array_layout=_make_slip_grid_layout(),
            im=_make_im_dto(),
            cable=None,
            result=_make_result(),
        )
        assert isinstance(dto.im_pc_catalogs, ImPerformanceCurveCatalogDtos)
        assert len(dto.im_pc_catalogs) == 0
        assert dto.numerical_stability_report is None

    def test_holds_numerical_stability_report(self) -> None:
        report = NumericalStabilityReportDto(
            event_counts=(("clamp_zero", 2),),
        )
        dto = OutputDto(
            name=ImCableSystemName(base="SYS"),
            array_layout=_make_slip_grid_layout(),
            im=_make_im_dto(),
            cable=None,
            result=_make_result(),
            numerical_stability_report=report,
        )
        assert dto.numerical_stability_report is report
        assert not dto.numerical_stability_report.is_empty()
