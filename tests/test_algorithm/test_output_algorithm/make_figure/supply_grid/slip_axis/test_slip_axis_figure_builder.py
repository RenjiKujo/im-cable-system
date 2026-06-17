"""SupplyGridSlipAxisFigureBuilder の描画契約テスト。"""

from __future__ import annotations

from typing import Any

import matplotlib.pyplot as plt

from im_cable_system.engine.algorithm.output_algorithm.make_figure.supply_grid.slip_axis.figure_builder import (  # noqa: E501
    SupplyGridSlipAxisFigureBuilder,
)
from im_cable_system.engine.shared.config import IConfig, ILogger


class TestSupplyGridSlipAxisFigureBuilder:
    """SupplyGridSlipAxisFigureBuilder.build の契約テスト。"""

    def test_build_returns_empty_figure_when_required_axes_are_missing(
        self,
        config: IConfig,
        logger: ILogger,
        slip_only_output_dto: Any,
    ) -> None:
        """必須軸不足時は空 Figure を返す。"""
        builder = SupplyGridSlipAxisFigureBuilder.create(
            config=config,
            logger=logger,
        )

        figure = builder.build(slip_only_output_dto)

        assert len(figure.axes) == 0

    def test_build_returns_slip_axis_grid_figure(
        self,
        config: IConfig,
        logger: ILogger,
        supply_grid_output_dto: Any,
    ) -> None:
        """(f, V) サブプロットと slip 横軸系列を描画する。"""
        builder = SupplyGridSlipAxisFigureBuilder.create(
            config=config,
            logger=logger,
        )

        figure = builder.build(supply_grid_output_dto)

        assert len(figure.axes) == 4
        assert figure.axes[0].get_title() == "f = 60 Hz, V = 460 V"
        assert len(figure.axes[0].get_lines()) == 2
        assert len(figure.axes[1].get_lines()) == 1
        assert len(figure.axes[2].get_lines()) == 1
        assert len(figure.axes[3].get_lines()) == 1
        plt.close(figure)

    def test_build_consolidates_legend_without_duplicate_labels(
        self,
        config: IConfig,
        logger: ILogger,
        supply_grid_output_dto: Any,
    ) -> None:
        """サブプロット横断の凡例を重複なく統合する。"""
        builder = SupplyGridSlipAxisFigureBuilder.create(
            config=config,
            logger=logger,
        )

        figure = builder.build(supply_grid_output_dto)

        assert len(figure.legends) == 1
        labels = [text.get_text() for text in figure.legends[0].get_texts()]
        assert labels == list(dict.fromkeys(labels))
        assert "T [N·m]" in labels
        plt.close(figure)
