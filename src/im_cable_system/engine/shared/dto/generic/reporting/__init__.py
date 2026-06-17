"""汎用レポート系 DTO の公開窓口。

最適化・適合度などの「結果レポート」を表す値オブジェクトを束ねる。
これらは Itm モデルに依存しない汎用 DTO であり、``itm`` 中間 DTO と
``output`` 出力 DTO の双方から、ステージ窓口を経由せずに参照できる。

層外・層横断からは本窓口（``generic.reporting``）経由で import すること。
"""

from im_cable_system.engine.shared.dto.generic.reporting.estimate_params_fit_summary_dto import (  # noqa: E501
    EstimateParamsFitSummaryDto,
    FitChannelMetricDto,
    FittedModelLabelsDto,
    FittedParameterReportDto,
    OptimizerResultDto,
    OptimizerSettingsDto,
    ResidualObjectiveSettingsDto,
)
from im_cable_system.engine.shared.dto.generic.reporting.numerical_stability_report_dto import (  # noqa: E501
    NumericalStabilityReportDto,
)

__all__ = [
    "EstimateParamsFitSummaryDto",
    "FitChannelMetricDto",
    "FittedModelLabelsDto",
    "FittedParameterReportDto",
    "NumericalStabilityReportDto",
    "OptimizerResultDto",
    "OptimizerSettingsDto",
    "ResidualObjectiveSettingsDto",
]
