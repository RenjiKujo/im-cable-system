"""operating_points ``plotting`` ヘルパの単体テスト。"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402

from im_cable_system.engine.algorithm.output_algorithm.make_figure.operating_points.plotting import (  # noqa: E402, E501, PLC2701
    _attach_figure_legend,
    _legend_sort_key,
    _make_value_axis,
    _set_integer_xaxis,
)


class TestLegendSortKey:
    """``_legend_sort_key`` は量の定義順を返す。"""

    def test_known_labels_follow_quantity_order(self) -> None:
        assert _legend_sort_key("PF [-]") < _legend_sort_key("η [-]")
        assert _legend_sort_key("η [-]") < _legend_sort_key("Pout [W]")
        assert _legend_sort_key("Pout [W]") < _legend_sort_key("V [V]")

    def test_unknown_label_sorts_last(self) -> None:
        assert _legend_sort_key("unknown") >= _legend_sort_key("V [V]")


class TestMakeValueAxis:
    """``_make_value_axis`` は指定側へ outward に出した軸を作る。"""

    def test_right_axis_spine_position_and_visibility(self) -> None:
        _figure, ax_base = plt.subplots()
        ax = _make_value_axis(ax_base, side="right", offset=65)
        assert ax.spines["right"].get_position() == ("outward", 65)
        assert ax.spines["right"].get_visible() is True
        assert ax.spines["left"].get_visible() is False
        assert ax.yaxis.get_label_position() == "right"
        plt.close(_figure)

    def test_left_axis_spine_position_and_visibility(self) -> None:
        _figure, ax_base = plt.subplots()
        ax = _make_value_axis(ax_base, side="left", offset=120)
        assert ax.spines["left"].get_position() == ("outward", 120)
        assert ax.spines["left"].get_visible() is True
        assert ax.spines["right"].get_visible() is False
        assert ax.yaxis.get_label_position() == "left"
        plt.close(_figure)


class TestSetIntegerXAxis:
    """``_set_integer_xaxis`` は運転点 index 横軸を整える。"""

    def test_xlabel_and_xlim(self) -> None:
        _figure, ax = plt.subplots()
        _set_integer_xaxis(ax, num_points=5)
        assert ax.get_xlabel() == "Operating point"
        assert ax.get_xlim() == (-0.5, 4.5)
        plt.close(_figure)


class TestAttachFigureLegend:
    """``_attach_figure_legend`` は重複排除・量順で統合凡例を付与する。"""

    def test_legend_dedup_and_order(self) -> None:
        figure, ax = plt.subplots()
        ax.plot([0, 1], [0, 1], label="η [-]")
        ax.plot([0, 1], [1, 0], label="PF [-]")
        ax_twin = ax.twinx()
        ax_twin.plot([0, 1], [0, 2], label="Pout [W]")
        ax_twin.plot([0, 1], [2, 0], label="PF [-]")

        _attach_figure_legend(figure)

        assert len(figure.legends) == 1
        labels = [text.get_text() for text in figure.legends[0].get_texts()]
        assert labels == ["PF [-]", "η [-]", "Pout [W]"]
        plt.close(figure)

    def test_underscore_labels_are_excluded(self) -> None:
        figure, ax = plt.subplots()
        ax.plot([0, 1], [0, 1], label="_internal")
        ax.plot([0, 1], [1, 0], label="PF [-]")

        _attach_figure_legend(figure)

        labels = [text.get_text() for text in figure.legends[0].get_texts()]
        assert labels == ["PF [-]"]
        plt.close(figure)
