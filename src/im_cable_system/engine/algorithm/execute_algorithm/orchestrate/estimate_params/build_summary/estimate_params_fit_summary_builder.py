"""フィット要約ビルダーの実装。

最適化器の生結果・実行条件と、カタログ補間値・シミュレーション予測値の比較指標
（RMSE / Δ標準偏差）を 1 つの :class:`EstimateParamsFitSummaryDto` に集約する。
「どんな条件で最適化したか」「どんな結果か」「どれほど適合したか」を一括取得
できる構造で組み立て、DTO 構築は 1 箇所に統一する。カーブ比較値が得られない
場合は適合指標を 0.0 とする。
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import (  # type: ignore[import-untyped]
    OptimizeResult,
)

from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.build_summary.i_estimate_params_fit_summary_builder import (  # noqa: E501
    IEstimateParamsFitSummaryBuilder,
)
from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.support.curve_eval import (  # noqa: E501
    extract_curve_fit_comparison_data,
)
from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.support.descriptor import (  # noqa: E501
    FittableParamDescriptor,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ImCageMultiplicityType,
    ImPerformanceCurveCatalogDtos,
    ImSecondaryCageBranchType,
    ImSecondaryModelDto,
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
from im_cable_system.engine.shared.dto.input import (
    InputDto,
)
from im_cable_system.engine.shared.dto.itm import (
    ItmDto,
)

# 本エンジンは残差を評価点数で正規化しない（点数を slip 領域の重みとして扱う）。
# その設計判断を要約に明示するための定数。
_NORMALIZE_BY_POINT_COUNT = False

_LINE_CURRENT_UNIT = "A"
_OUTPUT_POWER_UNIT = "W"
_DIMENSIONLESS_UNIT = "-"


def _secondary_model_labels(
    cage_multiplicity: ImCageMultiplicityType,
    secondary_models: dict[ImSecondaryCageBranchType, ImSecondaryModelDto],
) -> tuple[str | None, str]:
    """二次側の (inner, outer) モデル名ラベルを返す。

    単一かごでは inner ラベルは存在しないため None を返す。

    Args:
        cage_multiplicity: かご多重度（単一 / 二重）。
        secondary_models: 二次枝モデル DTO（ブランチキー → DTO）。

    Returns:
        (inner_label, outer_label)。単一かごのとき inner_label は None。
    """
    if cage_multiplicity == ImCageMultiplicityType.DOUBLE_CAGE:
        inner = secondary_models[ImSecondaryCageBranchType.INNER].get_name()
        outer = secondary_models[ImSecondaryCageBranchType.OUTER].get_name()
        return inner, outer
    outer = secondary_models[ImSecondaryCageBranchType.SINGLE].get_name()
    return None, outer


def _bound_flags(
    value: float,
    lb: float,
    ub: float,
) -> tuple[bool, bool, bool]:
    """(is_fixed, is_at_lower_bound, is_at_upper_bound) を返す。

    ``lb >= ub`` は固定パラメータとみなし、境界張り付き判定は行わない。
    張り付き判定の許容差は探索幅に比例させる。

    Args:
        value: フィット後値。
        lb: 探索下限。
        ub: 探索上限。

    Returns:
        (固定か, 下限張り付きか, 上限張り付きか)。
    """
    span = ub - lb
    if span <= 0.0:
        return True, False, False
    atol = max(1.0e-12, 1.0e-6 * span)
    is_at_lower = abs(value - lb) <= atol
    is_at_upper = abs(value - ub) <= atol
    return False, is_at_lower, is_at_upper


def _rmse_masked(
    target: np.ndarray,
    pred: np.ndarray,
    mask: np.ndarray,
) -> float:
    """mask 上の RMSE を返す。有効点が無ければ 0.0。"""
    ok = np.asarray(mask, dtype=bool) & np.isfinite(target) & np.isfinite(pred)
    if not np.any(ok):
        return 0.0
    diff = np.asarray(pred[ok], dtype=np.float64) - np.asarray(
        target[ok], dtype=np.float64
    )
    return float(np.sqrt(np.mean(diff * diff)))


def _std_delta_masked(
    target: np.ndarray,
    pred: np.ndarray,
    mask: np.ndarray,
) -> float:
    """mask 上の (pred-target) の標準偏差。有効点が 1 以下なら 0.0。"""
    ok = np.asarray(mask, dtype=bool) & np.isfinite(target) & np.isfinite(pred)
    delta = np.asarray(pred[ok], dtype=np.float64) - np.asarray(
        target[ok], dtype=np.float64
    )
    if delta.size <= 1:
        return 0.0
    return float(np.std(delta, ddof=1))


def _channel_metric(
    target: np.ndarray,
    pred: np.ndarray,
    valid: np.ndarray,
    unit: str | None,
) -> FitChannelMetricDto:
    """1 チャネル分の適合指標 DTO を作る。"""
    return FitChannelMetricDto(
        n_valid=int(np.sum(valid)),
        rmse=_rmse_masked(target, pred, valid),
        std_delta=_std_delta_masked(target, pred, valid),
        unit=unit,
    )


@dataclass(frozen=True)
class _CurveMetrics:
    """4 チャネルの適合指標と、有効点の和集合数。"""

    n_valid_union: int
    line_current: FitChannelMetricDto
    output_power: FitChannelMetricDto
    power_factor: FitChannelMetricDto
    im_efficiency: FitChannelMetricDto

    @classmethod
    def zeros(cls) -> _CurveMetrics:
        """カーブ比較不能時の既定値（全指標 0・有効点 0）。"""
        return cls(
            n_valid_union=0,
            line_current=FitChannelMetricDto(
                n_valid=0, rmse=0.0, std_delta=0.0, unit=_LINE_CURRENT_UNIT
            ),
            output_power=FitChannelMetricDto(
                n_valid=0, rmse=0.0, std_delta=0.0, unit=_OUTPUT_POWER_UNIT
            ),
            power_factor=FitChannelMetricDto(
                n_valid=0, rmse=0.0, std_delta=0.0, unit=_DIMENSIONLESS_UNIT
            ),
            im_efficiency=FitChannelMetricDto(
                n_valid=0, rmse=0.0, std_delta=0.0, unit=_DIMENSIONLESS_UNIT
            ),
        )


class EstimateParamsFitSummaryBuilder(IEstimateParamsFitSummaryBuilder):
    """estimate_params 要約 DTO を組み立てる実装。"""

    def __init__(self, config: IConfig, logger: ILogger) -> None:
        """インスタンスを初期化する。"""
        self._config: IConfig = config
        self._logger: ILogger = logger

    @classmethod
    def create(
        cls,
        config: IConfig,
        logger: ILogger,
    ) -> IEstimateParamsFitSummaryBuilder:
        """config と logger を受け取り、自身のインスタンスを生成する。"""
        return cls(config=config, logger=logger)

    def build(
        self,
        input_dto: InputDto,
        descriptors: list[FittableParamDescriptor],
        fitted_x: np.ndarray,
        optimize_result: OptimizeResult,
        pc_catalogs: ImPerformanceCurveCatalogDtos,
        itm_done: ItmDto,
    ) -> EstimateParamsFitSummaryDto:
        """要約 DTO を組み立てる。"""
        residual_final = np.asarray(
            optimize_result.fun,
            dtype=np.float64,
        ).ravel()
        n_res = int(residual_final.size)
        overall_rmse = (
            float(np.sqrt(np.mean(residual_final * residual_final)))
            if n_res > 0
            else 0.0
        )

        metrics = self._curve_fit_metrics(pc_catalogs, itm_done)

        return EstimateParamsFitSummaryDto(
            model_labels=self._model_labels(input_dto),
            optimizer_settings=self._optimizer_settings(),
            residual_objective_settings=self._residual_objective_settings(),
            optimizer_result=OptimizerResultDto(
                success=bool(optimize_result.success),
                message=str(optimize_result.message),
                nfev=int(optimize_result.nfev),
                cost=float(optimize_result.cost),
            ),
            overall_rmse_weighted_residual=overall_rmse,
            n_residual_elements=n_res,
            n_valid_curve_points=metrics.n_valid_union,
            line_current=metrics.line_current,
            output_power=metrics.output_power,
            power_factor=metrics.power_factor,
            im_efficiency=metrics.im_efficiency,
            fitted_parameters=self._fitted_parameters(descriptors, fitted_x),
        )

    @staticmethod
    def _model_labels(input_dto: InputDto) -> FittedModelLabelsDto:
        """モデル名ラベル一式を組み立てる。"""
        series = input_dto.im.im_series
        inner_label, outer_label = _secondary_model_labels(
            series.cage_multiplicity,
            series.secondary_models,
        )
        cable_conductor = (
            input_dto.cable.conductor_model.get_name()
            if input_dto.cable is not None
            else None
        )
        return FittedModelLabelsDto(
            im_primary=series.primary_model.get_name(),
            im_excitation=series.excitation_model.get_name(),
            im_secondary_inner=inner_label,
            im_secondary_outer=outer_label,
            im_friction_windage=series.friction_windage_model.get_name(),
            im_stray_load=series.stray_load_model.get_name(),
            cable_conductor=cable_conductor,
        )

    def _optimizer_settings(self) -> OptimizerSettingsDto:
        """config から最適化器の実行条件を組み立てる。"""
        optimizer = self._config.estimate_params_calculation_config.optimizer
        ls_cfg = optimizer.least_squares
        return OptimizerSettingsDto(
            algorithm=optimizer.algorithm.value,
            max_nfev=int(ls_cfg.max_nfev),
            ftol=float(ls_cfg.ftol),
            xtol=float(ls_cfg.xtol),
            gtol=float(ls_cfg.gtol),
        )

    def _residual_objective_settings(self) -> ResidualObjectiveSettingsDto:
        """config から残差（目的関数）の構成条件を組み立てる。"""
        residual = self._config.estimate_params_calculation_config.residual
        weights = residual.weights
        normalization = residual.normalization
        return ResidualObjectiveSettingsDto(
            current_weight=float(weights.current),
            power_weight=float(weights.power),
            power_factor_weight=float(weights.power_factor),
            efficiency_weight=float(weights.efficiency),
            normalization_method=normalization.method.value,
            normalization_statistic=normalization.statistic.value,
            normalization_eps=float(normalization.eps),
            normalize_by_point_count=_NORMALIZE_BY_POINT_COUNT,
        )

    @staticmethod
    def _fitted_parameters(
        descriptors: list[FittableParamDescriptor],
        fitted_x: np.ndarray,
    ) -> tuple[FittedParameterReportDto, ...]:
        """記述子とフィット後値から、パラメータ報告単位の列を組み立てる。"""
        reports: list[FittedParameterReportDto] = []
        for descriptor, raw_value in zip(descriptors, fitted_x, strict=True):
            fitted_value = float(raw_value)
            is_fixed, is_at_lower, is_at_upper = _bound_flags(
                fitted_value,
                descriptor.lb,
                descriptor.ub,
            )
            reports.append(
                FittedParameterReportDto(
                    path=".".join(descriptor.path),
                    initial_value=float(descriptor.current_value),
                    fitted_value=fitted_value,
                    lower_bound=float(descriptor.lb),
                    upper_bound=float(descriptor.ub),
                    unit=descriptor.unit,
                    is_fixed=is_fixed,
                    is_at_lower_bound=is_at_lower,
                    is_at_upper_bound=is_at_upper,
                )
            )
        return tuple(reports)

    def _curve_fit_metrics(
        self,
        pc_catalogs: ImPerformanceCurveCatalogDtos,
        itm_done: ItmDto,
    ) -> _CurveMetrics:
        """カタログ補間値とシミュ予測値から比較指標を算出する。"""
        comparison = extract_curve_fit_comparison_data(pc_catalogs, itm_done)
        if comparison is None:
            return _CurveMetrics.zeros()

        # チャネルごとに独立な観測マスクを使う。n_valid_union は「いずれかの
        # チャネルが観測済みの格子点数」（評価に寄与する点の和集合）。
        any_valid = (
            comparison.valid_i
            | comparison.valid_p
            | comparison.valid_pf
            | comparison.valid_eta
        )
        return _CurveMetrics(
            n_valid_union=int(np.sum(any_valid)),
            line_current=_channel_metric(
                comparison.target_i,
                comparison.pred_i,
                comparison.valid_i,
                _LINE_CURRENT_UNIT,
            ),
            output_power=_channel_metric(
                comparison.target_p,
                comparison.pred_p,
                comparison.valid_p,
                _OUTPUT_POWER_UNIT,
            ),
            power_factor=_channel_metric(
                comparison.target_pf,
                comparison.pred_pf,
                comparison.valid_pf,
                _DIMENSIONLESS_UNIT,
            ),
            im_efficiency=_channel_metric(
                comparison.target_eta,
                comparison.pred_eta,
                comparison.valid_eta,
                _DIMENSIONLESS_UNIT,
            ),
        )
