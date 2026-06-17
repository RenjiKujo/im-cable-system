"""make_table ステップ（OutputDto → 表 artifact）のインターフェース。

artifact は過剰抽象を避け pandas ``DataFrame`` を素で返す。保存（I/O）は
本ステップでは行わず、export ステップの責務とする。
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from pandas import DataFrame

from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.output import OutputDto


class ITableBuilder(ABC):
    """OutputDto から表 DataFrame を組み立てる契約。"""

    @classmethod
    @abstractmethod
    def create(
        cls,
        config: IConfig,
        logger: ILogger,
    ) -> ITableBuilder:
        """config / logger からビルダーを生成する。

        Args:
            config: 設定オブジェクト。
            logger: ロガーオブジェクト。

        Returns:
            ITableBuilder: 生成されたビルダー。
        """
        pass

    @abstractmethod
    def build(self, output_dto: OutputDto) -> DataFrame:
        """OutputDto から表 DataFrame を組み立てて返す（保存はしない）。

        横軸は実装する出力系に依存する（supply_grid: slip /
        operating_points: index）。各種特性値の列を持つ表を構成し、派生量
        （PF / |I| / 出力比 等）は ``output_dto.result`` から算出する。

        Args:
            output_dto: 出力データ DTO。

        Returns:
            DataFrame: 組み立てた表。
        """
        pass
