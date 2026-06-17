"""IM ケーブルシステム出力ステージ実装。

``IStage[ItmDtos, OutputDtos]`` を実装する。実行モードごとに分割する。

- ``ForwardByCartesianGridOutputStage``: 直交格子順計算の Itm を出力へ変換
- ``ForwardByOperatingPointsOutputStage``: 運転点指定順計算の Itm を出力へ変換
- ``EstimateParamsOutputStage``: パラメータ推定の Itm を出力へ変換
  （レポート出力は per-itm の orchestrator に閉じる。3 モードとも同型）
"""

from im_cable_system.engine.processor.output_stage.estimate_params_output_stage import (  # noqa: E501
    EstimateParamsOutputStage,
)
from im_cable_system.engine.processor.output_stage.forward_by_cartesian_grid_output_stage import (  # noqa: E501
    ForwardByCartesianGridOutputStage,
)
from im_cable_system.engine.processor.output_stage.forward_by_operating_points_output_stage import (  # noqa: E501
    ForwardByOperatingPointsOutputStage,
)

__all__ = [
    "EstimateParamsOutputStage",
    "ForwardByCartesianGridOutputStage",
    "ForwardByOperatingPointsOutputStage",
]
