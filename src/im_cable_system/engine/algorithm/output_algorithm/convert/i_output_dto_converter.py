"""ItmDto → OutputDto 変換ステップのインターフェース。

本ステップは output_algorithm で **唯一 itm に依存** する境界である。
以降の make_figure / make_table / export は OutputDto（generic 合成）のみを
参照し、itm 内部構造から切り離す。
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.itm import ItmDto
from im_cable_system.engine.shared.dto.output import OutputDto


class IOutputDtoConverter(ABC):
    """中間 DTO（ItmDto）から出力 DTO（OutputDto）への変換契約。"""

    @classmethod
    @abstractmethod
    def create(
        cls,
        config: IConfig,
        logger: ILogger,
    ) -> IOutputDtoConverter:
        """config / logger から変換器を生成する。

        Args:
            config: 設定オブジェクト。
            logger: ロガーオブジェクト。

        Returns:
            IOutputDtoConverter: 生成された変換器。
        """
        pass

    @abstractmethod
    def convert(self, itm_dto: ItmDto) -> OutputDto:
        """ItmDto から OutputDto を構築して返す。

        入力原値（name / array_layout / im / cable / im_pc_catalogs）と
        シミュレーション結果の生量（result）、レポート（数値安定化・推定要約）を
        OutputDto に詰め替える。

        Args:
            itm_dto: 単一の中間 DTO（model と simulation_result を含む）。

        Returns:
            OutputDto: 出力データ DTO。
        """
        pass
