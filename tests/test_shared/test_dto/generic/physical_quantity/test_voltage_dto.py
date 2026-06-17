"""FloatVoltageDto / ArrayComplexVoltageDto テスト。"""

from __future__ import annotations

import math

import numpy as np
import pytest

from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexVoltageDto,
    FloatVoltageDto,
)


class TestFloatVoltageDtoValidation:
    """FloatVoltageDto.__post_init__ テスト。"""

    @pytest.mark.parametrize("unit", ["mV", "V", "kV", "MV"])
    def test_valid_unit_accepted(self, unit: str) -> None:
        dto = FloatVoltageDto(value=100.0, unit=unit)
        assert dto.get_unit() == unit

    def test_zero_accepted(self) -> None:
        FloatVoltageDto(value=0.0, unit="V")

    def test_nan_rejected(self) -> None:
        with pytest.raises(ValueError, match="NaN/inf"):
            FloatVoltageDto(value=math.nan, unit="V")

    def test_inf_rejected(self) -> None:
        with pytest.raises(ValueError, match="NaN/inf"):
            FloatVoltageDto(value=math.inf, unit="V")

    def test_negative_rejected(self) -> None:
        with pytest.raises(ValueError, match="non-negative"):
            FloatVoltageDto(value=-1.0, unit="V")

    def test_invalid_unit_rejected(self) -> None:
        with pytest.raises(ValueError, match="invalid voltage unit"):
            FloatVoltageDto(value=1.0, unit="bogus")


class TestFloatVoltageDtoConversion:
    def test_to_base_unit(self) -> None:
        dto = FloatVoltageDto(value=2.5, unit="kV")
        assert dto.to_base_unit().get_value() == pytest.approx(2500.0)

    def test_round_trip(self) -> None:
        original = FloatVoltageDto(value=4.5, unit="kV")
        round_trip = original.convert_to_unit("V").convert_to_unit("kV")
        assert round_trip.get_value() == pytest.approx(4.5)

    def test_convert_to_invalid_unit_rejected(self) -> None:
        dto = FloatVoltageDto(value=1.0, unit="V")
        with pytest.raises(ValueError, match="invalid voltage unit"):
            dto.convert_to_unit("bogus")


class TestArrayComplexVoltageDtoValidation:
    """ArrayComplexVoltageDto.__post_init__ テスト。"""

    def test_valid_array_accepted(self) -> None:
        arr = np.array([1.0 + 0j, 2.0 + 1j], dtype=np.complex128)
        dto = ArrayComplexVoltageDto(value=arr, unit="V")
        assert dto.get_shape() == (2,)
        assert dto.get_ndim() == 1

    def test_non_ndarray_rejected(self) -> None:
        with pytest.raises(ValueError, match="must be a NumPy array"):
            ArrayComplexVoltageDto(value=[1.0 + 0j], unit="V")  # type: ignore[arg-type]

    def test_empty_array_rejected(self) -> None:
        with pytest.raises(ValueError, match="must not be empty"):
            ArrayComplexVoltageDto(
                value=np.array([], dtype=np.complex128), unit="V"
            )

    def test_nan_rejected(self) -> None:
        arr = np.array([complex(np.nan, 0)], dtype=np.complex128)
        with pytest.raises(ValueError, match="NaN/inf"):
            ArrayComplexVoltageDto(value=arr, unit="V")

    def test_inf_rejected(self) -> None:
        arr = np.array([complex(0, np.inf)], dtype=np.complex128)
        with pytest.raises(ValueError, match="NaN/inf"):
            ArrayComplexVoltageDto(value=arr, unit="V")

    def test_invalid_unit_rejected(self) -> None:
        arr = np.array([1.0 + 0j], dtype=np.complex128)
        with pytest.raises(ValueError, match="invalid voltage unit"):
            ArrayComplexVoltageDto(value=arr, unit="bogus")


class TestArrayComplexVoltageDtoConversion:
    def test_round_trip(self) -> None:
        arr = np.array([100.0 + 0j, 200.0 + 50j], dtype=np.complex128)
        original = ArrayComplexVoltageDto(value=arr, unit="V")
        round_trip = original.convert_to_unit("kV").convert_to_unit("V")
        assert np.allclose(round_trip.get_value(), arr)

    def test_magnitude_phase_real_imag(self) -> None:
        arr = np.array([3.0 + 4.0j], dtype=np.complex128)
        dto = ArrayComplexVoltageDto(value=arr, unit="V")
        assert dto.get_magnitude()[0] == pytest.approx(5.0)
        assert dto.get_phase()[0] == pytest.approx(math.atan2(4.0, 3.0))
        assert dto.get_real_part()[0] == pytest.approx(3.0)
        assert dto.get_imaginary_part()[0] == pytest.approx(4.0)
