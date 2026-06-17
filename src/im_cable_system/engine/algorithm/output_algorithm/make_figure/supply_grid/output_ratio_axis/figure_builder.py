"""make_figure（supply_grid / 出力比横軸）の実装。

供給電圧・周波数を (f, V) サブプロット軸、出力比 [%] を横軸とする性能曲線
Figure を ``OutputDto`` から組み立てる。縦軸は電流比 [%] / 回転数 [rpm] /
PF [%] / 効率 [%] とし、参照カタログが同じ (f, V) 条件にある場合は破線で
重ね描きする。
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.lines import Line2D

from im_cable_system.engine.algorithm.output_algorithm.make_figure.i_figure_builder import (  # noqa: E501
    IFigureBuilder,
)
from im_cable_system.engine.algorithm.output_algorithm.make_figure.supply_grid.catalog import (  # noqa: E501
    _build_catalog_slices,
    _CatalogSlice,
    _match_catalog,
)
from im_cable_system.engine.algorithm.output_algorithm.make_figure.supply_grid.plotting_common import (  # noqa: E501
    _A4_LANDSCAPE_INCHES,
    _CATALOG_COLOR_EFFICIENCY,
    _CATALOG_COLOR_LINE_CURRENT,
    _CATALOG_COLOR_POWER_FACTOR,
    _CATALOG_COLOR_SPEED,
    _CATALOG_LABEL_PREFIX,
    _COLOR_EFFICIENCY,
    _COLOR_LINE_CURRENT,
    _COLOR_POWER_FACTOR,
    _COLOR_SPEED,
    _PRINT_DPI,
    _output_name,
    _public_lines,
    _subplot_layout,
    _subplot_title,
)
from im_cable_system.engine.algorithm.output_algorithm.make_figure.supply_grid.ratios import (  # noqa: E501
    _current_ratio_percent,
    _output_ratio_percent,
    _ratio_to_percent,
)
from im_cable_system.engine.algorithm.output_algorithm.make_figure.supply_grid.series import (  # noqa: E501
    _build_simulated_slices,
    _has_required_axes,
    _SupplySlice,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.output import OutputDto

# 描画順（Current ratio / Speed / PF / η）に対応する色並び。物理量ごとの色は
# plotting_common の共有定数を参照し、全 Figure で同じ量を同色に保つ。
_SERIES_COLORS = (
    _COLOR_LINE_CURRENT,
    _COLOR_SPEED,
    _COLOR_POWER_FACTOR,
    _COLOR_EFFICIENCY,
)
_CATALOG_COLORS = (
    _CATALOG_COLOR_LINE_CURRENT,
    _CATALOG_COLOR_SPEED,
    _CATALOG_COLOR_POWER_FACTOR,
    _CATALOG_COLOR_EFFICIENCY,
)
_CATALOG_LINESTYLE = "--"
_LEGEND_LABEL_ORDER = (
    "Current ratio [%]",
    "Speed [rpm]",
    "PF [%]",
    "η [%]",
)


def _legend_sort_key(label: str) -> tuple[int, int]:
    """出力比横軸 Figure の凡例順序キーを返す。"""
    is_catalog = 1 if label.startswith(_CATALOG_LABEL_PREFIX) else 0
    quantity = label.removeprefix(_CATALOG_LABEL_PREFIX)
    try:
        quantity_rank = _LEGEND_LABEL_ORDER.index(quantity)
    except ValueError:
        quantity_rank = len(_LEGEND_LABEL_ORDER)
    return (is_catalog, quantity_rank)


def _collect_unique_legend(
    figure: Figure,
) -> tuple[list[Line2D], list[str]]:
    """Fig 全サブプロットの凡例候補を重複排除して整列する。"""
    seen: dict[str, Line2D] = {}
    for ax in figure.axes:
        for line in _public_lines(ax):
            label = str(line.get_label())
            if label not in seen:
                seen[label] = line
    labels = sorted(seen, key=_legend_sort_key)
    return [seen[label] for label in labels], labels


def _attach_figure_legend(figure: Figure) -> None:
    """サブプロット横断の統合凡例を Fig 下部に付与する。"""
    handles, labels = _collect_unique_legend(figure)
    if handles:
        figure.legend(
            handles,
            labels,
            loc="lower center",
            bbox_to_anchor=(0.5, 0.0),
            ncol=min(len(labels), len(_LEGEND_LABEL_ORDER)),
            frameon=True,
        )


def _peak_output_slip(supply_slice: _SupplySlice) -> float:
    """出力（Pout）が最大となる slip を返す。"""
    slip = np.asarray(supply_slice.slip, dtype=np.float64)
    output_power = np.asarray(
        supply_slice.series.output_power_w, dtype=np.float64
    )
    peak_index = int(np.nanargmax(output_power))
    return float(slip[peak_index])


def _stable_region_mask(
    supply_slice: _SupplySlice | _CatalogSlice,
    *,
    slip_upper: float,
) -> np.ndarray:
    """出力最大点より小 slip 側（ピーク含む）を残すマスクを返す。"""
    slip = np.asarray(supply_slice.slip, dtype=np.float64)
    return slip <= slip_upper


def _plot_output_ratio_slice(
    ax_left: Axes,
    supply_slice: _SupplySlice | _CatalogSlice,
    output_dto: OutputDto,
    *,
    linestyle: str,
    label_prefix: str,
    colors: tuple[str, ...],
    slip_upper: float,
    ax_right_speed: Axes | None = None,
) -> tuple[Axes, Axes]:
    """1つの (f, V) 系列を出力比横軸で描画する。

    出力最大点より小 slip 側（ピーク含む）だけを描く。``slip_upper`` は
    シミュレーション側の出力最大 slip を渡し、シミュレーション・カタログの
    双方に共通適用する（安定運転領域に揃える）。
    """
    series = supply_slice.series
    mask = _stable_region_mask(supply_slice, slip_upper=slip_upper)
    output_ratio = _output_ratio_percent(series, output_dto)[mask]
    current_ratio = _current_ratio_percent(series, output_dto)[mask]
    speed = series.rotational_speed_rpm[mask]
    power_factor = _ratio_to_percent(series.power_factor)[mask]
    efficiency = _ratio_to_percent(series.efficiency)[mask]

    ax_left.plot(
        output_ratio,
        current_ratio,
        color=colors[0],
        linestyle=linestyle,
        label=f"{label_prefix}Current ratio [%]",
    )
    ax_left.plot(
        output_ratio,
        power_factor,
        color=colors[2],
        linestyle=linestyle,
        label=f"{label_prefix}PF [%]",
    )
    ax_left.plot(
        output_ratio,
        efficiency,
        color=colors[3],
        linestyle=linestyle,
        label=f"{label_prefix}η [%]",
    )
    ax_left.set_xlabel("Output ratio [%]")
    ax_left.set_ylabel("Current ratio / PF / η [%]")
    ax_left.grid(True, alpha=0.3)

    if ax_right_speed is None:
        ax_right_speed = ax_left.twinx()
    if not np.all(np.isnan(speed)):
        ax_right_speed.plot(
            output_ratio,
            speed,
            color=colors[1],
            linestyle=linestyle,
            label=f"{label_prefix}Speed [rpm]",
        )
    ax_right_speed.set_ylabel("Speed [rpm]")
    return (ax_left, ax_right_speed)


class SupplyGridOutputRatioFigureBuilder(IFigureBuilder):
    """OutputDto から出力比横軸グリッド表示の Figure を組み立てるビルダー。"""

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
        """OutputDto から出力比横軸グリッド Figure を組み立てて返す。

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
            slip_upper = _peak_output_slip(simulated)
            axis_pair = _plot_output_ratio_slice(
                ax,
                simulated,
                output_dto,
                linestyle="-",
                label_prefix="",
                colors=_SERIES_COLORS,
                slip_upper=slip_upper,
            )
            catalog = _match_catalog(simulated, catalog_slices)
            if catalog is not None:
                _plot_output_ratio_slice(
                    axis_pair[0],
                    catalog,
                    output_dto,
                    linestyle=_CATALOG_LINESTYLE,
                    label_prefix=_CATALOG_LABEL_PREFIX,
                    colors=_CATALOG_COLORS,
                    slip_upper=slip_upper,
                    ax_right_speed=axis_pair[1],
                )
            ax.set_title(_subplot_title(simulated), fontsize=9)

        for index in range(len(simulated_slices), len(axes_flat)):
            axes_flat[index].set_visible(False)

        figure.suptitle(
            f"{_output_name(output_dto)} - output ratio performance",
            fontsize=11,
        )
        figure.tight_layout(rect=(0.055, 0.16, 0.91, 0.93))
        _attach_figure_legend(figure)
        return figure
