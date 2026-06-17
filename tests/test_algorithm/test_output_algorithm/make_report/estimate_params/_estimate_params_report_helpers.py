"""estimate_params make_report テスト用ヘルパー。"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import numpy as np

from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ImCageMultiplicityType,
    ImCircuitType,
    ImConnectionType,
    ImDto,
    ImExcitationModelDto,
    ImExcitationModelType,
    ImName,
    ImPoles,
    ImPrimaryModelDto,
    ImPrimaryModelType,
    ImSecondaryCageBranchType,
    ImSecondaryModelDto,
    ImSecondaryModelType,
    ImSeriesDto,
    ImSeriesName,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexCurrentDto,
    ArrayComplexPowerDto,
    ArrayEfficiencyDto,
    ArrayRotationalSpeedDto,
    ArrayTorqueDto,
    FloatActivePowerDto,
    FloatCurrentDto,
    FloatFrequencyDto,
    FloatInductanceDto,
    FloatResistanceDto,
    FloatVoltageDto,
)
from im_cable_system.engine.shared.dto.generic.reporting import (
    EstimateParamsFitSummaryDto,
    FitChannelMetricDto,
    FittedModelLabelsDto,
    FittedParameterReportDto,
    OptimizerResultDto,
    OptimizerSettingsDto,
    ResidualObjectiveSettingsDto,
)


def minimal_fit_summary() -> EstimateParamsFitSummaryDto:
    """最小のフィット要約 DTO を返す。"""
    return EstimateParamsFitSummaryDto(
        model_labels=FittedModelLabelsDto(
            im_primary="BASIC",
            im_excitation="BASIC",
            im_secondary_inner=None,
            im_secondary_outer="BASIC",
            cable_conductor=None,
        ),
        optimizer_settings=OptimizerSettingsDto(
            algorithm="least_squares",
            max_nfev=100,
            ftol=1.0e-8,
            xtol=1.0e-8,
            gtol=1.0e-8,
        ),
        residual_objective_settings=ResidualObjectiveSettingsDto(
            current_weight=1.0,
            power_weight=1.0,
            power_factor_weight=1.0,
            efficiency_weight=1.0,
            normalization_method="by_curve_scale",
            normalization_statistic="std",
            normalization_eps=1.0e-12,
            normalize_by_point_count=False,
        ),
        optimizer_result=OptimizerResultDto(
            success=True,
            message="ok",
            nfev=10,
            cost=0.5,
        ),
        overall_rmse_weighted_residual=0.1,
        n_residual_elements=20,
        n_valid_curve_points=5,
        line_current=FitChannelMetricDto(
            n_valid=5,
            rmse=0.1,
            std_delta=0.05,
            unit="A",
        ),
        output_power=FitChannelMetricDto(
            n_valid=5,
            rmse=10.0,
            std_delta=5.0,
            unit="W",
        ),
        power_factor=FitChannelMetricDto(
            n_valid=5,
            rmse=0.01,
            std_delta=0.005,
            unit="-",
        ),
        im_efficiency=FitChannelMetricDto(
            n_valid=5,
            rmse=0.02,
            std_delta=0.01,
            unit="-",
        ),
        fitted_parameters=(
            FittedParameterReportDto(
                path="im.primary_resistance",
                initial_value=0.5,
                fitted_value=0.4,
                lower_bound=0.1,
                upper_bound=1.0,
                unit="Ω",
                is_fixed=False,
                is_at_lower_bound=False,
                is_at_upper_bound=False,
            ),
        ),
    )


_SINGLE: ImSecondaryCageBranchType = ImSecondaryCageBranchType.SINGLE


def im_dto_stub() -> ImDto:
    """最小 ImDto stub を返す。"""
    secondary_resistance = FloatResistanceDto(value=5.0, unit="Ω")
    secondary_inductance = FloatInductanceDto(value=6.0, unit="H")
    return ImDto(
        name=ImName(value="IM01"),
        im_series=ImSeriesDto(
            name=ImSeriesName(value="SERIES"),
            poles=ImPoles.P4,
            nameplate_voltage=FloatVoltageDto(value=400.0, unit="V"),
            nameplate_current=FloatCurrentDto(value=10.0, unit="A"),
            nameplate_power=FloatActivePowerDto(value=1000.0, unit="W"),
            nameplate_frequency=FloatFrequencyDto(value=60.0, unit="Hz"),
            connection_type=ImConnectionType.STAR,
            circuit_type=ImCircuitType.T,
            primary_model=ImPrimaryModelDto(name=ImPrimaryModelType.BASIC),
            primary_resistance=FloatResistanceDto(value=1.5, unit="Ω"),
            primary_inductance=FloatInductanceDto(value=2.5, unit="H"),
            excitation_model=ImExcitationModelDto(
                name=ImExcitationModelType.BASIC,
            ),
            excitation_resistance=FloatResistanceDto(value=3.0, unit="Ω"),
            excitation_inductance=FloatInductanceDto(value=4.0, unit="H"),
            cage_multiplicity=ImCageMultiplicityType.SINGLE_CAGE,
            secondary_models={
                _SINGLE: ImSecondaryModelDto(name=ImSecondaryModelType.BASIC),
            },
            secondary_resistances={_SINGLE: secondary_resistance},
            secondary_inductances={_SINGLE: secondary_inductance},
        ),
    )


def result_stub() -> Any:
    """最小 result stub を返す。"""
    shape = (2, 1, 1)
    return SimpleNamespace(
        output_power=ArrayComplexPowerDto(
            value=np.full(shape, 100.0 + 0.0j, dtype=np.complex128),
            unit="VA",
        ),
        cable_input_phase_power=ArrayComplexPowerDto(
            value=np.full(shape, 100.0 + 0.0j, dtype=np.complex128),
            unit="VA",
        ),
        input_line_current=ArrayComplexCurrentDto(
            value=np.full(shape, 2.0 + 0.0j, dtype=np.complex128),
            unit="A",
        ),
        system_efficiency=ArrayEfficiencyDto(
            value=np.full(shape, 0.8), unit="-"
        ),
        torque=ArrayTorqueDto(value=np.full(shape, 5.0), unit="Nm"),
        rotational_speed=ArrayRotationalSpeedDto(
            value=np.full(shape, 1800.0),
            unit="rpm",
        ),
    )
