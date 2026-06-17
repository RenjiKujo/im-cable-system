"""FloatPowerFactorDto / ArrayPowerFactorDto テスト。"""

from __future__ import annotations

import math

import numpy as np
import pytest

from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayPowerFactorDto,
    FloatPowerFactorDto,
)


class TestFloatPowerFactorDtoValidation:
    @pytest.mark.parametrize("unit", ["-", "%"])
    def test_valid_unit_accepted(self, unit: str) -> None:
        FloatPowerFactorDto(value=0.5, unit=unit)

    def test_dimensionless_within_range(self) -> None:
        FloatPowerFactorDto(value=-1.0, unit="-")
        FloatPowerFactorDto(value=1.0, unit="-")

    def test_dimensionless_above_range_rejected(self) -> None:
        with pytest.raises(ValueError, match="-1.0 and 1.0"):
            FloatPowerFactorDto(value=1.5, unit="-")

    def test_dimensionless_below_range_rejected(self) -> None:
        with pytest.raises(ValueError, match="-1.0 and 1.0"):
            FloatPowerFactorDto(value=-1.5, unit="-")

    def test_percent_within_range(self) -> None:
        FloatPowerFactorDto(value=-100.0, unit="%")
        FloatPowerFactorDto(value=100.0, unit="%")

    def test_percent_out_of_range_rejected(self) -> None:
        with pytest.raises(ValueError, match="-100 and 100"):
            FloatPowerFactorDto(value=150.0, unit="%")

    def test_nan_rejected(self) -> None:
        with pytest.raises(ValueError, match="NaN/inf"):
            FloatPowerFactorDto(value=math.nan, unit="-")

    def test_invalid_unit_rejected(self) -> None:
        with pytest.raises(ValueError, match="invalid power factor unit"):
            FloatPowerFactorDto(value=0.5, unit="bogus")


class TestFloatPowerFactorDtoConversion:
    def test_dimensionless_to_percent(self) -> None:
        dto = FloatPowerFactorDto(value=0.8, unit="-")
        assert dto.convert_to_unit("%").get_value() == pytest.approx(80.0)

    def test_percent_to_dimensionless(self) -> None:
        dto = FloatPowerFactorDto(value=80.0, unit="%")
        assert dto.convert_to_unit("-").get_value() == pytest.approx(0.8)

    def test_round_trip(self) -> None:
        original = FloatPowerFactorDto(value=0.95, unit="-")
        round_trip = original.convert_to_unit("%").convert_to_unit("-")
        assert round_trip.get_value() == pytest.approx(0.95)

    def test_calculate_phase_angle(self) -> None:
        dto = FloatPowerFactorDto(value=1.0, unit="-")
        assert dto.calculate_phase_angle() == pytest.approx(0.0)
        dto = FloatPowerFactorDto(value=0.0, unit="-")
        assert dto.calculate_phase_angle() == pytest.approx(math.pi / 2)
        dto = FloatPowerFactorDto(value=-1.0, unit="-")
        assert dto.calculate_phase_angle() == pytest.approx(math.pi)


class TestArrayPowerFactorDtoValidation:
    def test_valid_accepted(self) -> None:
        ArrayPowerFactorDto(value=np.array([0.5, -0.5]), unit="-")

    def test_empty_rejected(self) -> None:
        with pytest.raises(ValueError, match="must not be empty"):
            ArrayPowerFactorDto(value=np.array([]), unit="-")

    def test_nan_rejected(self) -> None:
        with pytest.raises(ValueError, match="NaN/inf"):
            ArrayPowerFactorDto(value=np.array([0.5, np.nan]), unit="-")

    def test_dimensionless_out_of_range_rejected(self) -> None:
        with pytest.raises(ValueError, match="-1.0 and 1.0"):
            ArrayPowerFactorDto(value=np.array([0.5, 1.5]), unit="-")

    def test_percent_out_of_range_rejected(self) -> None:
        with pytest.raises(ValueError, match="-100 and 100"):
            ArrayPowerFactorDto(value=np.array([50.0, 150.0]), unit="%")


class TestArrayPowerFactorDtoConversion:
    def test_round_trip(self) -> None:
        arr = np.array([0.6, 0.95])
        original = ArrayPowerFactorDto(value=arr, unit="-")
        round_trip = original.convert_to_unit("%").convert_to_unit("-")
        assert np.allclose(round_trip.get_value(), arr)

    def test_calculate_phase_angle_array(self) -> None:
        dto = ArrayPowerFactorDto(value=np.array([1.0, 0.0, -1.0]), unit="-")
        angles = dto.calculate_phase_angle()
        assert angles[0] == pytest.approx(0.0)
        assert angles[1] == pytest.approx(math.pi / 2)
        assert angles[2] == pytest.approx(math.pi)
