"""残差正規化ストラテジのインターフェース。"""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np


class IResidualNormalizationStrategy(ABC):
    """1 チャネル分の残差を正規化する契約。"""

    @abstractmethod
    def normalize(
        self,
        target: np.ndarray,
        pred: np.ndarray,
        valid: np.ndarray,
    ) -> np.ndarray:
        """正規化済み残差 ``(target - pred) / scale`` を返す。

        Args:
            target: カタログ目標値。
            pred: シミュレーション予測値。
            valid: カタログ側の評価対象マスク。

        Returns:
            np.ndarray: 無効点を 0.0 にした float64 残差。
        """
        pass
