"""make_figure ステップ（OutputDto → Figure artifact）のインターフェース。

artifact は過剰抽象を避け matplotlib ``Figure`` を素で返す。保存（I/O）は
本ステップでは行わず、export ステップの責務とする。
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from matplotlib.figure import Figure

from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.output import OutputDto


class IFigureBuilder(ABC):
    """OutputDto から Figure を組み立てる契約。"""

    @classmethod
    @abstractmethod
    def create(
        cls,
        config: IConfig,
        logger: ILogger,
    ) -> IFigureBuilder:
        """config / logger からビルダーを生成する。

        Args:
            config: 設定オブジェクト。
            logger: ロガーオブジェクト。

        Returns:
            IFigureBuilder: 生成されたビルダー。
        """
        pass

    @abstractmethod
    def build(self, output_dto: OutputDto) -> Figure:
        """OutputDto から Figure を組み立てて返す（保存はしない）。

        表示形状は実装する出力系に依存する（supply_grid: slip 軸グリッド /
        operating_points: index 時系列）。派生量（PF / |I| / 出力比 等）は
        ``output_dto.result`` から算出する。

        Args:
            output_dto: 出力データ DTO。

        Returns:
            Figure: 組み立てた matplotlib Figure。
        """
        pass
