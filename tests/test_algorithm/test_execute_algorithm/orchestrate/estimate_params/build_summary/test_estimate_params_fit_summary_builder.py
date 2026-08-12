"""EstimateParamsFitSummaryBuilder の単体テスト。"""

from __future__ import annotations

from types import SimpleNamespace
from typing import cast

import numpy as np
import pytest
from scipy.optimize import OptimizeResult  # type: ignore[import-untyped]

import im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.build_summary.estimate_params_fit_summary_builder as builder_module  # noqa: E501
from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.build_summary import (  # noqa: E501
    EstimateParamsFitSummaryBuilder,
    IEstimateParamsFitSummaryBuilder,
)
from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.build_summary.estimate_params_fit_summary_builder import (  # noqa: E501, PLC2701
    _bound_flags,
    _channel_metric,
    _CurveMetrics,
    _rmse_masked,
    _secondary_model_labels,
    _std_delta_masked,
)
from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.support.curve_eval import (  # noqa: E501
    CurveFitComparisonData,
)
from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.support.descriptor import (  # noqa: E501
    FittableParamDescriptor,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ImCageMultiplicityType,
    ImSecondaryCageBranchType,
    ImSecondaryModelDto,
    ImSecondaryModelType,
)
from im_cable_system.engine.shared.dto.input import InputDtos
from im_cable_system.engine.shared.dto.itm import ItmDto


class TestEstimateParamsFitSummaryBuilder:
    """要約ビルダーの生成を確認する。"""

    def test_create_returns_interface(
        self,
        config: IConfig,
        logger: ILogger,
    ) -> None:
        """create がインターフェース型を返す。"""
        builder = EstimateParamsFitSummaryBuilder.create(
            config=config,
            logger=logger,
        )
        assert isinstance(builder, IEstimateParamsFitSummaryBuilder)


class TestSecondaryModelLabels:
    """二次側モデルラベル抽出ヘルパーの単体テスト。"""

    def test_single_cage_returns_none_inner(self) -> None:
        """単一かごは inner=None・outer=単一枝のモデル名を返す。"""
        secondary_models = {
            ImSecondaryCageBranchType.SINGLE: ImSecondaryModelDto(
                name=ImSecondaryModelType.BASIC,
            ),
        }
        inner, outer = _secondary_model_labels(
            ImCageMultiplicityType.SINGLE_CAGE,
            secondary_models,
        )
        assert inner is None
        assert outer == "BASIC"

    def test_double_cage_returns_inner_and_outer(self) -> None:
        """二重かごは inner / outer 両方のモデル名を返す。"""
        secondary_models = {
            ImSecondaryCageBranchType.INNER: ImSecondaryModelDto(
                name=ImSecondaryModelType.BASIC,
            ),
            ImSecondaryCageBranchType.OUTER: ImSecondaryModelDto(
                name=ImSecondaryModelType.BASIC,
            ),
        }
        inner, outer = _secondary_model_labels(
            ImCageMultiplicityType.DOUBLE_CAGE,
            secondary_models,
        )
        assert inner == "BASIC"
        assert outer == "BASIC"


class TestBoundFlags:
    """``_bound_flags`` の固定・境界張り付き判定。"""

    def test_fixed_when_lb_ge_ub(self) -> None:
        """lb >= ub は固定とみなし、張り付き判定はしない。"""
        is_fixed, at_lower, at_upper = _bound_flags(1.0, 1.0, 1.0)
        assert is_fixed is True
        assert at_lower is False
        assert at_upper is False

    def test_at_lower_bound(self) -> None:
        """下限ちょうどは下限張り付き。"""
        is_fixed, at_lower, at_upper = _bound_flags(0.0, 0.0, 10.0)
        assert is_fixed is False
        assert at_lower is True
        assert at_upper is False

    def test_at_upper_bound(self) -> None:
        """上限ちょうどは上限張り付き。"""
        is_fixed, at_lower, at_upper = _bound_flags(10.0, 0.0, 10.0)
        assert is_fixed is False
        assert at_lower is False
        assert at_upper is True

    def test_interior_value_not_at_bounds(self) -> None:
        """内点はどちらにも張り付かない。"""
        is_fixed, at_lower, at_upper = _bound_flags(5.0, 0.0, 10.0)
        assert (is_fixed, at_lower, at_upper) == (False, False, False)


