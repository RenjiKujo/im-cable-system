"""operating_points 図の描画・多軸レイアウト・凡例のヘルパ。

運転点（index）横軸の 1 サブプロットに、量ごとのスケール差を保ったまま複数の
縦軸（左ベース＋左右の追加軸）へ系列を描く作法を集約する。量ごとの線色は全図で
共通になるよう名前付き定数で一元管理する。
"""

from __future__ import annotations

from typing import Literal

import numpy as np
from matplotlib.artist import Artist
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator

# 物理量ごとの線色（量を主語にした名前付き定数で一元管理する）。
_COLOR_POWER_FACTOR = "#1f77b4"
_COLOR_EFFICIENCY = "#ff7f0e"
_COLOR_OUTPUT_POWER = "#2ca02c"
_COLOR_LINE_CURRENT = "#d62728"
_COLOR_TORQUE = "#9467bd"
_COLOR_SPEED = "#8c564b"
_COLOR_FREQUENCY = "#e377c2"
_COLOR_VOLTAGE = "#17becf"

# A4 横（210x297mm）を inch 換算した Figure サイズ（1 枚印刷前提の固定値）。
_A4_LANDSCAPE_INCHES = (11.69, 8.27)
# 印刷用解像度 [dpi]。
_PRINT_DPI = 300

# 凡例の量の並び順（左ベース → 右軸 → 左追加軸の描画順に合わせる）。
_LEGEND_QUANTITY_ORDER = (
    "PF [-]",
    "η [-]",
    "Pout [W]",
    "|I_line| [A]",
    "T [N·m]",
    "Speed [rpm]",
    "f [Hz]",
    "V [V]",
)


def _make_value_axis(
    ax_base: Axes,
    *,
    side: Literal["left", "right"],
    offset: float,
) -> Axes:
    """ベース軸に対し、指定側へ ``offset`` ポイント外側に出した値軸を作る。

    Args:
        ax_base: 横軸を共有するベース軸。
        side: ``"left"`` または ``"right"``。spine・目盛り・ラベルの配置側。
        offset: spine をプロット領域から外側に出す距離 [points]。

    Returns:
        Axes: 追加した値軸（横軸はベースと共有）。
    """
    ax = ax_base.twinx()
    other = "right" if side == "left" else "left"
    ax.spines[side].set_position(("outward", offset))
    ax.spines[side].set_visible(True)
    ax.spines[other].set_visible(False)
    ax.yaxis.set_label_position(side)
    ax.yaxis.set_ticks_position(side)
    return ax


def _plot_index_series(
    ax: Axes,
    x: np.ndarray,
    y: np.ndarray,
    *,
    color: str,
    label: str,
) -> None:
    """運転点 index 横軸に 1 系列をマーカー付き折れ線で描く。"""
    ax.plot(
        x,
        y,
        color=color,
        linestyle="-",
        marker=".",
        markersize=4,
        label=label,
    )
    ax.set_ylabel(label, color=color)
    ax.tick_params(axis="y", colors=color)


def _set_integer_xaxis(ax: Axes, *, num_points: int) -> None:
    """横軸を運転点 index（整数）に整える。"""
    ax.set_xlabel("Operating point")
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.set_xlim(-0.5, num_points - 0.5)
    ax.grid(True, alpha=0.3)


def _legend_sort_key(label: str) -> int:
    """凡例ラベルの並び順キー（量の定義順）を返す。"""
    try:
        return _LEGEND_QUANTITY_ORDER.index(label)
    except ValueError:
        return len(_LEGEND_QUANTITY_ORDER)


def _attach_figure_legend(figure: Figure) -> None:
    """全軸の凡例候補を量の定義順に整列し、Fig 下部へ統合凡例を付与する。"""
    seen: dict[str, Artist] = {}
    for ax in figure.axes:
        handles, labels = ax.get_legend_handles_labels()
        for handle, label in zip(handles, labels, strict=True):
            if label and not label.startswith("_") and label not in seen:
                seen[label] = handle
    ordered = sorted(seen, key=_legend_sort_key)
    if ordered:
        figure.legend(
            [seen[label] for label in ordered],
            ordered,
            loc="lower center",
            bbox_to_anchor=(0.5, 0.0),
            ncol=min(len(ordered), len(_LEGEND_QUANTITY_ORDER)),
            frameon=True,
        )
