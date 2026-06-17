"""カーブ残差評価器のインターフェース。"""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np


class ICurveResidualEvaluator(ABC):
    """試行点（ボックス正規化座標）に対する残差ベクトルを返す。"""

    @abstractmethod
    def evaluate(self, z: np.ndarray) -> np.ndarray:
        """試行パラメータ z に対する残差ベクトルを返す。

        Args:
            z: ボックス正規化座標上の試行点。

        Returns:
            np.ndarray: 重み付き残差ベクトル（float64）。
        """
        pass
