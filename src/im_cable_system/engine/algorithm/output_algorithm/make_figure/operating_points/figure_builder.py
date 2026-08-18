"""make_figure（operating_points 系）の実装。

``OutputDto`` から運転点（リスト番号）を横軸とする性能 Figure を組み立てる。
A4 横 1 枚にサブプロット 1 つを置き、回転数 / 電流 / 電圧 / 周波数 / 出力 /
トルク / 効率 / 力率を、量ごとのスケール差を保つよう複数の縦軸へ分けて描く。
図表専用 DTO は作らず、``OutputDto.result`` / ``array_layout`` から派生計算する。
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from im_cable_system.engine.algorithm.output_algorithm.make_figure.i_figure_builder import (  # noqa: E501
    IFigureBuilder,
)
from im_cable_system.engine.algorithm.output_algorithm.make_figure.operating_points.plotting import (  # noqa: E501
    _A4_LANDSCAPE_INCHES,
    _COLOR_EFFICIENCY,
    _COLOR_FREQUENCY,
    _COLOR_LINE_CURRENT,
    _COLOR_OUTPUT_POWER,
    _COLOR_POWER_FACTOR,
    _COLOR_SPEED,
    _COLOR_TORQUE,
    _COLOR_VOLTAGE,
    _PRINT_DPI,
    _attach_figure_legend,
    _make_value_axis,
    _plot_index_series,
    _set_integer_xaxis,
)
from im_cable_system.engine.algorithm.output_algorithm.make_figure.operating_points.series import (  # noqa: E501
    _derive_series,
    _operating_point_count,
    _OperatingPointSeries,
)

# NOTE: model_label_lines は supply_grid 配下にあるが、表示チャート種別に
#     依存しない共有ユーティリティ（データ源は OutputDto.im / OutputDto.cable
#     のみ）として supply_grid の公開窓口が例外的に公開している。
from im_cable_system.engine.algorithm.output_algorithm.make_figure.supply_grid import (  # noqa: E501
    model_label_lines,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.output import OutputDto


def _output_display_name(output_dto: OutputDto) -> str:
    """OutputDto の表示名（name の基底名部分）をタイトル用の文字列へ変換する。"""
    return output_dto.name.get_base()


def _draw_dimensionless_base(
    ax: Axes,
    x: np.ndarray,
    series: _OperatingPointSeries,
) -> None:
    """ベース左軸に PF・η（無次元 0–1）を描く。"""
    ax.plot(
        x,
        series.power_factor,
        color=_COLOR_POWER_FACTOR,
        linestyle="-",
        marker=".",
        markersize=4,
        label="PF [-]",
    )
    ax.plot(
        x,
        series.efficiency,
        color=_COLOR_EFFICIENCY,
        linestyle="-",
        marker=".",
        markersize=4,
        label="η [-]",
    )
    ax.set_ylabel("PF / η [-]")
    ax.set_ylim(0.0, 1.0)


def _draw_right_axes(
    ax_base: Axes,
    x: np.ndarray,
    series: _OperatingPointSeries,
) -> None:
    """右側の追加軸へ Pout / |I_line| / T を描く。"""
    ax_power = _make_value_axis(ax_base, side="right", offset=0)
    _plot_index_series(
        ax_power,
        x,
        series.output_power_w,
        color=_COLOR_OUTPUT_POWER,
        label="Pout [W]",
    )
    ax_current = _make_value_axis(ax_base, side="right", offset=65)
    _plot_index_series(
        ax_current,
        x,
        series.input_current_magnitude_a,
        color=_COLOR_LINE_CURRENT,
        label="|I_line| [A]",
    )
    ax_torque = _make_value_axis(ax_base, side="right", offset=130)
    _plot_index_series(
        ax_torque,
        x,
        series.torque_nm,
        color=_COLOR_TORQUE,
        label="T [N·m]",
    )


def _draw_left_axes(
    ax_base: Axes,
    x: np.ndarray,
    series: _OperatingPointSeries,
) -> None:
    """左側の追加軸へ 回転数 / 周波数 / 電圧 を描く（無い量は省く）。"""
    ax_speed = _make_value_axis(ax_base, side="left", offset=55)
    _plot_index_series(
        ax_speed,
        x,
        series.rotational_speed_rpm,
        color=_COLOR_SPEED,
        label="Speed [rpm]",
    )
    if series.frequency_hz is not None:
        ax_frequency = _make_value_axis(ax_base, side="left", offset=120)
        _plot_index_series(
            ax_frequency,
            x,
            series.frequency_hz,
            color=_COLOR_FREQUENCY,
            label="f [Hz]",
        )
    if series.voltage_v is not None:
        ax_voltage = _make_value_axis(ax_base, side="left", offset=185)
        _plot_index_series(
            ax_voltage,
            x,
            series.voltage_v,
            color=_COLOR_VOLTAGE,
            label="V [V]",
        )


class OperatingPointsFigureBuilder(IFigureBuilder):
    """OutputDto から運転点ごとの index 性能 Figure を組み立てるビルダー。"""

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
        """OutputDto から運転点 index 横軸の性能 Figure を組み立てて返す。

        A4 横 1 枚にサブプロット 1 つを置き、PF・η を左ベース軸、Pout・
        |I_line|・T を右の追加軸、回転数・周波数・電圧を左の追加軸へ、量ごとの
        スケールを保って描く。運転点数が 0 の場合は、呼び出し側の出力フローを
        止めないため空の ``Figure`` を返す。
        """
        num_points = _operating_point_count(output_dto)
        if num_points <= 0:
            return Figure()

        series = _derive_series(output_dto)
        x = np.arange(num_points, dtype=np.float64)

        figure, ax_base = plt.subplots(
            1,
            1,
            figsize=_A4_LANDSCAPE_INCHES,
            dpi=_PRINT_DPI,
            squeeze=True,
        )
        _draw_dimensionless_base(ax_base, x, series)
        _draw_right_axes(ax_base, x, series)
        _draw_left_axes(ax_base, x, series)
        _set_integer_xaxis(ax_base, num_points=num_points)

        figure.suptitle(
            f"{_output_display_name(output_dto)} - operating point performance",
            fontsize=11,
        )
        figure.text(
            0.02,
            0.02,
            "\n".join(model_label_lines(output_dto)),
            fontsize=7,
            va="bottom",
            ha="left",
        )
        # NOTE: 縦軸を多数 outward に並べるため tight_layout は使わない
        #     （外側スパインを内側へ押し込み、プロット領域が潰れるため）。
        #     プロット枠を中央寄りに固定し、左右に追加軸用の余白を確保する。
        #     bottom はモデル名注記（最大 7 行程度）の分だけ広げてある。
        figure.subplots_adjust(
            left=0.30,
            right=0.76,
            top=0.90,
            bottom=0.20,
        )
        _attach_figure_legend(figure)
        return figure
