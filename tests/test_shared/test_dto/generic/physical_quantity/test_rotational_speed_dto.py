"""FloatRotationalSpeedDto / ArrayRotationalSpeedDto テスト。"""

from __future__ import annotations

import math

import numpy as np
import pytest

from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayRotationalSpeedDto,
    FloatRotationalSpeedDto,
)


class TestFloatRotationalSpeedDtoValidation:
    @pytest.mark.parametrize("unit", ["rad/s", "rpm"])
    def test_valid_unit_accepted(self, unit: str) -> None:
        FloatRotationalSpeedDto(value=1.0, unit=unit)

    def test_zero_accepted(self) -> None:
        FloatRotationalSpeedDto(value=0.0, unit="rad/s")

    def test_negative_rejected(self) -> None:
        with pytest.raises(ValueError, match="non-negative"):
            FloatRotationalSpeedDto(value=-1.0, unit="rad/s")

    def test_nan_rejected(self) -> None:
        with pytest.raises(ValueError, match="NaN/inf"):
            FloatRotationalSpeedDto(value=math.nan, unit="rad/s")

    def test_inf_rejected(self) -> None:
        with pytest.raises(ValueError, match="NaN/inf"):
            FloatRotationalSpeedDto(value=math.inf, unit="rad/s")

    def test_invalid_unit_rejected(self) -> None:
        with pytest.raises(ValueError, match="invalid rotational speed unit"):
            FloatRotationalSpeedDto(value=1.0, unit="bogus")


class TestFloatRotationalSpeedDtoConversion:
    def test_rpm_to_rad_s(self) -> None:
        # 60 rpm = 2π rad/s
        dto = FloatRotationalSpeedDto(value=60.0, unit="rpm")
        base = dto.to_base_unit()
        assert base.get_unit() == "rad/s"
        assert base.get_value() == pytest.approx(2.0 * math.pi)

    def test_round_trip(self) -> None:
        original = FloatRotationalSpeedDto(value=1800.0, unit="rpm")
        round_trip = original.convert_to_unit("rad/s").convert_to_unit("rpm")
        assert round_trip.get_value() == pytest.approx(1800.0)


class TestArrayRotationalSpeedDtoValidation:
    def test_valid_accepted(self) -> None:
        ArrayRotationalSpeedDto(value=np.array([0.0, 1800.0]), unit="rpm")

    def test_empty_rejected(self) -> None:
        with pytest.raises(ValueError, match="must not be empty"):
            ArrayRotationalSpeedDto(value=np.array([]), unit="rpm")

    def test_nan_rejected(self) -> None:
        with pytest.raises(ValueError, match="NaN/inf"):
            ArrayRotationalSpeedDto(value=np.array([0.0, np.nan]), unit="rpm")

    def test_negative_rejected(self) -> None:
        with pytest.raises(ValueError, match="non-negative"):
            ArrayRotationalSpeedDto(value=np.array([-1.0]), unit="rpm")

    def test_invalid_unit_rejected(self) -> None:
        with pytest.raises(ValueError, match="invalid rotational speed unit"):
            ArrayRotationalSpeedDto(value=np.array([0.0]), unit="bogus")


class TestArrayRotationalSpeedDtoConversion:
    def test_round_trip(self) -> None:
        arr = np.array([1750.0, 1800.0])
        original = ArrayRotationalSpeedDto(value=arr, unit="rpm")
        round_trip = original.convert_to_unit("rad/s").convert_to_unit("rpm")
        assert np.allclose(round_trip.get_value(), arr)
