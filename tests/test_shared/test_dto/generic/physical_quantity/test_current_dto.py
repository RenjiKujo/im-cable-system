"""FloatCurrentDto / ArrayComplexCurrentDto / ArrayCurrentMagnitudeDto テスト。

- ``__post_init__`` のバリデーション（finite/non-negative/unit）
- ``to_base_unit`` / ``convert_to_unit`` の往復一致
- magnitude / phase / real / imaginary 抽出
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexCurrentDto,
    ArrayCurrentMagnitudeDto,
    FloatCurrentDto,
)


class TestFloatCurrentDtoValidation:
    """FloatCurrentDto.__post_init__ テスト。"""

    @pytest.mark.parametrize("unit", ["mA", "A", "kA"])
    def test_valid_unit_accepted(self, unit: str) -> None:
        dto = FloatCurrentDto(value=1.0, unit=unit)
        assert dto.get_unit() == unit

    def test_zero_value_accepted(self) -> None:
        dto = FloatCurrentDto(value=0.0, unit="A")
        assert dto.get_value() == 0.0

    def test_nan_rejected(self) -> None:
        with pytest.raises(ValueError, match="NaN/inf"):
            FloatCurrentDto(value=math.nan, unit="A")

    def test_inf_rejected(self) -> None:
        with pytest.raises(ValueError, match="NaN/inf"):
            FloatCurrentDto(value=math.inf, unit="A")

    def test_negative_value_rejected(self) -> None:
        with pytest.raises(ValueError, match="non-negative"):
            FloatCurrentDto(value=-0.1, unit="A")

    def test_invalid_unit_rejected(self) -> None:
        with pytest.raises(ValueError, match="invalid current unit"):
            FloatCurrentDto(value=1.0, unit="bogus")


class TestFloatCurrentDtoConversion:
    """単位変換テスト。"""

    def test_to_base_unit_from_kiloampere(self) -> None:
        dto = FloatCurrentDto(value=2.5, unit="kA")
        base = dto.to_base_unit()
        assert base.get_unit() == "A"
        assert base.get_value() == pytest.approx(2500.0)

    def test_to_base_unit_from_milliampere(self) -> None:
        dto = FloatCurrentDto(value=750.0, unit="mA")
        base = dto.to_base_unit()
        assert base.get_value() == pytest.approx(0.75)

    def test_round_trip_unit_conversion(self) -> None:
        original = FloatCurrentDto(value=3.0, unit="A")
        round_trip = original.convert_to_unit("kA").convert_to_unit("A")
        assert round_trip.get_value() == pytest.approx(3.0)

    def test_convert_to_invalid_unit_rejected(self) -> None:
        dto = FloatCurrentDto(value=1.0, unit="A")
        with pytest.raises(ValueError, match="invalid current unit"):
            dto.convert_to_unit("bogus")


class TestArrayComplexCurrentDtoValidation:
    """ArrayComplexCurrentDto.__post_init__ テスト。"""

    def test_valid_complex_array_accepted(self) -> None:
        arr = np.array([1.0 + 2.0j, 3.0 + 0j], dtype=np.complex128)
        dto = ArrayComplexCurrentDto(value=arr, unit="A")
        assert dto.get_shape() == (2,)
        assert dto.get_ndim() == 1

    def test_empty_array_rejected(self) -> None:
        with pytest.raises(ValueError, match="must not be empty"):
            ArrayComplexCurrentDto(
                value=np.array([], dtype=np.complex128), unit="A"
            )

    def test_nan_in_real_rejected(self) -> None:
        arr = np.array([1.0 + 0j, complex(np.nan, 0)], dtype=np.complex128)
        with pytest.raises(ValueError, match="NaN/inf"):
            ArrayComplexCurrentDto(value=arr, unit="A")

    def test_nan_in_imag_rejected(self) -> None:
        arr = np.array([1.0 + 0j, complex(0, np.nan)], dtype=np.complex128)
        with pytest.raises(ValueError, match="NaN/inf"):
            ArrayComplexCurrentDto(value=arr, unit="A")

    def test_inf_in_real_rejected(self) -> None:
        arr = np.array([1.0 + 0j, complex(np.inf, 0)], dtype=np.complex128)
        with pytest.raises(ValueError, match="NaN/inf"):
            ArrayComplexCurrentDto(value=arr, unit="A")

    def test_invalid_unit_rejected(self) -> None:
        arr = np.array([1.0 + 0j], dtype=np.complex128)
        with pytest.raises(ValueError, match="invalid current unit"):
            ArrayComplexCurrentDto(value=arr, unit="bogus")


class TestArrayComplexCurrentDtoConversion:
    """単位変換と複素抽出テスト。"""

    def test_round_trip_unit_conversion(self) -> None:
        arr = np.array([1.0 + 2.0j], dtype=np.complex128)
        original = ArrayComplexCurrentDto(value=arr, unit="A")
        round_trip = original.convert_to_unit("kA").convert_to_unit("A")
        assert np.allclose(round_trip.get_value(), arr)

    def test_to_base_unit_scales_array(self) -> None:
        arr = np.array([1.0 + 0j, 2.0 + 0j], dtype=np.complex128)
        dto = ArrayComplexCurrentDto(value=arr, unit="kA")
        base = dto.to_base_unit()
        assert base.get_unit() == "A"
        assert np.allclose(base.get_value(), [1000.0, 2000.0])

    def test_magnitude_phase_real_imag(self) -> None:
        arr = np.array([3.0 + 4.0j], dtype=np.complex128)
        dto = ArrayComplexCurrentDto(value=arr, unit="A")
        assert dto.get_magnitude()[0] == pytest.approx(5.0)
        assert dto.get_phase()[0] == pytest.approx(math.atan2(4.0, 3.0))
        assert dto.get_real_part()[0] == pytest.approx(3.0)
        assert dto.get_imaginary_part()[0] == pytest.approx(4.0)


class TestArrayCurrentMagnitudeDtoValidation:
    """ArrayCurrentMagnitudeDto.__post_init__ テスト。"""

    def test_valid_array_accepted(self) -> None:
        dto = ArrayCurrentMagnitudeDto(
            value=np.array([1.0, 2.0], dtype=np.float64), unit="A"
        )
        assert dto.get_shape() == (2,)

    def test_empty_array_rejected(self) -> None:
        with pytest.raises(ValueError, match="must not be empty"):
            ArrayCurrentMagnitudeDto(
                value=np.array([], dtype=np.float64), unit="A"
            )

    def test_negative_element_rejected(self) -> None:
        with pytest.raises(ValueError, match="non-negative"):
            ArrayCurrentMagnitudeDto(
                value=np.array([1.0, -0.1], dtype=np.float64), unit="A"
            )

    def test_nan_rejected(self) -> None:
        with pytest.raises(ValueError, match="NaN/inf"):
            ArrayCurrentMagnitudeDto(
                value=np.array([1.0, np.nan], dtype=np.float64), unit="A"
            )

    def test_inf_rejected(self) -> None:
        with pytest.raises(ValueError, match="NaN/inf"):
            ArrayCurrentMagnitudeDto(
                value=np.array([1.0, np.inf], dtype=np.float64), unit="A"
            )

    def test_invalid_unit_rejected(self) -> None:
        with pytest.raises(ValueError, match="invalid current unit"):
            ArrayCurrentMagnitudeDto(
                value=np.array([1.0], dtype=np.float64), unit="bogus"
            )


class TestArrayCurrentMagnitudeDtoConversion:
    def test_round_trip(self) -> None:
        arr = np.array([10.0, 20.0], dtype=np.float64)
        original = ArrayCurrentMagnitudeDto(value=arr, unit="A")
        round_trip = original.convert_to_unit("mA").convert_to_unit("A")
        assert np.allclose(round_trip.get_value(), arr)
