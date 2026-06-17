"""データ処理戦略のインターフェース定義。

このモジュールは、並列処理と逐次処理を抽象化する
ストラテジーパターンのインターフェースを定義します。
IM ケーブルシステム用に InputDto / ItmDto を扱う。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable

from im_cable_system.engine.shared.dto.input import (
    InputDto,
)
from im_cable_system.engine.shared.dto.itm import (
    ItmDto,
)


class IDataProcessingStrategy(ABC):
    """データ処理戦略のインターフェース。

    並列処理と逐次処理を抽象化するストラテジーパターンの契約を定義します。
    IM ケーブルシステムの InputDto / ItmDto を扱う。
    """

    @abstractmethod
    def process(
        self,
        items: list[InputDto],
        process_func: Callable[[InputDto], ItmDto],
    ) -> list[ItmDto]:
        """アイテムのリストを処理する。

        設定に応じて並列処理または逐次処理を実行します。
        入力順序は保持されます。

        Args:
            items: 処理対象の InputDto のリスト。
            process_func: 各アイテムを処理する関数。

        Returns:
            list[ItmDto]: 処理結果のリスト（入力順序を保持）。

        Raises:
            ValueError: 処理に失敗した場合。
        """
        pass
