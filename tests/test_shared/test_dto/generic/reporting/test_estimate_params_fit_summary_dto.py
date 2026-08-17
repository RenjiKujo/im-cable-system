"""``EstimateParamsFitSummaryDto`` データ保持テスト。"""

from __future__ import annotations

from im_cable_system.engine.shared.dto.generic.reporting import (
    EstimateParamsFitSummaryDto,
    FitChannelMetricDto,
    FittedModelLabelsDto,
    FittedParameterReportDto,
    OptimizerResultDto,
    OptimizerSettingsDto,
    ResidualObjectiveSettingsDto,
)


class TestEstimateParamsFitSummaryDto:
    def test_minimal_construction(self) -> None:
        summary = EstimateParamsFitSummaryDto(
            model_labels=FittedModelLabelsDto(
                im_primary="BASIC",
                im_excitation="BASIC",
                im_secondary_inner=None,
                im_secondary_outer="BASIC",
                im_friction_windage="NONE",
                im_stray_load="NONE",
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
                n_valid=5, rmse=0.1, std_delta=0.05, unit="A"
            ),
            output_power=FitChannelMetricDto(
                n_valid=5, rmse=10.0, std_delta=5.0, unit="W"
            ),
            power_factor=FitChannelMetricDto(
                n_valid=5, rmse=0.01, std_delta=0.005, unit="-"
            ),
            im_efficiency=FitChannelMetricDto(
                n_valid=5, rmse=0.02, std_delta=0.01, unit="-"
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
        assert summary.optimizer_result.success is True
        assert summary.optimizer_result.nfev == 10
        assert summary.fitted_parameters[0].path == "im.primary_resistance"
        assert summary.fitted_parameters[0].fitted_value == 0.4
        assert summary.model_labels.im_primary == "BASIC"
        assert summary.model_labels.im_secondary_inner is None
        assert summary.model_labels.cable_conductor is None
        assert summary.line_current.unit == "A"
        assert (
            summary.residual_objective_settings.normalize_by_point_count
            is False
        )
