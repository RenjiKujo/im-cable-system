"""残差正規化 strategy の単体テスト。"""

from __future__ import annotations

import numpy as np
import pytest

from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.support.curve_eval.residual_normalization import (  # noqa: E501
    ByCurveScaleResidualNormalizationStrategy,
    NoResidualNormalizationStrategy,
    ResidualNormalizationStrategyFactory,
)
from im_cable_system.engine.shared.config import (
    ResidualNormalizationConfig,
    ResidualNormalizationMethod,
    ResidualNormalizationStatistic,
)


class TestResidualNormalizationStrategy:
    """正規化 strategy の代表挙動を確認する。"""

    def test_by_curve_scale_std_matches_legacy_formula(self) -> None:
        """std は旧実装の std(concat(target, pred)) + eps と一致する。"""
        target = np.array([1.0, 3.0, np.nan, 7.0], dtype=np.float64)
        pred = np.array([2.0, 5.0, 10.0, 11.0], dtype=np.float64)
        valid = np.array([True, True, True, False])
        eps = 1.0e-12
        strategy = ByCurveScaleResidualNormalizationStrategy(
            statistic=ResidualNormalizationStatistic.STD,
            eps=eps,
        )

        actual = strategy.normalize(target=target, pred=pred, valid=valid)
        scale = float(np.std(np.array([1.0, 3.0, 2.0, 5.0])) + eps)
        expected = np.array(
            [(1.0 - 2.0) / scale, (3.0 - 5.0) / scale, 0.0, 0.0]
        )

        np.testing.assert_allclose(actual, expected)

    def test_none_returns_raw_difference_on_valid_points(self) -> None:
        """none は正規化せず target - pred を返す。"""
        strategy = NoResidualNormalizationStrategy()
        actual = strategy.normalize(
            target=np.array([1.0, 3.0]),
            pred=np.array([2.0, 1.0]),
            valid=np.array([True, False]),
        )
        np.testing.assert_allclose(actual, np.array([-1.0, 0.0]))

    def test_factory_creates_configured_strategy(self) -> None:
        """factory が method に応じた strategy を返す。"""
        config = ResidualNormalizationConfig(
            method=ResidualNormalizationMethod.BY_CURVE_SCALE,
            statistic=ResidualNormalizationStatistic.STD,
            eps=1.0e-12,
        )
        strategy = ResidualNormalizationStrategyFactory.create(config)
        assert isinstance(strategy, ByCurveScaleResidualNormalizationStrategy)

    def test_unknown_statistic_raises(self) -> None:
        """未対応 statistic は ValueError。"""
        strategy = ByCurveScaleResidualNormalizationStrategy(
            statistic="unknown",  # type: ignore[arg-type]
            eps=1.0e-12,
        )
        with pytest.raises(ValueError, match="未対応"):
            strategy.normalize(
                target=np.array([1.0]),
                pred=np.array([2.0]),
                valid=np.array([True]),
            )