class TestRmseAndStdDeltaMasked:
    """``_rmse_masked`` / ``_std_delta_masked`` の mask 適用。"""

    def test_rmse_only_on_masked_points(self) -> None:
        """mask False と非有限は RMSE 計算から除外する。"""
        target = np.array([1.0, 2.0, np.nan, 4.0], dtype=np.float64)
        pred = np.array([2.0, 4.0, 100.0, 4.0], dtype=np.float64)
        mask = np.array([True, True, True, False], dtype=bool)
        # 有効点は index 0, 1（diff=1, 2）→ RMSE = sqrt((1+4)/2)
        assert np.isclose(_rmse_masked(target, pred, mask), np.sqrt(2.5))

    def test_rmse_zero_when_no_valid_points(self) -> None:
        """有効点ゼロなら 0.0。"""
        target = np.array([np.nan, np.nan], dtype=np.float64)
        pred = np.array([1.0, 2.0], dtype=np.float64)
        mask = np.array([True, True], dtype=bool)
        assert _rmse_masked(target, pred, mask) == 0.0

    def test_std_delta_zero_when_single_point(self) -> None:
        """有効点 1 以下なら標準偏差 0.0。"""
        target = np.array([1.0, np.nan], dtype=np.float64)
        pred = np.array([2.0, 5.0], dtype=np.float64)
        mask = np.array([True, True], dtype=bool)
        assert _std_delta_masked(target, pred, mask) == 0.0

    def test_std_delta_uses_ddof_one(self) -> None:
        """Δ標準偏差は ddof=1（不偏）で算出する。"""
        target = np.array([0.0, 0.0, 0.0], dtype=np.float64)
        pred = np.array([1.0, 2.0, 3.0], dtype=np.float64)
        mask = np.array([True, True, True], dtype=bool)
        # delta = [1, 2, 3], std(ddof=1) = 1.0
        assert np.isclose(_std_delta_masked(target, pred, mask), 1.0)


class TestChannelMetric:
    """``_channel_metric`` の DTO 組み立て。"""

    def test_builds_metric_dto(self) -> None:
        """n_valid / rmse / std_delta / unit を集約する。"""
        target = np.array([1.0, 2.0, 3.0], dtype=np.float64)
        pred = np.array([2.0, 3.0, 4.0], dtype=np.float64)
        valid = np.array([True, True, True], dtype=bool)
        metric = _channel_metric(target, pred, valid, "A")
        assert metric.n_valid == 3
        assert np.isclose(metric.rmse, 1.0)
        assert metric.unit == "A"


class TestCurveMetricsZeros:
    """``_CurveMetrics.zeros`` のフォールバック既定値。"""

    def test_all_zero_metrics(self) -> None:
        """カーブ比較不能時は全チャネル 0、有効点 0。"""
        metrics = _CurveMetrics.zeros()
        assert metrics.n_valid_union == 0
        assert metrics.line_current.rmse == 0.0
        assert metrics.output_power.n_valid == 0
        assert metrics.power_factor.unit == "-"
        assert metrics.im_efficiency.std_delta == 0.0


class TestFittedParameters:
    """``_fitted_parameters`` の記述子 → 報告 DTO 変換。"""

    def test_maps_descriptors_to_reports(self) -> None:
        """path / 初期値 / 上下限 / 単位 / 境界判定を反映する。"""
        descriptors = [
            FittableParamDescriptor(
                path=("im", "primary_resistance"),
                current_value=1.0,
                lb=0.0,
                ub=10.0,
                unit="Ω",
            ),
            FittableParamDescriptor(
                path=("cable", "ground_resistance_length"),
                current_value=5.0,
                lb=5.0,
                ub=5.0,
                unit="Ω*m",
            ),
        ]
        fitted_x = np.array([10.0, 5.0], dtype=np.float64)
        reports = EstimateParamsFitSummaryBuilder._fitted_parameters(
            descriptors, fitted_x
        )
        assert len(reports) == 2
        first = reports[0]
        assert first.path == "im.primary_resistance"
        assert first.initial_value == 1.0
        assert first.fitted_value == 10.0
        assert first.is_at_upper_bound is True
        assert first.is_fixed is False
        # lb==ub の記述子は固定扱い。
        assert reports[1].is_fixed is True

    def test_length_mismatch_raises(self) -> None:
        """記述子と値の長さ不一致は zip(strict=True) で例外。"""
        descriptors = [
            FittableParamDescriptor(
                path=("im", "primary_resistance"),
                current_value=1.0,
                lb=0.0,
                ub=10.0,
                unit="Ω",
            ),
        ]
        with pytest.raises(ValueError):
            EstimateParamsFitSummaryBuilder._fitted_parameters(
                descriptors, np.array([1.0, 2.0])
            )


