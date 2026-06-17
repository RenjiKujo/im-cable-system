"""データ処理戦略パッケージ。

このパッケージは、並列処理と逐次処理を抽象化する
ストラテジーパターンを提供します。
"""

from im_cable_system.engine.processor.execute_stage.strategy.factory_data_processing_strategy import (  # noqa: E501
    DataProcessingStrategyFactory,
)
from im_cable_system.engine.processor.execute_stage.strategy.i_data_processing_strategy import (  # noqa: E501
    IDataProcessingStrategy,
)
from im_cable_system.engine.processor.execute_stage.strategy.parallel_processing_strategy import (  # noqa: E501
    ParallelProcessingStrategy,
)
from im_cable_system.engine.processor.execute_stage.strategy.sequential_processing_strategy import (  # noqa: E501
    SequentialProcessingStrategy,
)

__all__ = [
    "IDataProcessingStrategy",
    "SequentialProcessingStrategy",
    "ParallelProcessingStrategy",
    "DataProcessingStrategyFactory",
]
