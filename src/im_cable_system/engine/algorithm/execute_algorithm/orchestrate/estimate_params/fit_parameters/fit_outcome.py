"""パラメータフィットの結果 DTO。

最適化後の物理パラメータ値と、最適化器（``scipy.optimize.least_squares``）の
生結果を保持する。要約 DTO 生成（build_summary）が参照する。
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import (  # type: ignore[import-untyped]
    OptimizeResult,
)


@dataclass(frozen=True)
class FitOutcome:
    """フィット結果。

    Attributes:
        fitted_x: フィット後の物理パラメータ値（記述子順）。
        optimize_result: 最適化器の生結果（収束情報・残差など）。
    """

    fitted_x: np.ndarray
    optimize_result: OptimizeResult
