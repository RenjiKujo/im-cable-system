"""残差評価（evaluate_residual）。

ボックス正規化座標の試行点 z を物理パラメータへ写像し、forward（検証なし）で
再計算したカタログ残差ベクトルを返す :class:`CurveResidualEvaluator` を公開する。
最適化（:mod:`fit_parameters.optimize`）から目的関数として利用される。
"""

from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.fit_parameters.evaluate_residual.curve_residual_evaluator import (  # noqa: E501
    CurveResidualEvaluator,
)
from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.fit_parameters.evaluate_residual.i_curve_residual_evaluator import (  # noqa: E501
    ICurveResidualEvaluator,
)

__all__: list[str] = [
    "CurveResidualEvaluator",
    "ICurveResidualEvaluator",
]
