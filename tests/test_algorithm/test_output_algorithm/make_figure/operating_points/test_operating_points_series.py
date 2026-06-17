"""operating_points ``series`` ヘルパの単体テスト。"""

from __future__ import annotations

from typing import Any

import numpy as np

from im_cable_system.engine.algorithm.output_algorithm.make_figure.operating_points.series import (  # noqa: E501, PLC2701
    _derive_series,
    _operating_point_count,
    _power_factor_from_complex_power,
)


class TestOperatingPointCount:
    """``_operating_point_count`` は参照軸直積の総数を返す。"""

    def test_count_matches_reference_length(
        self,
        operating_points_output_dto: Any,
    ) -> None:
        assert _operating_point_count(operating_points_output_dto) == 4


class TestPowerFactor:
    """``_power_factor_from_complex_power`` は ``Re(S)/|S|`` を返す。"""

    def test_zero_magnitude_maps_to_zero(self) -> None:
        power = np.array([0.0 + 0.0j, 3.0 + 4.0j], dtype=np.complex128)
        result = _power_factor_from_complex_power(power)
        assert result[0] == 0.0
        assert np.isclose(result[1], 0.6)


class TestDeriveSeries:
    """``_derive_series`` は長さ N の co-indexed な派生系列を返す。"""

    def test_series_shapes_and_values(
        self,
        operating_points_output_dto: Any,
    ) -> None:
        series = _derive_series(operating_points_output_dto)
        assert series.rotational_speed_rpm.shape == (4,)
        assert series.output_power_w.shape == (4,)
        assert series.frequency_hz is not None
        assert series.voltage_v is not None
        assert np.isclose(series.frequency_hz[0], 50.0)
        assert np.allclose(series.efficiency, np.linspace(0.7, 0.85, 4))

    def test_missing_supply_axes_yield_none(
        self,
        build_operating_points_output_dto: Any,
    ) -> None:
        output_dto = build_operating_points_output_dto(with_supply_axes=False)
        series = _derive_series(output_dto)
        assert series.frequency_hz is None
        assert series.voltage_v is None
        assert series.rotational_speed_rpm.shape == (4,)
