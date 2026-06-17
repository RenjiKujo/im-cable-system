"""supply_grid 図群が共有する描画・凡例・レイアウトのヘルパ。

slip 軸サブプロットの多軸（左軸＋右軸3本）描画、カタログ重ね描き、サブプロット
横断の統合凡例（重複排除・整列）、A4 グリッドレイアウトを提供する。横軸の意味
（slip / 出力比）に依存しない描画作法を集約し、各ビルダーから利用する。
"""

from __future__ import annotations

import math

import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.lines import Line2D

from im_cable_system.engine.algorithm.output_algorithm.make_figure.supply_grid.catalog import (  # noqa: E501
    _CatalogSlice,
)
from im_cable_system.engine.algorithm.output_algorithm.make_figure.supply_grid.series import (  # noqa: E501
    _SupplySlice,
)
from im_cable_system.engine.shared.dto.output import OutputDto

# 物理量ごとの線色（全 Figure 共通）。同じ量はどの図でも同色にするため、
# 量を主語にした名前付き定数を一元管理する（measured は明色、catalog は暗色）。
_COLOR_POWER_FACTOR = "#1f77b4"
_COLOR_EFFICIENCY = "#ff7f0e"
_COLOR_OUTPUT_POWER = "#2ca02c"
_COLOR_LINE_CURRENT = "#d62728"
_COLOR_TORQUE = "#9467bd"
_COLOR_SPEED = "#8c564b"

_CATALOG_COLOR_POWER_FACTOR = "#144d75"
_CATALOG_COLOR_EFFICIENCY = "#a65309"
_CATALOG_COLOR_OUTPUT_POWER = "#1d681d"
_CATALOG_COLOR_LINE_CURRENT = "#8b191a"
_CATALOG_COLOR_TORQUE = "#5c3a80"
_CATALOG_COLOR_SPEED = "#4f342e"

# slip 横軸図の描画順（PF / η / Pout / |I_line| / T）に対応する色並び。
_SERIES_COLORS = (
    _COLOR_POWER_FACTOR,
    _COLOR_EFFICIENCY,
    _COLOR_OUTPUT_POWER,
    _COLOR_LINE_CURRENT,
    _COLOR_TORQUE,
)
_CATALOG_COLORS = (
    _CATALOG_COLOR_POWER_FACTOR,
    _CATALOG_COLOR_EFFICIENCY,
    _CATALOG_COLOR_OUTPUT_POWER,
    _CATALOG_COLOR_LINE_CURRENT,
    _CATALOG_COLOR_TORQUE,
)
_CATALOG_LINESTYLE = "--"
_CATALOG_LABEL_PREFIX = "Catalog "
# 凡例の量の並び順（measured / catalog 共通）。
_LEGEND_QUANTITY_ORDER = (
    "Pout [W]",
    "T [N·m]",
    "|I_line| [A]",
    "η [-]",
    "PF [-]",
)
# A4 横（210x297mm）を inch 換算した Figure サイズ。A4 1 枚への印刷を前提に、
# サブプロット数によらず固定サイズで作る（サイズ・解像度の責務は build 側）。
_A4_LANDSCAPE_INCHES = (11.69, 8.27)
# 印刷用解像度 [dpi]。figure.dpi として保持し、表示・保存の双方で使われる。
_PRINT_DPI = 300


def _subplot_layout(num_plots: int) -> tuple[int, int]:
    """サブプロット数から格子レイアウトを返す。"""
    if num_plots <= 0:
        return (1, 1)
    cols = math.ceil(math.sqrt(num_plots))
    rows = math.ceil(num_plots / cols)
    return (rows, cols)


def _plot_slice(
    ax_left: Axes,
    supply_slice: _SupplySlice | _CatalogSlice,
    *,
    linestyle: str,
    label_prefix: str,
    colors: tuple[str, ...],
) -> tuple[Axes, Axes, Axes, Axes]:
    """1つの slip 軸系列を左軸と右軸3本に描画する。"""
    slip = np.flip(supply_slice.slip)
    series = supply_slice.series
    output_power = np.flip(series.output_power_w)
    current = np.flip(series.input_current_magnitude_a)
    power_factor = np.flip(series.power_factor)
    efficiency = np.flip(series.efficiency)
    torque = np.flip(series.torque_nm)

    ax_left.invert_xaxis()
    ax_left.plot(
        slip,
        power_factor,
        color=colors[0],
        linestyle=linestyle,
        label=f"{label_prefix}PF [-]",
    )
    ax_left.plot(
        slip,
        efficiency,
        color=colors[1],
        linestyle=linestyle,
        label=f"{label_prefix}η [-]",
    )
    ax_left.set_xlabel("Slip [-]")
    ax_left.set_ylabel("PF / η [-]")
    ax_left.set_ylim(0.0, 1.0)
    ax_left.grid(True, alpha=0.3)

    ax_right_power = ax_left.twinx()
    ax_right_power.plot(
        slip,
        output_power,
        color=colors[2],
        linestyle=linestyle,
        label=f"{label_prefix}Pout [W]",
    )
    ax_right_power.spines["right"].set_position(("outward", 0))
    ax_right_power.set_ylabel("Pout [W]")

    ax_right_current = ax_left.twinx()
    ax_right_current.plot(
        slip,
        current,
        color=colors[3],
        linestyle=linestyle,
        label=f"{label_prefix}|I_line| [A]",
    )
    ax_right_current.spines["right"].set_position(("outward", 60))
    ax_right_current.set_ylabel("|I_line| [A]")

    ax_right_torque = ax_left.twinx()
    if not np.all(np.isnan(torque)):
        ax_right_torque.plot(
            slip,
            torque,
            color=colors[4],
            linestyle=linestyle,
            label=f"{label_prefix}T [N·m]",
        )
    ax_right_torque.spines["right"].set_position(("outward", 120))
    ax_right_torque.set_ylabel("T [N·m]")

    return (ax_left, ax_right_power, ax_right_current, ax_right_torque)


