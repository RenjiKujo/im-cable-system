"""ArrayComplexImpedanceDto テスト。

- ``__post_init__`` のバリデーション（empty/NaN/inf/unit）
- ``to_base_unit`` / ``convert_to_unit`` の往復一致
- 複素抽出（magnitude/phase/real/imag）
"""

from __future__ import annotations

import numpy as np
import pytest

from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexImpedanceDto,
)


def _arr(values: list[complex]) -> np.ndarray:
    return np.array(values, dtype=np.complex128)


class TestArrayComplexImpedanceDtoValidation:
    """``__post_init__`` バリデーション。"""

    def test_valid_accepted(self) -> None:
        dto = ArrayComplexImpedanceDto(
            value=_arr([1.0 + 2.0j, 3.0 + 0j]), unit="Ω"
        )
        assert dto.get_shape() == (2,)
        assert dto.get_ndim() == 1

    def test_empty_rejected(self) -> None:
        with pytest.raises(ValueError, match="must not be empty"):
            ArrayComplexImpedanceDto(value=_arr([]), unit="Ω")

    def test_nan_rejected(self) -> None:
        with pytest.raises(ValueError, match="NaN/inf"):
            ArrayComplexImpedanceDto(value=_arr([complex(np.nan, 0)]), unit="Ω")

    def test_inf_rejected(self) -> None:
        with pytest.raises(ValueError, match="NaN/inf"):
            ArrayComplexImpedanceDto(value=_arr([complex(0, np.inf)]), unit="Ω")

    @pytest.mark.parametrize("unit", ["Ω", "mΩ", "kΩ", "MΩ"])
    def test_valid_units(self, unit: str) -> None:
        ArrayComplexImpedanceDto(value=_arr([1.0 + 0j]), unit=unit)

    def test_invalid_unit_rejected(self) -> None:
        with pytest.raises(ValueError, match="invalid impedance unit"):
            ArrayComplexImpedanceDto(value=_arr([1.0 + 0j]), unit="bogus")


class TestArrayComplexImpedanceDtoConversion:
    def test_round_trip(self) -> None:
        arr = _arr([10.0 + 0j, 20.0 + 5j])
        original = ArrayComplexImpedanceDto(value=arr, unit="Ω")
        round_trip = original.convert_to_unit("mΩ").convert_to_unit("Ω")
        assert np.allclose(round_trip.get_value(), arr)

    def test_to_base_unit(self) -> None:
        dto = ArrayComplexImpedanceDto(value=_arr([1.0 + 0j]), unit="kΩ")
        base = dto.to_base_unit()
        assert base.get_unit() == "Ω"
        assert np.allclose(base.get_value(), [1000.0 + 0j])

    def test_convert_to_invalid_rejected(self) -> None:
        dto = ArrayComplexImpedanceDto(value=_arr([1.0 + 0j]), unit="Ω")
        with pytest.raises(ValueError, match="invalid impedance unit"):
            dto.convert_to_unit("bogus")
