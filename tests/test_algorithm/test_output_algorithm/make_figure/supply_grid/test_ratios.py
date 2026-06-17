"""supply_grid ``ratios`` の単体テスト。"""

from __future__ import annotations

from typing import Any

import numpy as np
import pytest

from im_cable_system.engine.algorithm.output_algorithm.make_figure.supply_grid.ratios import (  # noqa: E501, PLC2701
    _current_ratio_percent,
    _output_ratio_percent,
    _ratio_to_percent,
)
from im_cable_system.engine.algorithm.output_algorithm.make_figure.supply_grid.series import (  # noqa: E501, PLC2701
    _SupplyGridSeries,
)


def _series() -> _SupplyGridSeries:
    return _SupplyGridSeries(
        output_power_w=np.array([100.0, 200.0], dtype=np.float64),
        input_current_magnitude_a=np.array([1.0, 2.0], dtype=np.float64),
        power_factor=np.array([0.8, 0.9], dtype=np.float64),
        efficiency=np.array([0.85, 0.95], dtype=np.float64),
        torque_nm=np.array([5.0, 6.0], dtype=np.float64),
        rotational_speed_rpm=np.array([1800.0, 1750.0], dtype=np.float64),
    )


class TestRatios:
    """定格比系列の算出。"""

    def test_output_and_current_ratio_percent(
        self,
        supply_grid_output_dto: Any,
    ) -> None:
        series = _series()
        np.testing.assert_allclose(
            _output_ratio_percent(series, supply_grid_output_dto),
            np.array([50.0, 100.0], dtype=np.float64),
        )
        np.testing.assert_allclose(
            _current_ratio_percent(series, supply_grid_output_dto),
            np.array([50.0, 100.0], dtype=np.float64),
        )

    def test_ratio_to_percent(self) -> None:
        np.testing.assert_allclose(
            _ratio_to_percent(np.array([0.8, 0.9])),
            np.array([80.0, 90.0], dtype=np.float64),
        )

    def test_raises_when_nameplate_power_non_positive(
        self,
        supply_grid_output_dto: Any,
    ) -> None:
        supply_grid_output_dto.im.im_series.nameplate_power = type(
            supply_grid_output_dto.im.im_series.nameplate_power
        )(value=0.0, unit="W")
        with pytest.raises(ValueError, match="nameplate_power"):
            _output_ratio_percent(_series(), supply_grid_output_dto)
