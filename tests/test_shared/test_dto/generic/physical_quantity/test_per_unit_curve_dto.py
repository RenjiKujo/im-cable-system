"""ArrayCurvePerUnitDto テスト。

無次元の比率（1.0 / 100% を超えても良い）を持つ DTO。
ratio 系の bounded DTO（efficiency / power_factor）と異なり上限なし。
"""

from __future__ import annotations

import numpy as np
import pytest

from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayCurvePerUnitDto,
)


class TestArrayCurvePerUnitDtoValidation:
    @pytest.mark.parametrize("unit", ["[-]", "%"])
    def test_valid_unit_accepted(self, unit: str) -> None:
        ArrayCurvePerUnitDto(value=np.array([1.0, 1.5]), unit=unit)

    def test_above_one_accepted(self) -> None:
        # 起動電流比など 1 を超える値が許容される
        ArrayCurvePerUnitDto(value=np.array([5.0]), unit="[-]")

    def test_empty_rejected(self) -> None:
        with pytest.raises(ValueError, match="must not be empty"):
            ArrayCurvePerUnitDto(value=np.array([]), unit="[-]")

    def test_negative_rejected(self) -> None:
        with pytest.raises(ValueError, match="non-negative"):
            ArrayCurvePerUnitDto(value=np.array([1.0, -0.1]), unit="[-]")

    def test_nan_rejected(self) -> None:
        with pytest.raises(ValueError, match="NaN/inf"):
            ArrayCurvePerUnitDto(value=np.array([1.0, np.nan]), unit="[-]")

    def test_invalid_unit_rejected(self) -> None:
        with pytest.raises(ValueError, match="invalid unit"):
            ArrayCurvePerUnitDto(value=np.array([1.0]), unit="bogus")


class TestArrayCurvePerUnitDtoConversion:
    def test_dimensionless_to_percent(self) -> None:
        dto = ArrayCurvePerUnitDto(value=np.array([0.5, 1.5]), unit="[-]")
        converted = dto.convert_to_unit("%")
        assert converted.get_unit() == "%"
        assert np.allclose(converted.get_value(), [50.0, 150.0])

    def test_percent_to_dimensionless(self) -> None:
        dto = ArrayCurvePerUnitDto(value=np.array([50.0, 150.0]), unit="%")
        converted = dto.convert_to_unit("[-]")
        assert np.allclose(converted.get_value(), [0.5, 1.5])

    def test_round_trip(self) -> None:
        arr = np.array([0.5, 1.0, 1.8])
        original = ArrayCurvePerUnitDto(value=arr, unit="[-]")
        round_trip = original.convert_to_unit("%").convert_to_unit("[-]")
        assert np.allclose(round_trip.get_value(), arr)

    def test_invalid_target_unit_rejected(self) -> None:
        dto = ArrayCurvePerUnitDto(value=np.array([1.0]), unit="[-]")
        with pytest.raises(ValueError, match="unsupported unit"):
            dto.convert_to_unit("bogus")
