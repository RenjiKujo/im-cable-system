"""最適化（optimize）。

ボックス正規化座標で ``scipy.optimize.least_squares`` を実行し、
残差評価（:mod:`fit_parameters.evaluate_residual`）を目的関数として
パラメータをフィットさせる :class:`CurveParameterFitter` を公開する。
将来のソルバー追加（別実装・ファクトリー）はこのサブパッケージに閉じる。
"""

from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.fit_parameters.optimize.curve_parameter_fitter import (  # noqa: E501
    CurveParameterFitter,
)
from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.fit_parameters.optimize.i_curve_parameter_fitter import (  # noqa: E501
    ICurveParameterFitter,
)

__all__: list[str] = [
    "CurveParameterFitter",
    "ICurveParameterFitter",
]
