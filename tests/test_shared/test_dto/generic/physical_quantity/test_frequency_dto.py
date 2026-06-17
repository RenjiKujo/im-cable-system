"""FloatFrequencyDto / ArrayFrequencyDto テスト。"""

from __future__ import annotations

import math

import numpy as np
import pytest

from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayFrequencyDto,
    FloatFrequencyDto,
)


class TestFloatFrequencyDtoValidation:
    """FloatFrequencyDto.__post_init__ テスト。"""

    @pytest.mark.parametrize("unit", ["Hz", "kHz", "MHz"])
    def test_valid_unit_accepted(self, unit: str) -> None:
        FloatFrequencyDto(value=1.0, unit=unit)

    def test_zero_rejected(self) -> None:
        with pytest.raises(ValueError, match="greater than zero"):
            FloatFrequencyDto(value=0.0, unit="Hz")

    def test_negative_rejected(self) -> None:
        with pytest.raises(ValueError, match="greater than zero"):
            FloatFrequencyDto(value=-1.0, unit="Hz")

    def test_nan_rejected(self) -> None:
        with pytest.raises(ValueError, match="NaN/inf"):
            FloatFrequencyDto(value=math.nan, unit="Hz")

    def test_inf_rejected(self) -> None:
        with pytest.raises(ValueError, match="NaN/inf"):
            FloatFrequencyDto(value=math.inf, unit="Hz")

    def test_invalid_unit_rejected(self) -> None:
        with pytest.raises(ValueError, match="invalid frequency unit"):
            FloatFrequencyDto(value=1.0, unit="bogus")


class TestFloatFrequencyDtoConversion:
    def test_to_base_unit_from_kilohertz(self) -> None:
        dto = FloatFrequencyDto(value=2.5, unit="kHz")
        assert dto.to_base_unit().get_value() == pytest.approx(2500.0)

    def test_round_trip(self) -> None:
        original = FloatFrequencyDto(value=60.0, unit="Hz")
        round_trip = original.convert_to_unit("kHz").convert_to_unit("Hz")
        assert round_trip.get_value() == pytest.approx(60.0)

    def test_convert_to_invalid_unit_rejected(self) -> None:
        dto = FloatFrequencyDto(value=1.0, unit="Hz")
        with pytest.raises(ValueError, match="invalid frequency unit"):
            dto.convert_to_unit("bogus")


class TestArrayFrequencyDtoValidation:
    """ArrayFrequencyDto.__post_init__ テスト。"""

    def test_valid_array_accepted(self) -> None:
        arr = np.array([50.0, 60.0], dtype=np.float64)
        dto = ArrayFrequencyDto(value=arr, unit="Hz")
        assert dto.get_shape() == (2,)

    def test_empty_rejected(self) -> None:
        with pytest.raises(ValueError, match="must not be empty"):
            ArrayFrequencyDto(value=np.array([], dtype=np.float64), unit="Hz")

    def test_nan_rejected(self) -> None:
        with pytest.raises(ValueError, match="NaN/inf"):
            ArrayFrequencyDto(
                value=np.array([50.0, np.nan], dtype=np.float64), unit="Hz"
            )

    def test_inf_rejected(self) -> None:
        with pytest.raises(ValueError, match="NaN/inf"):
            ArrayFrequencyDto(
                value=np.array([np.inf], dtype=np.float64), unit="Hz"
            )

    def test_zero_rejected(self) -> None:
        with pytest.raises(ValueError, match="greater than zero"):
            ArrayFrequencyDto(
                value=np.array([0.0], dtype=np.float64), unit="Hz"
            )

    def test_negative_rejected(self) -> None:
        with pytest.raises(ValueError, match="greater than zero"):
            ArrayFrequencyDto(
                value=np.array([-1.0], dtype=np.float64), unit="Hz"
            )

    def test_invalid_unit_rejected(self) -> None:
        with pytest.raises(ValueError, match="invalid frequency unit"):
            ArrayFrequencyDto(
                value=np.array([50.0], dtype=np.float64), unit="bogus"
            )


class TestArrayFrequencyDtoConversion:
    def test_round_trip(self) -> None:
        arr = np.array([50.0, 60.0], dtype=np.float64)
        original = ArrayFrequencyDto(value=arr, unit="Hz")
        round_trip = original.convert_to_unit("kHz").convert_to_unit("Hz")
        assert np.allclose(round_trip.get_value(), arr)
