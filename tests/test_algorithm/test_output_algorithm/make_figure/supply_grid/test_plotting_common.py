"""supply_grid ``plotting_common`` の純粋ヘルパの単体テスト。"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, cast

import pytest

from im_cable_system.engine.algorithm.output_algorithm.make_figure.supply_grid.plotting_common import (  # noqa: E501, PLC2701
    _CATALOG_LABEL_PREFIX,
    _legend_sort_key,
    _output_display_name,
    _subplot_layout,
    _subplot_title,
)


class TestSubplotLayout:
    """``_subplot_layout`` はサブプロット数から格子を返す。"""

    @pytest.mark.parametrize(
        ("num_plots", "expected"),
        [
            (0, (1, 1)),
            (1, (1, 1)),
            (2, (1, 2)),
            (3, (2, 2)),
            (4, (2, 2)),
            (5, (2, 3)),
            (9, (3, 3)),
        ],
    )
    def test_layout(
        self,
        num_plots: int,
        expected: tuple[int, int],
    ) -> None:
        assert _subplot_layout(num_plots) == expected


class TestLegendSortKey:
    """``_legend_sort_key`` は measured→catalog・量順を返す。"""

    def test_measured_sorts_before_catalog(self) -> None:
        measured = _legend_sort_key("PF [-]")
        catalog = _legend_sort_key(f"{_CATALOG_LABEL_PREFIX}PF [-]")
        assert measured < catalog

    def test_quantity_order_within_measured(self) -> None:
        assert _legend_sort_key("Pout [W]") < _legend_sort_key("PF [-]")


class TestSubplotTitle:
    """``_subplot_title`` は (f, V) を整形する。"""

    def test_title_format(self) -> None:
        supply_slice = SimpleNamespace(frequency_hz=60.0, voltage_v=460.0)
        assert _subplot_title(cast(Any, supply_slice)) == "f = 60 Hz, V = 460 V"


class TestOutputDisplayName:
    """``_output_display_name`` は ``name.get_base()``（候補一意化接尾辞を
    除いた表示専用の基底名）を返す。"""

    def test_returns_base_from_name(self) -> None:
        output_dto = SimpleNamespace(
            name=SimpleNamespace(get_base=lambda: "sys-a")
        )
        assert _output_display_name(cast(Any, output_dto)) == "sys-a"
