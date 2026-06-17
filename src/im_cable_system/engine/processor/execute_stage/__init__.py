"""IM ケーブルシステム実行ステージ実装。

機能別に ``IStage[InputDtos, ItmDtos]`` を実装する。各ステージは
逐次／並列を :mod:`strategy` のファクトリーで決定し、結果 ItmDtos の
ダンプを :mod:`dump_itm_dto` の共通関数に委譲する。ステージ自身は
「どの Execute オーケストレーターを使うか」と InputDtos→ItmDtos の
受け渡しだけを担う。

- ``ForwardExecuteStage``: スリップ既知 forward（CartesianGrid / OperatingPoints 共通）
- ``EstimateParamsExecuteStage``: パラメータ推定
"""

from im_cable_system.engine.processor.execute_stage.estimate_params_execute_stage import (  # noqa: E501
    EstimateParamsExecuteStage,
)
from im_cable_system.engine.processor.execute_stage.forward_execute_stage import (  # noqa: E501
    ForwardExecuteStage,
)
from im_cable_system.engine.processor.execute_stage.strategy import (  # noqa: E501
    DataProcessingStrategyFactory,
    IDataProcessingStrategy,
    ParallelProcessingStrategy,
    SequentialProcessingStrategy,
)

__all__ = [
    "DataProcessingStrategyFactory",
    "IDataProcessingStrategy",
    "EstimateParamsExecuteStage",
    "ForwardExecuteStage",
    "ParallelProcessingStrategy",
    "SequentialProcessingStrategy",
]
