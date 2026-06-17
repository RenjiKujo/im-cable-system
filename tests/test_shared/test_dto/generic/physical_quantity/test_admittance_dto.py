"""ArrayComplexAdmittanceDto テスト。

- ``__post_init__`` のバリデーション（empty/NaN/inf/unit）
- ``to_base_unit`` / ``convert_to_unit`` の往復一致
"""

from __future__ import annotations

import numpy as np
import pytest

from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexAdmittanceDto,
)


def _arr(values: list[complex]) -> np.ndarray:
    return np.array(values, dtype=np.complex128)


class TestArrayComplexAdmittanceDtoValidation:
    def test_valid_accepted(self) -> None:
        dto = ArrayComplexAdmittanceDto(
            value=_arr([1.0 + 2.0j, 3.0 + 0j]), unit="S"
        )
        assert dto.get_shape() == (2,)
        assert dto.get_ndim() == 1

    def test_empty_rejected(self) -> None:
        with pytest.raises(ValueError, match="must not be empty"):
            ArrayComplexAdmittanceDto(value=_arr([]), unit="S")

    def test_nan_rejected(self) -> None:
        with pytest.raises(ValueError, match="NaN/inf"):
            ArrayComplexAdmittanceDto(
                value=_arr([complex(np.nan, 0)]), unit="S"
            )

    @pytest.mark.parametrize("unit", ["S", "mS", "kS", "MS", "uS"])
    def test_valid_units(self, unit: str) -> None:
        ArrayComplexAdmittanceDto(value=_arr([1.0 + 0j]), unit=unit)

    def test_invalid_unit_rejected(self) -> None:
        with pytest.raises(ValueError, match="invalid admittance unit"):
            ArrayComplexAdmittanceDto(value=_arr([1.0 + 0j]), unit="bogus")


class TestArrayComplexAdmittanceDtoConversion:
    def test_round_trip(self) -> None:
        arr = _arr([1.0 + 0j, 2.0 + 0.5j])
        original = ArrayComplexAdmittanceDto(value=arr, unit="S")
        round_trip = original.convert_to_unit("mS").convert_to_unit("S")
        assert np.allclose(round_trip.get_value(), arr)

    def test_to_base_unit(self) -> None:
        dto = ArrayComplexAdmittanceDto(value=_arr([1.0 + 0j]), unit="kS")
        assert np.allclose(dto.to_base_unit().get_value(), [1000.0 + 0j])

    def test_extract_complex_components(self) -> None:
        dto = ArrayComplexAdmittanceDto(value=_arr([3.0 + 4.0j]), unit="S")
        assert dto.get_magnitude()[0] == pytest.approx(5.0)
        assert dto.get_real_part()[0] == pytest.approx(3.0)
        assert dto.get_imaginary_part()[0] == pytest.approx(4.0)
