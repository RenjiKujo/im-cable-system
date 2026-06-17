"""FloatEfficiencyDto / ArrayEfficiencyDto テスト。"""

from __future__ import annotations

import math

import numpy as np
import pytest

from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayEfficiencyDto,
    FloatEfficiencyDto,
)


class TestFloatEfficiencyDtoValidation:
    @pytest.mark.parametrize("unit", ["-", "%"])
    def test_valid_unit_accepted(self, unit: str) -> None:
        FloatEfficiencyDto(value=0.5, unit=unit)

    def test_dimensionless_boundary(self) -> None:
        FloatEfficiencyDto(value=0.0, unit="-")
        FloatEfficiencyDto(value=1.0, unit="-")

    def test_dimensionless_above_one_rejected(self) -> None:
        with pytest.raises(ValueError, match="0.0 and 1.0"):
            FloatEfficiencyDto(value=1.5, unit="-")

    def test_negative_rejected(self) -> None:
        with pytest.raises(ValueError, match="0.0 and 1.0"):
            FloatEfficiencyDto(value=-0.1, unit="-")

    def test_percent_out_of_range_rejected(self) -> None:
        with pytest.raises(ValueError, match="0 and 100"):
            FloatEfficiencyDto(value=150.0, unit="%")

    def test_nan_rejected(self) -> None:
        with pytest.raises(ValueError, match="NaN/inf"):
            FloatEfficiencyDto(value=math.nan, unit="-")

    def test_invalid_unit_rejected(self) -> None:
        with pytest.raises(ValueError, match="invalid efficiency unit"):
            FloatEfficiencyDto(value=0.5, unit="bogus")


class TestFloatEfficiencyDtoConversion:
    def test_dimensionless_to_percent(self) -> None:
        dto = FloatEfficiencyDto(value=0.85, unit="-")
        assert dto.convert_to_unit("%").get_value() == pytest.approx(85.0)

    def test_percent_to_dimensionless(self) -> None:
        dto = FloatEfficiencyDto(value=85.0, unit="%")
        assert dto.convert_to_unit("-").get_value() == pytest.approx(0.85)

    def test_round_trip(self) -> None:
        original = FloatEfficiencyDto(value=0.5, unit="-")
        round_trip = original.convert_to_unit("%").convert_to_unit("-")
        assert round_trip.get_value() == pytest.approx(0.5)

    def test_same_unit_returns_self(self) -> None:
        dto = FloatEfficiencyDto(value=0.5, unit="-")
        assert dto.convert_to_unit("-") is dto


class TestArrayEfficiencyDtoValidation:
    def test_valid_accepted(self) -> None:
        ArrayEfficiencyDto(value=np.array([0.5, 0.9]), unit="-")

    def test_empty_rejected(self) -> None:
        with pytest.raises(ValueError, match="must not be empty"):
            ArrayEfficiencyDto(value=np.array([]), unit="-")

    def test_nan_rejected(self) -> None:
        with pytest.raises(ValueError, match="NaN/inf"):
            ArrayEfficiencyDto(value=np.array([0.5, np.nan]), unit="-")

    def test_dimensionless_above_one_rejected(self) -> None:
        with pytest.raises(ValueError, match="0.0 and 1.0"):
            ArrayEfficiencyDto(value=np.array([0.5, 1.5]), unit="-")

    def test_percent_out_of_range_rejected(self) -> None:
        with pytest.raises(ValueError, match="0 and 100"):
            ArrayEfficiencyDto(value=np.array([50.0, 150.0]), unit="%")


class TestArrayEfficiencyDtoConversion:
    def test_round_trip(self) -> None:
        arr = np.array([0.5, 0.9])
        original = ArrayEfficiencyDto(value=arr, unit="-")
        round_trip = original.convert_to_unit("%").convert_to_unit("-")
        assert np.allclose(round_trip.get_value(), arr)
