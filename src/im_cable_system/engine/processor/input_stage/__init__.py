"""IM ケーブルシステム InputStage の公開窓口。

実行モード別の InputStage 実装（``ForwardByCartesianGrid`` /
``ForwardByOperatingPoints`` / ``EstimateParams``）を pipeline 層に向けて
公開する。Forward 系 2 ステージは ``ForwardJobSpecs`` → :class:`InputDtos`
の同一契約を共有し、``reference_axes`` の差分のみを各ステージが内部で
持つ。
"""

from im_cable_system.engine.processor.input_stage.estimate_params_input_stage import (  # noqa: E501
    EstimateParamsInputStage,
)
from im_cable_system.engine.processor.input_stage.forward_by_cartesian_grid_input_stage import (  # noqa: E501
    ForwardByCartesianGridInputStage,
)
from im_cable_system.engine.processor.input_stage.forward_by_operating_points_input_stage import (  # noqa: E501
    ForwardByOperatingPointsInputStage,
)

__all__ = [
    "EstimateParamsInputStage",
    "ForwardByCartesianGridInputStage",
    "ForwardByOperatingPointsInputStage",
]
