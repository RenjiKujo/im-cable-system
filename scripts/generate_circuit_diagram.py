"""README 用の等価回路図（PNG）を生成するスクリプト。

IM+ケーブル系の代表構成として、π型ケーブル（任意区間）と T 型誘導電動機
等価回路を 1 相分で描く。図内では単一かごを実線、二重かごの追加枝を破線、
ケーブルを任意ブロックとして示すことで、「ケーブルあり専用」「二重かご専用」
「T型専用」ではなく、構成を切り替えられるモデルであることを README 上で伝える。

レイアウト方針:
    上側レール（直列経路）と下側レール（共通帰路）の 2 本で構成し、分路
    （ケーブル対地アドミタンス・励磁・二次）は両レール間に渡す縦枝として描く。
    対地アドミタンスと励磁は「抵抗 ‖ リアクタンス（容量）」の並列ブロックで、
    共通の関数 :func:`_parallel_block` を用いて同じ見た目に揃える。素子の x 位置
    は十分な間隔を取り、素子・リード線・ラベルが重ならないようにする。

使い方::

    MPLBACKEND=Agg .venv/bin/python scripts/generate_circuit_diagram.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import schemdraw  # noqa: E402
import schemdraw.elements as elm  # noqa: E402
from matplotlib import patches  # noqa: E402

_OUTPUT_FILENAME = "equivalent_circuit.png"
_FIGURE_SIZE = (16.6, 5.0)
_DPI = 200

# 上側レール（直列経路）と下側レール（共通帰路）の y 座標。
_TOP = 2.4
_BOTTOM = -0.9

# 上下レール中点（分路素子をこの高さに中心化する）。
_MID = (_TOP + _BOTTOM) / 2.0

# 分路素子（対地アドミタンス・励磁・二次）を収める共通の縦バンド。中点を挟んで
# 対称に置き、上下レール導体から十分なリード長を確保する。
_SHUNT_TOP = _MID + 0.75
_SHUNT_BOTTOM = _MID - 0.75

# 並列ブロック（抵抗 ‖ リアクタンス/容量）の 2 脚を中心から左右に振る量。
_BLOCK_HALF_WIDTH = 0.45

# 縦枝（二次）の素子寸法。コイルは励磁 Xm と同じ長さ・同じ elm.Inductor2 で
# 描く。抵抗とコイルの接続リードを上下レールの中点 _MID に置きつつ、上下の
# リードも短くするため、抵抗も同じ長さにして中点の上半分をちょうど埋める
# （上半分＝抵抗・下半分＝コイルの対称配置）。
_VERTICAL_RESISTOR_LEN = 1.5
_VERTICAL_INDUCTOR_LEN = 1.5
_VERTICAL_GAP = 0.15

# 直列素子の x 区間と分路タップの x 位置（左から）。素子・リード・ラベルが
# 重ならないよう、各ブロック脚と隣接素子の間に十分な間隔を取る。
_X_SOURCE = 0.0
_X_CABLE_IN = 1.7
_X_RC = (2.7, 4.2)
_X_XC = (4.5, 6.0)
_X_CABLE_OUT = 7.0
_X_R1 = (8.3, 9.8)
_X_X1 = (10.1, 11.6)
_X_MAG = 12.5
_X_ROTOR_IN = 14.6
_X_ROTOR_OUT = 16.6

_DASH = "--"


def _assets_dir() -> Path:
    """README 用アセットディレクトリを返す。"""
    return Path(__file__).resolve().parents[1] / "docs" / "assets"


def _series(
    drawing: schemdraw.Drawing,
    element: elm.Element,
    span: tuple[float, float],
    label: str,
) -> None:
    """上側レール上に直列素子を 1 つ描く。"""
    start, end = span
    drawing.add(
        element.at((start, _TOP)).to((end, _TOP)).label(label, loc="top")
    )


def _parallel_block(
    drawing: schemdraw.Drawing,
    x_center: float,
    left_element: elm.Element,
    right_element: elm.Element,
) -> None:
    """並列ブロック（左素子 ‖ 右素子）を縦枝として両レール間に描く。

    上側レール上の 1 点（タップ）から分岐し、上側バーで左右 2 脚に分け、左脚に
    ``left_element``・右脚に ``right_element`` を縦に置き、下側バーで合流して下側
    レールへ落とす。対地アドミタンス（抵抗 ‖ 容量）と励磁（抵抗 ‖ リアクタンス）
    を同じ見た目に揃えるための共通処理。ラベルは重なりを避けるため
    :func:`_add_branch_labels` 側で配置する（ここでは付けない）。

    Args:
        drawing: 追記先の Drawing。
        x_center: 上側レール上のタップ x 座標（ブロックの中心）。
        left_element: 左脚に置く素子（抵抗を想定）。
        right_element: 右脚に置く素子（容量またはリアクトルを想定）。
    """
    left_x = x_center - _BLOCK_HALF_WIDTH
    right_x = x_center + _BLOCK_HALF_WIDTH
    # 上側レールからの分岐タップと、上側バーまでのリード。
    drawing.add(elm.Dot().at((x_center, _TOP)))
    drawing.add(elm.Line().at((x_center, _TOP)).to((x_center, _SHUNT_TOP)))
    # 上側バー（左右 2 脚へ分岐）。
    drawing.add(elm.Line().at((left_x, _SHUNT_TOP)).to((right_x, _SHUNT_TOP)))
    # 並列 2 脚（左: 抵抗 / 右: 容量 or リアクトル）。
    drawing.add(
        left_element.at((left_x, _SHUNT_TOP)).to((left_x, _SHUNT_BOTTOM))
    )
    drawing.add(
        right_element.at((right_x, _SHUNT_TOP)).to((right_x, _SHUNT_BOTTOM))
    )
    # 下側バー（合流）と下側レールへの帰路。
    drawing.add(
        elm.Line().at((left_x, _SHUNT_BOTTOM)).to((right_x, _SHUNT_BOTTOM))
    )
    drawing.add(
        elm.Line().at((x_center, _SHUNT_BOTTOM)).to((x_center, _BOTTOM))
    )


def _vertical_two_elements(
    drawing: schemdraw.Drawing,
    x_position: float,
    *,
    line_style: str = "-",
) -> None:
    """抵抗 + リアクタンスを縦に積んだ枝を両レール間に渡す。

    縦枝のラベルは重なりを避けるため、描画後に :func:`_add_branch_labels`
    で ``ax.text`` を用いて配置する（ここでは付けない）。
    """
    # 抵抗とコイルの接続リード（両者の間のギャップ）が、上側レール（導線）と
    # 下側レール（アース線）のちょうど中点 _MID に来るように配置する。中点を
    # 挟んで上に抵抗・下にコイル（Xm と同寸の elm.Inductor2）を置き、間のリード
    # は短く保つ。抵抗・コイルとも長さを揃え、上下のリードも短くする。
    half_gap = _VERTICAL_GAP / 2.0
    resistor_bottom = _MID + half_gap
    resistor_top = resistor_bottom + _VERTICAL_RESISTOR_LEN
    inductor_top = _MID - half_gap
    inductor_bottom = inductor_top - _VERTICAL_INDUCTOR_LEN
    drawing.add(
        elm.Line()
        .at((x_position, _TOP))
        .to((x_position, resistor_top))
        .linestyle(line_style)
    )
    drawing.add(
        elm.Resistor()
        .at((x_position, resistor_top))
        .to((x_position, resistor_bottom))
        .linestyle(line_style)
    )
    drawing.add(
        elm.Line()
        .at((x_position, resistor_bottom))
        .to((x_position, inductor_top))
        .linestyle(line_style)
    )
    drawing.add(
        elm.Inductor2()
        .at((x_position, inductor_top))
        .to((x_position, inductor_bottom))
        .linestyle(line_style)
    )
    drawing.add(
        elm.Line()
        .at((x_position, inductor_bottom))
        .to((x_position, _BOTTOM))
        .linestyle(line_style)
    )


def _draw_circuit() -> schemdraw.Drawing:
    """π型ケーブル + IM 等価回路（T型）の Drawing を組み立てる。"""
    drawing = schemdraw.Drawing(show=False)
    drawing.config(unit=1.0, fontsize=12)

    # 入力電圧源（左の縦枝）。
    drawing.add(
        elm.SourceSin()
        .at((_X_SOURCE, _BOTTOM))
        .to((_X_SOURCE, _TOP))
        .label("$V_s$", loc="left")
    )
    # 下側レール（共通帰路）を電源から二次外かごまで連続させる。
    drawing.add(elm.Line().at((_X_SOURCE, _BOTTOM)).to((_X_ROTOR_OUT, _BOTTOM)))

    # 上側レール（直列経路）のリード。素子区間の隙間を埋める。
    drawing.add(elm.Line().at((_X_SOURCE, _TOP)).to((_X_CABLE_IN, _TOP)))
    drawing.add(elm.Line().at((_X_CABLE_IN, _TOP)).to((_X_RC[0], _TOP)))
    drawing.add(elm.Line().at((_X_RC[1], _TOP)).to((_X_XC[0], _TOP)))
    drawing.add(elm.Line().at((_X_XC[1], _TOP)).to((_X_CABLE_OUT, _TOP)))
    drawing.add(elm.Line().at((_X_CABLE_OUT, _TOP)).to((_X_R1[0], _TOP)))
    drawing.add(elm.Line().at((_X_R1[1], _TOP)).to((_X_X1[0], _TOP)))
    # 一次端から二次タップまで（途中 _X_MAG で励磁を分岐）。
    drawing.add(elm.Line().at((_X_X1[1], _TOP)).to((_X_ROTOR_IN, _TOP)))
    drawing.add(elm.Line().at((_X_ROTOR_IN, _TOP)).to((_X_ROTOR_OUT, _TOP)))

    # π型ケーブル（1 区間、両端に対地分路 = 抵抗 ‖ 容量）。
    _parallel_block(drawing, _X_CABLE_IN, elm.Resistor(), elm.Capacitor())
    _series(drawing, elm.Resistor(), _X_RC, "$R_c$")
    _series(drawing, elm.Inductor2(), _X_XC, "$X_c$")
    _parallel_block(drawing, _X_CABLE_OUT, elm.Resistor(), elm.Capacitor())

    # IM 一次（T型の直列枝）。
    _series(drawing, elm.Resistor(), _X_R1, "$R_1$")
    _series(drawing, elm.Inductor2(), _X_X1, "$X_1$")

    # 励磁枝（Rm ‖ Xm）。対地分路と同じ並列ブロックで描く。
    _parallel_block(drawing, _X_MAG, elm.Resistor(), elm.Inductor2())

    # 二次タップ（単一/二重かご）。
    drawing.add(elm.Dot().at((_X_ROTOR_IN, _TOP)))
    _vertical_two_elements(drawing, _X_ROTOR_IN)
    drawing.add(elm.Dot().at((_X_ROTOR_OUT, _TOP)))
    _vertical_two_elements(drawing, _X_ROTOR_OUT, line_style=_DASH)
    return drawing


def _add_branch_labels(ax: plt.Axes) -> None:
    """並列ブロック（対地・励磁）・二次のラベルを重なりなく明示配置する。"""
    # 抵抗・容量は脚の近くでよいが、コイル（Inductor2）は左右に膨らむため、
    # コイル側ラベル（Xm・二次）はオフセットを広めに取って重なりを避ける。
    r_offset = _BLOCK_HALF_WIDTH + 0.3
    coil_offset = _BLOCK_HALF_WIDTH + 0.5
    rotor_offset = 0.45
    branch_labels = (
        (_X_CABLE_IN - r_offset, _MID, "$R_g$", "right"),
        (_X_CABLE_IN + r_offset, _MID, "$C_g$", "left"),
        (_X_CABLE_OUT - r_offset, _MID, "$R_g$", "right"),
        (_X_CABLE_OUT + r_offset, _MID, "$C_g$", "left"),
        (_X_MAG - r_offset, _MID, "$R_m$", "right"),
        (_X_MAG + coil_offset, _MID, "$X_m$", "left"),
        (_X_ROTOR_IN + rotor_offset, 1.58, "$R_{2,in}/s$", "left"),
        (_X_ROTOR_IN + rotor_offset, -0.08, "$X_{2,in}$", "left"),
        (_X_ROTOR_OUT + rotor_offset, 1.58, "$R_{2,out}/s$", "left"),
        (_X_ROTOR_OUT + rotor_offset, -0.08, "$X_{2,out}$", "left"),
    )
    for x_position, y_position, label, ha in branch_labels:
        ax.text(
            x_position,
            y_position,
            label,
            fontsize=12,
            ha=ha,
            va="center",
        )


def _add_group_callouts(ax: plt.Axes) -> None:
    """各機能ブロックの見出しを回路の上側に配置する。"""
    callout_y = 3.35
    groups = (
        (4.35, "Cable (π): 0..N sections", "#1f77b4"),
        (9.95, "Stator", "#444444"),
        (12.5, "Magnetizing", "#444444"),
        (15.6, "Rotor (1 or 2 cages)", "#444444"),
    )
    for x_center, text, color in groups:
        ax.text(
            x_center,
            callout_y,
            text,
            fontsize=10,
            color=color,
            ha="center",
            va="bottom",
            fontweight="bold",
        )


def _add_optional_boxes(ax: plt.Axes) -> None:
    """ケーブル・外かごが任意であることを破線枠で示す。"""
    cable_box = patches.Rectangle(
        (0.55, -1.15),
        7.6,
        3.9,
        linewidth=1.2,
        edgecolor="#1f77b4",
        facecolor="none",
        linestyle="--",
    )
    ax.add_patch(cable_box)

    outer_box = patches.Rectangle(
        (16.25, -1.15),
        0.7,
        3.9,
        linewidth=1.2,
        edgecolor="#888888",
        facecolor="none",
        linestyle="--",
    )
    ax.add_patch(outer_box)
    ax.text(
        16.6,
        -1.35,
        "optional\nouter cage",
        fontsize=8.5,
        color="#888888",
        ha="center",
        va="top",
    )


def main() -> int:
    """等価回路図を ``docs/assets`` に保存する。"""
    assets_dir = _assets_dir()
    assets_dir.mkdir(parents=True, exist_ok=True)

    drawing = _draw_circuit()
    backend_figure = drawing.draw(show=False)
    fig = backend_figure.fig
    fig.set_size_inches(*_FIGURE_SIZE)
    ax = fig.axes[0]
    ax.set_xlim(-0.8, 18.4)
    ax.set_ylim(-1.9, 3.9)
    _add_branch_labels(ax)
    _add_group_callouts(ax)
    _add_optional_boxes(ax)
    fig.suptitle(
        "Representative IM + Cable Equivalent Circuit (one phase, T-type)",
        fontsize=14,
        y=0.99,
    )
    fig.savefig(assets_dir / _OUTPUT_FILENAME, dpi=_DPI)
    plt.close(fig)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
