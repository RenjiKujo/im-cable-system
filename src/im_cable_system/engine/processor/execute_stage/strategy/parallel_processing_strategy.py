"""並列処理戦略実装。

このモジュールは、並列処理（Thread/Process）の
ストラテジーパターン実装を提供します。
"""

import os
from collections.abc import Callable, Iterator
from concurrent.futures import (
    Executor,
    Future,
    ProcessPoolExecutor,
    ThreadPoolExecutor,
    as_completed,
)

from im_cable_system.engine.processor.execute_stage.strategy.i_data_processing_strategy import (  # noqa: E501
    IDataProcessingStrategy,
)
from im_cable_system.engine.shared.config import (
    DataProcessingMethod,
    IConfig,
    ILogger,
)
from im_cable_system.engine.shared.dto.input import (
    InputDto,
)
from im_cable_system.engine.shared.dto.itm import (
    ItmDto,
)


class ParallelProcessingStrategy(IDataProcessingStrategy):
    """並列処理戦略実装。

    ThreadPoolExecutorまたはProcessPoolExecutorを使用して
    アイテムを並列処理します。
    """

    def __init__(
        self,
        config: IConfig,
        logger: ILogger,
        method: DataProcessingMethod,
    ) -> None:
        """並列処理戦略のインスタンスを初期化する。

        Args:
            config: 設定オブジェクト。
            logger: ロガーオブジェクト。
            method: 並列処理の方法（``THREAD`` または ``PROCESS``）。
        """
        self._config: IConfig = config
        self._logger: ILogger = logger
        self._method: DataProcessingMethod = method

    @classmethod
    def create(
        cls,
        config: IConfig,
        logger: ILogger,
        method: DataProcessingMethod,
    ) -> IDataProcessingStrategy:
        """並列処理戦略のインスタンスを生成するファクトリーメソッド。

        Args:
            config: 設定オブジェクト。
            logger: ロガーオブジェクト。
            method: 並列処理の方法（``THREAD`` または ``PROCESS``）。

        Returns:
            IDataProcessingStrategy: 生成された戦略インスタンス。

        Raises:
            ValueError: ``method`` が ``THREAD`` でも ``PROCESS`` でもない場合。
        """
        if method not in (
            DataProcessingMethod.THREAD,
            DataProcessingMethod.PROCESS,
        ):
            raise ValueError(
                f"無効な並列処理方法です: {method.value}. "
                f'"thread" または "process" を指定してください。'
            )
        return cls(config=config, logger=logger, method=method)

    def process(
        self,
        items: list[InputDto],
        process_func: Callable[[InputDto], ItmDto],
    ) -> list[ItmDto]:
        """アイテムのリストを並列処理する。

        各 future を完了順（``as_completed``）で回収し、最後に元の入力
        インデックス順へ並べ替えて返す。これにより、先頭タスクが遅い場合に
        完了済みの後続タスクを待たずに結果を回収できる。

        Args:
            items: 処理対象の InputDto のリスト。
            process_func: 各アイテムを処理する関数。

        Returns:
            list[ItmDto]: 処理結果のリスト（入力順序を保持）。

        Raises:
            ValueError: 並列処理方法が不正な場合。
            TimeoutError: ``timeout_seconds`` 内に全タスクが完了しない場合。
        """
        data_processing_config = self._config.data_processing
        max_workers = data_processing_config.max_workers
        timeout_seconds = data_processing_config.timeout_seconds

        if max_workers is None:
            max_workers = os.cpu_count() or 1

        with self._create_executor(max_workers) as executor:
            # 入力順序を保持するために、future へ入力インデックスを対応付ける
            future_to_index = {
                executor.submit(process_func, item): idx
                for idx, item in enumerate(items)
            }
            indexed_results = self._collect_in_completion_order(
                future_to_index=future_to_index,
                timeout_seconds=timeout_seconds,
            )

        # 完了順で集めた結果を、元の入力インデックス順へ並べ替えて返す
        indexed_results.sort(key=lambda indexed: indexed[0])
        return [result for _, result in indexed_results]

    def _create_executor(self, max_workers: int) -> Executor:
        """設定された並列方法に応じた Executor を生成する。

        Args:
            max_workers: 最大ワーカー数。

        Returns:
            Executor: Thread または Process の Executor。

        Raises:
            ValueError: 並列処理方法が ``THREAD`` / ``PROCESS`` でない場合。
        """
        if self._method is DataProcessingMethod.THREAD:
            return ThreadPoolExecutor(max_workers=max_workers)
        if self._method is DataProcessingMethod.PROCESS:
            return ProcessPoolExecutor(max_workers=max_workers)
        raise ValueError(f"無効な並列処理方法です: {self._method.value}")

    def _collect_in_completion_order(
        self,
        future_to_index: dict[Future[ItmDto], int],
        timeout_seconds: float | None,
    ) -> list[tuple[int, ItmDto]]:
        """future を完了順に回収し、(index, 結果) のリストを返す。

        ``future.result()`` の例外はそのまま呼び出し元へ伝播させる。

        Args:
            future_to_index: future から入力インデックスへの対応表。
            timeout_seconds: 全タスクの完了待ち上限秒（None ならなし）。

        Returns:
            list[tuple[int, ItmDto]]: 完了順に並んだ (入力 index, 結果)。

        Raises:
            TimeoutError: ``timeout_seconds`` 内に全タスクが完了しない場合。
        """
        completed: Iterator[Future[ItmDto]]
        if timeout_seconds is not None:
            completed = as_completed(future_to_index, timeout=timeout_seconds)
        else:
            completed = as_completed(future_to_index)

        indexed_results: list[tuple[int, ItmDto]] = []
        for future in completed:
            idx = future_to_index[future]
            indexed_results.append((idx, future.result()))
        return indexed_results