def _overlay_slice(
    axis_quad: tuple[Axes, Axes, Axes, Axes],
    supply_slice: _CatalogSlice,
    *,
    linestyle: str,
    label_prefix: str,
    colors: tuple[str, ...],
) -> None:
    """既存の slip 軸4軸へカタログ系列を重ね描きする。"""
    ax_left, ax_right_power, ax_right_current, ax_right_torque = axis_quad
    slip = np.flip(supply_slice.slip)
    series = supply_slice.series
    ax_left.plot(
        slip,
        np.flip(series.power_factor),
        color=colors[0],
        linestyle=linestyle,
        label=f"{label_prefix}PF [-]",
    )
    ax_left.plot(
        slip,
        np.flip(series.efficiency),
        color=colors[1],
        linestyle=linestyle,
        label=f"{label_prefix}η [-]",
    )
    ax_right_power.plot(
        slip,
        np.flip(series.output_power_w),
        color=colors[2],
        linestyle=linestyle,
        label=f"{label_prefix}Pout [W]",
    )
    ax_right_current.plot(
        slip,
        np.flip(series.input_current_magnitude_a),
        color=colors[3],
        linestyle=linestyle,
        label=f"{label_prefix}|I_line| [A]",
    )
    torque = np.flip(series.torque_nm)
    if not np.all(np.isnan(torque)):
        ax_right_torque.plot(
            slip,
            torque,
            color=colors[4],
            linestyle=linestyle,
            label=f"{label_prefix}T [N·m]",
        )


def _public_lines(ax: Axes) -> list[Line2D]:
    """凡例に出す public ラベル付き Line2D を返す。"""
    return [
        line
        for line in ax.get_lines()
        if line.get_label() and not str(line.get_label()).startswith("_")
    ]


def _legend_sort_key(label: str) -> tuple[int, int]:
    """凡例ラベルの並び順キー（measured→catalog、量の定義順）を返す。

    ``ncol=len(量)`` の凡例にしたとき、1 段目に measured 系列、2 段目に
    Catalog 系列が量の順（Pout / T / |I_line| / η / PF）で並ぶようにする。
    """
    is_catalog = 1 if label.startswith(_CATALOG_LABEL_PREFIX) else 0
    quantity = label.removeprefix(_CATALOG_LABEL_PREFIX)
    try:
        quantity_rank = _LEGEND_QUANTITY_ORDER.index(quantity)
    except ValueError:
        quantity_rank = len(_LEGEND_QUANTITY_ORDER)
    return (is_catalog, quantity_rank)


def _collect_unique_legend(
    figure: Figure,
) -> tuple[list[Line2D], list[str]]:
    """Fig 全サブプロットの public ラベル線を集め、ラベル重複を除いて整列する。

    全サブプロットで同一ラベル（PF / η / Pout / |I_line| / T と各 Catalog 系列）
    が繰り返し描かれるため、ラベル先勝ちで重複を除いた和集合を作る。色・線種は
    サブプロット間で共通なので、代表ハンドル1本で凡例として十分。順序は
    :func:`_legend_sort_key` に従い measured→catalog・量の定義順に整列する。

    Args:
        figure: 対象 Figure。

    Returns:
        整列・重複排除済みのハンドルとラベルのタプル。
    """
    seen: dict[str, Line2D] = {}
    for ax in figure.axes:
        for line in _public_lines(ax):
            label = str(line.get_label())
            if label not in seen:
                seen[label] = line
    ordered_labels = sorted(seen, key=_legend_sort_key)
    return [seen[label] for label in ordered_labels], ordered_labels


def _attach_figure_legend(figure: Figure) -> None:
    """サブプロット横断の統合凡例を Fig 下部に付与する。"""
    handles, labels = _collect_unique_legend(figure)
    if handles:
        figure.legend(
            handles,
            labels,
            loc="lower center",
            bbox_to_anchor=(0.5, 0.0),
            ncol=min(len(labels), 5),
            frameon=True,
        )


def _subplot_title(supply_slice: _SupplySlice) -> str:
    """(f, V) のサブプロットタイトルを返す。"""
    return (
        f"f = {supply_slice.frequency_hz:.0f} Hz, "
        f"V = {supply_slice.voltage_v:.0f} V"
    )


def _output_name(output_dto: OutputDto) -> str:
    """OutputDto の名前をタイトル用の文字列へ変換する。"""
    name = output_dto.name
    if hasattr(name, "get_value"):
        return str(name.get_value())
    return str(name)