def _comparison_two_points() -> CurveFitComparisonData:
    """2 格子点・チャネル別 valid を持つ比較データ stub。

    |I| / η は両点観測、P は 1 点のみ観測、PF は全点未観測とする。
    """
    return CurveFitComparisonData(
        slip_fraction=np.array([0.02, 0.04], dtype=np.float64),
        target_i=np.array([10.0, 20.0], dtype=np.float64),
        pred_i=np.array([11.0, 19.0], dtype=np.float64),
        valid_i=np.array([True, True], dtype=bool),
        target_p=np.array([100.0, np.nan], dtype=np.float64),
        pred_p=np.array([110.0, 0.0], dtype=np.float64),
        valid_p=np.array([True, False], dtype=bool),
        target_pf=np.array([np.nan, np.nan], dtype=np.float64),
        pred_pf=np.array([0.0, 0.0], dtype=np.float64),
        valid_pf=np.array([False, False], dtype=bool),
        target_eta=np.array([0.90, 0.92], dtype=np.float64),
        pred_eta=np.array([0.91, 0.93], dtype=np.float64),
        valid_eta=np.array([True, True], dtype=bool),
    )


class TestBuildIntegration:
    """``build`` 全体が要約 DTO を組み立てる結合テスト。

    カーブ比較は ``extract_curve_fit_comparison_data`` を stub 化して固定し、
    残差 RMS・有効点・最適化結果・チャネル指標・fitted パラメータの結線を検証する。
    """

    def test_build_assembles_summary(
        self,
        monkeypatch,
        config: IConfig,
        logger: ILogger,
        input_im_cable_system_dtos: InputDtos,
    ) -> None:
        """各サブ DTO が期待どおり集約される。"""
        input_dto = input_im_cable_system_dtos.get_all()[0]
        descriptors = [
            FittableParamDescriptor(
                path=("im", "primary_resistance"),
                current_value=1.0,
                lb=0.0,
                ub=10.0,
                unit="Ω",
            ),
        ]
        fitted_x = np.array([2.0], dtype=np.float64)
        optimize_result = SimpleNamespace(
            fun=np.array([0.3, 0.4], dtype=np.float64),
            success=True,
            message="ok",
            nfev=7,
            cost=0.125,
        )
        monkeypatch.setattr(
            builder_module,
            "extract_curve_fit_comparison_data",
            lambda *_args: _comparison_two_points(),
        )

        builder = EstimateParamsFitSummaryBuilder.create(
            config=config, logger=logger
        )
        summary = builder.build(
            input_dto=input_dto,
            descriptors=descriptors,
            fitted_x=fitted_x,
            optimize_result=cast(OptimizeResult, optimize_result),
            pc_catalogs=input_dto.im_pc_catalogs,
            itm_done=cast(ItmDto, SimpleNamespace()),
        )

        # 残差 [0.3, 0.4] の RMS = sqrt((0.09+0.16)/2) = sqrt(0.125)
        assert np.isclose(
            summary.overall_rmse_weighted_residual, np.sqrt(0.125)
        )
        assert summary.n_residual_elements == 2
        # 有効点和集合: valid_i(T,T) | ... = [T, T] → 2
        assert summary.n_valid_curve_points == 2
        # 最適化器の生結果。
        assert summary.optimizer_result.success is True
        assert summary.optimizer_result.nfev == 7
        assert np.isclose(summary.optimizer_result.cost, 0.125)
        # |I| は両点観測、RMSE = sqrt(((11-10)^2+(19-20)^2)/2) = 1.0
        assert summary.line_current.n_valid == 2
        assert np.isclose(summary.line_current.rmse, 1.0)
        # P は 1 点のみ観測、PF は全点未観測。
        assert summary.output_power.n_valid == 1
        assert summary.power_factor.n_valid == 0
        # fitted パラメータが記述子と一致。
        assert len(summary.fitted_parameters) == 1
        assert summary.fitted_parameters[0].path == "im.primary_resistance"
        assert summary.fitted_parameters[0].fitted_value == 2.0
        # config 由来の条件 DTO が載っている。
        assert isinstance(summary.optimizer_settings.max_nfev, int)
        assert summary.residual_objective_settings.normalize_by_point_count is (
            False
        )
