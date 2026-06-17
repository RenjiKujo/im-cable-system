"""残差正規化 strategy（residual_normalization）。

``calculation.execute.estimate_params.residual.normalization`` の method に応じて、
カーブ残差のスケール正規化を差し替えるための strategy と factory を公開する。
"""

from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.support.curve_eval.residual_normalization.factory_residual_normalization_strategy import (  # noqa: E501
    ResidualNormalizationStrategyFactory,
)
from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.support.curve_eval.residual_normalization.i_residual_normalization_strategy import (  # noqa: E501
    IResidualNormalizationStrategy,
)
from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.support.curve_eval.residual_normalization.residual_normalization_strategy import (  # noqa: E501
    ByCurveScaleResidualNormalizationStrategy,
    ByReferenceResidualNormalizationStrategy,
    NoResidualNormalizationStrategy,
)

__all__: list[str] = [
    "ByCurveScaleResidualNormalizationStrategy",
    "ByReferenceResidualNormalizationStrategy",
    "IResidualNormalizationStrategy",
    "NoResidualNormalizationStrategy",
    "ResidualNormalizationStrategyFactory",
]
