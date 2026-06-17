"""残差正規化ストラテジ factory。"""

from __future__ import annotations

from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.support.curve_eval.residual_normalization.i_residual_normalization_strategy import (  # noqa: E501
    IResidualNormalizationStrategy,
)
from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.support.curve_eval.residual_normalization.residual_normalization_strategy import (  # noqa: E501
    ByCurveScaleResidualNormalizationStrategy,
    ByReferenceResidualNormalizationStrategy,
    NoResidualNormalizationStrategy,
)
from im_cable_system.engine.shared.config import (
    ResidualNormalizationConfig,
    ResidualNormalizationMethod,
)


class ResidualNormalizationStrategyFactory:
    """残差正規化 config から対応する strategy を生成する。"""

    @staticmethod
    def create(
        config: ResidualNormalizationConfig,
    ) -> IResidualNormalizationStrategy:
        """正規化 method に応じた strategy を返す。

        Args:
            config: 残差正規化設定。

        Returns:
            IResidualNormalizationStrategy: 正規化 strategy。

        Raises:
            ValueError: 未対応の method が指定された場合。
        """
        if config.method is ResidualNormalizationMethod.BY_CURVE_SCALE:
            return ByCurveScaleResidualNormalizationStrategy(
                statistic=config.statistic,
                eps=config.eps,
            )
        if config.method is ResidualNormalizationMethod.BY_REFERENCE:
            return ByReferenceResidualNormalizationStrategy(
                statistic=config.statistic,
                eps=config.eps,
            )
        if config.method is ResidualNormalizationMethod.NONE:
            return NoResidualNormalizationStrategy()
        raise ValueError(f"未対応の残差正規化方式です: {config.method}")
