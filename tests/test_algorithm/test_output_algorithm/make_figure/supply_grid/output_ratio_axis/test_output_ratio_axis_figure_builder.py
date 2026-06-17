"""SupplyGridOutputRatioFigureBuilder の描画契約テスト。"""

from __future__ import annotations

from typing import Any

import matplotlib.pyplot as plt
import numpy as np

from im_cable_system.engine.algorithm.output_algorithm.make_figure.supply_grid.output_ratio_axis.figure_builder import (  # noqa: E501
    SupplyGridOutputRatioFigureBuilder,
)
from im_cable_system.engine.shared.config import IConfig, ILogger


class TestSupplyGridOutputRatioFigureBuilder:
    """SupplyGridOutputRatioFigureBuilder.build の契約テスト。"""

    def test_build_returns_empty_figure_when_required_axes_are_missing(
        self,
        config: IConfig,
        logger: ILogger,
        slip_only_output_dto: Any,
    ) -> None:
        """必須軸不足時は空 Figure を返す。"""
        builder = SupplyGridOutputRatioFigureBuilder.create(
            config=config,
            logger=logger,
        )

        figure = builder.build(slip_only_output_dto)

        assert len(figure.axes) == 0

    def test_build_returns_output_ratio_axis_grid_figure(
        self,
        config: IConfig,
        logger: ILogger,
        supply_grid_output_dto: Any,
    ) -> None:
        """出力比横軸と twin 軸の回転数系列を描画する。"""
        builder = SupplyGridOutputRatioFigureBuilder.create(
            config=config,
            logger=logger,
        )

        figure = builder.build(supply_grid_output_dto)

        assert len(figure.axes) == 2
        assert figure.axes[0].get_title() == "f = 60 Hz, V = 460 V"
        assert figure.axes[0].get_xlabel() == "Output ratio [%]"
        assert len(figure.axes[0].get_lines()) == 3
        assert len(figure.axes[1].get_lines()) == 1
        plt.close(figure)

    def test_build_truncates_high_slip_side_of_output_peak(
        self,
        config: IConfig,
        logger: ILogger,
        peak_at_middle_slip_output_dto: Any,
    ) -> None:
        """出力ピークより大 slip 側を落として安定運転領域だけ描く。"""
        builder = SupplyGridOutputRatioFigureBuilder.create(
            config=config,
            logger=logger,
        )

        figure = builder.build(peak_at_middle_slip_output_dto)

        # slip=[0.05, 0.1, 0.3]、出力ピークは slip=0.1。ピーク含む小 slip 側
        # （0.05, 0.1）の 2 点だけが残り、大 slip 側（0.3）は落ちる。
        current_ratio_line = figure.axes[0].get_lines()[0]
        assert np.asarray(current_ratio_line.get_xdata()).size == 2
        plt.close(figure)

    def test_build_consolidates_legend_without_duplicate_labels(
        self,
        config: IConfig,
        logger: ILogger,
        supply_grid_output_dto: Any,
    ) -> None:
        """サブプロット横断の凡例を重複なく統合する。"""
        builder = SupplyGridOutputRatioFigureBuilder.create(
            config=config,
            logger=logger,
        )

        figure = builder.build(supply_grid_output_dto)

        assert len(figure.legends) == 1
        labels = [text.get_text() for text in figure.legends[0].get_texts()]
        assert labels == list(dict.fromkeys(labels))
        assert labels == [
            "Current ratio [%]",
            "Speed [rpm]",
            "PF [%]",
            "η [%]",
        ]
        plt.close(figure)
