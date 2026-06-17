"""make_figure（supply_grid / slip 横軸）の実装。

供給電圧・周波数を (f, V) サブプロット軸、slip を横軸とする性能曲線 Figure を
``OutputDto`` から組み立てる。図表専用 DTO は作らず、``OutputDto.result`` の
生量から PF / |I_line| / Pout / η / トルクを派生計算する（``supply_grid`` の
共有モジュールを利用）。
"""

from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from im_cable_system.engine.algorithm.output_algorithm.make_figure.i_figure_builder import (  # noqa: E501
    IFigureBuilder,
)
from im_cable_system.engine.algorithm.output_algorithm.make_figure.supply_grid.catalog import (  # noqa: E501
    _build_catalog_slices,
    _match_catalog,
)
from im_cable_system.engine.algorithm.output_algorithm.make_figure.supply_grid.plotting_common import (  # noqa: E501
    _A4_LANDSCAPE_INCHES,
    _CATALOG_COLORS,
    _CATALOG_LABEL_PREFIX,
    _CATALOG_LINESTYLE,
    _PRINT_DPI,
    _SERIES_COLORS,
    _attach_figure_legend,
    _output_name,
    _overlay_slice,
    _plot_slice,
    _subplot_layout,
    _subplot_title,
)
from im_cable_system.engine.algorithm.output_algorithm.make_figure.supply_grid.series import (  # noqa: E501
    _build_simulated_slices,
    _has_required_axes,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.output import OutputDto


class SupplyGridSlipAxisFigureBuilder(IFigureBuilder):
    """OutputDto から slip 軸グリッド表示の Figure を組み立てるビルダー。"""

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
    ) -> IFigureBuilder:
        """ビルダーのインスタンスを生成する。"""
        return cls(config=config, logger=logger)

    def build(self, output_dto: OutputDto) -> Figure:
        """OutputDto から slip 軸グリッド Figure を組み立てて返す。

        ``array_layout`` に supply_grid の必須軸が揃わない場合は、呼び出し側の
        出力フローを止めないため空の ``Figure`` を返す。
        """
        if not _has_required_axes(output_dto):
            return Figure()

        simulated_slices = _build_simulated_slices(output_dto)
        if not simulated_slices:
            return Figure()

        catalog_slices = _build_catalog_slices(output_dto)
        rows, cols = _subplot_layout(len(simulated_slices))
        figure, axes = plt.subplots(
            rows,
            cols,
            figsize=_A4_LANDSCAPE_INCHES,
            dpi=_PRINT_DPI,
            squeeze=False,
        )
        axes_flat = axes.flatten()

        for index, simulated in enumerate(simulated_slices):
            ax = axes_flat[index]
            axis_quad = _plot_slice(
                ax,
                simulated,
                linestyle="-",
                label_prefix="",
                colors=_SERIES_COLORS,
            )
            catalog = _match_catalog(simulated, catalog_slices)
            if catalog is not None:
                _overlay_slice(
                    axis_quad,
                    catalog,
                    linestyle=_CATALOG_LINESTYLE,
                    label_prefix=_CATALOG_LABEL_PREFIX,
                    colors=_CATALOG_COLORS,
                )
            ax.set_title(_subplot_title(simulated), fontsize=9)

        for index in range(len(simulated_slices), len(axes_flat)):
            axes_flat[index].set_visible(False)

        figure.suptitle(
            f"{_output_name(output_dto)} - slip axis performance",
            fontsize=11,
        )
        figure.tight_layout(rect=(0.055, 0.16, 0.86, 0.93))
        _attach_figure_legend(figure)
        return figure
