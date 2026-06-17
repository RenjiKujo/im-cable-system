"""パラメータフィット（fit_parameters）。

ボックス正規化座標での least_squares 実行（:class:`CurveParameterFitter`）、
残差評価器（:class:`CurveResidualEvaluator`）、結果 DTO（:class:`FitOutcome`）を
公開する。最適化ループとその座標変換を本サブパッケージに閉じる。

サブパッケージ構成:
    - :mod:`optimize`: ソルバー実行（least_squares）。
    - :mod:`evaluate_residual`: 目的関数となる残差評価器。
    - ``box_interval_map`` / ``fit_outcome``: 両者が共有する座標写像・結果 DTO。
"""

from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.fit_parameters.evaluate_residual import (  # noqa: E501
    CurveResidualEvaluator,
    ICurveResidualEvaluator,
)
from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.fit_parameters.fit_outcome import (  # noqa: E501
    FitOutcome,
)
from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.fit_parameters.optimize import (  # noqa: E501
    CurveParameterFitter,
    ICurveParameterFitter,
)

__all__: list[str] = [
    "CurveParameterFitter",
    "CurveResidualEvaluator",
    "FitOutcome",
    "ICurveParameterFitter",
    "ICurveResidualEvaluator",
]
