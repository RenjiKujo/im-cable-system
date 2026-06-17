"""残差正規化ストラテジの実装。"""

from __future__ import annotations

import numpy as np

from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.support.curve_eval.residual_normalization.i_residual_normalization_strategy import (  # noqa: E501
    IResidualNormalizationStrategy,
)
from im_cable_system.engine.shared.config import ResidualNormalizationStatistic


class BaseResidualNormalizationStrategy(IResidualNormalizationStrategy):
    """正規化に共通する mask と統計量計算を提供する基底実装。"""

    def __init__(
        self,
        statistic: ResidualNormalizationStatistic,
        eps: float,
    ) -> None:
        """統計量種別と eps を保持する。"""
        self._statistic: ResidualNormalizationStatistic = statistic
        self._eps: float = eps

    def normalize(
        self,
        target: np.ndarray,
        pred: np.ndarray,
        valid: np.ndarray,
    ) -> np.ndarray:
        """正規化済み残差 ``(target - pred) / scale`` を返す。"""
        channel_ok = self._channel_ok(target=target, pred=pred, valid=valid)
        if not np.any(channel_ok):
            return np.zeros_like(target, dtype=np.float64)
        scale_values = self._scale_values(
            target=np.asarray(target[channel_ok], dtype=np.float64),
            pred=np.asarray(pred[channel_ok], dtype=np.float64),
        )
        scale = self._scale(scale_values)
        diff = np.asarray(target - pred, dtype=np.float64)
        return np.where(channel_ok, diff / scale, 0.0)

    def _scale_values(
        self,
        target: np.ndarray,
        pred: np.ndarray,
    ) -> np.ndarray:
        """scale 算出に使う値列を返す。"""
        raise NotImplementedError

    def _channel_ok(
        self,
        target: np.ndarray,
        pred: np.ndarray,
        valid: np.ndarray,
    ) -> np.ndarray:
        """評価対象かつ target / pred が有限のマスクを返す。"""
        return (
            np.asarray(valid, dtype=bool)
            & np.isfinite(target)
            & np.isfinite(pred)
        )

    def _scale(self, values: np.ndarray) -> float:
        """設定された代表統計量から正規化スケールを算出する。"""
        finite_values = np.asarray(
            values[np.isfinite(values)], dtype=np.float64
        )
        if finite_values.size == 0:
            return self._eps
        abs_values = np.abs(finite_values)
        if self._statistic is ResidualNormalizationStatistic.MAX:
            base = float(np.max(abs_values))
        elif self._statistic is ResidualNormalizationStatistic.MEAN:
            base = float(np.mean(abs_values))
        elif self._statistic is ResidualNormalizationStatistic.P95:
            base = float(np.percentile(abs_values, 95.0))
        elif self._statistic is ResidualNormalizationStatistic.STD:
            base = float(np.std(finite_values, ddof=0))
        else:
            raise ValueError(f"未対応の残差正規化統計量です: {self._statistic}")
        return max(base, 0.0) + self._eps


class ByCurveScaleResidualNormalizationStrategy(
    BaseResidualNormalizationStrategy
):
    """target と pred を結合したカーブスケールで正規化する。"""

    def _scale_values(
        self,
        target: np.ndarray,
        pred: np.ndarray,
    ) -> np.ndarray:
        """target と pred を結合した値列を返す。"""
        return np.concatenate([target, pred])


class ByReferenceResidualNormalizationStrategy(
    BaseResidualNormalizationStrategy
):
    """target（参照値）だけのスケールで正規化する。"""

    def _scale_values(
        self,
        target: np.ndarray,
        _pred: np.ndarray,
    ) -> np.ndarray:
        """target の値列を返す。"""
        return target


class NoResidualNormalizationStrategy(IResidualNormalizationStrategy):
    """正規化せず ``target - pred`` を返す。"""

    def normalize(
        self,
        target: np.ndarray,
        pred: np.ndarray,
        valid: np.ndarray,
    ) -> np.ndarray:
        """正規化しない残差を返す。"""
        channel_ok = (
            np.asarray(valid, dtype=bool)
            & np.isfinite(target)
            & np.isfinite(pred)
        )
        diff = np.asarray(target - pred, dtype=np.float64)
        return np.where(channel_ok, diff, 0.0)
