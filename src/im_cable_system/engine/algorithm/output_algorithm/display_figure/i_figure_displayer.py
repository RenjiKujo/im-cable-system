"""Figure display ステップ（Figure artifact の画面表示）のインターフェース。

build / 保存と分離した表示専用ステップ。表示可否（ON/OFF）の判定は呼び出し側
（orchestrator）が config フラグで行い、本ステップは渡された Figure の表示
のみを担う（Figure の生成・加工・保存はしない）。
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from matplotlib.figure import Figure

from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.output import OutputDto


class IFigureDisplayer(ABC):
    """Figure を画面に表示する契約。"""

    @classmethod
    @abstractmethod
    def create(
        cls,
        config: IConfig,
        logger: ILogger,
    ) -> IFigureDisplayer:
        """config / logger から displayer を生成する。

        Args:
            config: 設定オブジェクト。
            logger: ロガーオブジェクト。

        Returns:
            IFigureDisplayer: 生成された displayer。
        """
        pass

    @abstractmethod
    def show(self, figure: Figure, output_dto: OutputDto) -> None:
        """渡された Figure をそのまま画面に表示する。

        本ステップは Figure を変更・再構築・保存しない（保存は
        export_figure、生成・加工は make_figure の責務）。表示時間は
        ``config.output_figures_config.show_duration_seconds`` に従う。

        ``output_dto`` の用途（意図）:
            現状は未使用だが、将来ウィンドウタイトル等の表示文脈に系統名
            （``output_dto.name``）等を反映できるよう受け取っておく。保存
            （export_figure）と引数の対を揃える意図もある。

        Args:
            figure: 表示対象の matplotlib Figure（完成済み）。
            output_dto: 出力データ DTO（表示文脈。現状未使用）。
        """
        pass
