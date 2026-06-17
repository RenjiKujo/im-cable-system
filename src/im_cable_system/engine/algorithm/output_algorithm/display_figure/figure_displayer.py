"""Figure display ステップの実装。

完成済み Figure を表示し、表示後に閉じる。生成・加工・保存は行わない。
"""

from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from im_cable_system.engine.algorithm.output_algorithm.display_figure.i_figure_displayer import (  # noqa: E501
    IFigureDisplayer,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.output import OutputDto

# 画面表示用の dpi。make_figure は印刷用（A4 / 高 dpi）で Figure を作るため、
# そのまま表示すると画面に対して過大になり窮屈に見える。Export は show より
# 前に完了しているため、ここで dpi を下げても保存済みファイルには影響しない。
_SCREEN_DPI = 100


class FigureDisplayer(IFigureDisplayer):
    """Figure を画面に表示する displayer。"""

    def __init__(self, config: IConfig, logger: ILogger) -> None:
        """インスタンスを初期化する。

        Args:
            config: 設定オブジェクト。
            logger: ロガーオブジェクト。
        """
        self._config: IConfig = config
        self._logger: ILogger = logger

    @classmethod
    def create(
        cls,
        config: IConfig,
        logger: ILogger,
    ) -> IFigureDisplayer:
        """displayer のインスタンスを生成する。"""
        return cls(config=config, logger=logger)

    def show(self, figure: Figure, output_dto: OutputDto) -> None:
        """渡された Figure を画面に表示し、表示後に閉じる。

        ``output_dto`` は将来の表示文脈（ウィンドウタイトル等）に用いる
        ために受け取る（現状未使用）。Figure の生成・加工・保存はしないが、
        画面に収まるよう表示用 dpi（``_SCREEN_DPI``）へ下げてから表示する
        （Export は show より前に完了済みのため保存物には影響しない）。

        表示時間は ``output_figures_config.show_duration_seconds`` に従う。
        """
        _ = output_dto
        duration = self._config.output_figures_config.show_duration_seconds
        figure.set_dpi(_SCREEN_DPI)
        figure_number = getattr(figure, "number", None)
        if figure_number is not None:
            plt.figure(figure_number)
        plt.show(block=False)
        plt.pause(max(duration, 0.01))
        plt.close(figure)
