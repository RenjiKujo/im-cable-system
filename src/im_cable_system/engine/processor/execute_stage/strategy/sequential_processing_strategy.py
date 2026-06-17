"""逐次処理戦略実装。

このモジュールは、逐次処理（並列処理を使用しない）の
ストラテジーパターン実装を提供します。
"""

from collections.abc import Callable

from im_cable_system.engine.processor.execute_stage.strategy.i_data_processing_strategy import (  # noqa: E501
    IDataProcessingStrategy,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.input import (
    InputDto,
)
from im_cable_system.engine.shared.dto.itm import (
    ItmDto,
)


class SequentialProcessingStrategy(IDataProcessingStrategy):
    """逐次処理戦略実装。

    並列処理を使用せず、アイテムを順番に処理します。
    """

    def __init__(self, config: IConfig, logger: ILogger) -> None:
        """逐次処理戦略のインスタンスを初期化する。

        Args:
            config: 設定オブジェクト。
            logger: ロガーオブジェクト。
        """
        self._config: IConfig = config
        self._logger: ILogger = logger

    @classmethod
    def create(
        cls, config: IConfig, logger: ILogger
    ) -> IDataProcessingStrategy:
        """逐次処理戦略のインスタンスを生成するファクトリーメソッド。

        Args:
            config: 設定オブジェクト。
            logger: ロガーオブジェクト。

        Returns:
            IDataProcessingStrategy: 生成された戦略インスタンス。
        """
        return cls(config=config, logger=logger)

    def process(
        self,
        items: list[InputDto],
        process_func: Callable[[InputDto], ItmDto],
    ) -> list[ItmDto]:
        """アイテムのリストを逐次処理する。

        Args:
            items: 処理対象の InputDto のリスト。
            process_func: 各アイテムを処理する関数。

        Returns:
            list[ItmDto]: 処理結果のリスト（入力順序を保持）。
        """
        results: list[ItmDto] = []
        for item in items:
            result = process_func(item)
            results.append(result)
        return results
