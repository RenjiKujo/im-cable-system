"""supply_grid ``series`` の単体テスト。"""

from __future__ import annotations

from typing import Any

import numpy as np
import pytest

from im_cable_system.engine.algorithm.output_algorithm.make_figure.supply_grid.series import (  # noqa: E501, PLC2701
    _build_simulated_slices,
    _has_required_axes,
    _power_factor_from_complex_power,
)


class TestSeries:
    """シミュレーション系列の派生と (f, V) スライス。"""

    def test_has_required_axes_true_for_supply_grid_layout(
        self,
        supply_grid_output_dto: Any,
    ) -> None:
        assert _has_required_axes(supply_grid_output_dto) is True

    def test_has_required_axes_false_for_slip_only_layout(
        self,
        slip_only_output_dto: Any,
    ) -> None:
        assert _has_required_axes(slip_only_output_dto) is False

    def test_power_factor_from_complex_power(self) -> None:
        power = np.array([100.0 + 0.0j, 0.0 + 0.0j], dtype=np.complex128)
        out = _power_factor_from_complex_power(power)
        np.testing.assert_allclose(out, np.array([1.0, 0.0], dtype=np.float64))

    def test_build_simulated_slices_returns_one_supply_condition(
        self,
        supply_grid_output_dto: Any,
    ) -> None:
        slices = _build_simulated_slices(supply_grid_output_dto)
        assert len(slices) == 1
        assert slices[0].frequency_hz == pytest.approx(60.0)
        assert slices[0].voltage_v == pytest.approx(460.0)
        assert slices[0].slip.size == 2
        assert slices[0].series.output_power_w.size == 2
