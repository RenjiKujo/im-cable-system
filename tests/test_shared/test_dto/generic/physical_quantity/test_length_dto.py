"""FloatLengthDto の単体テスト。"""

from __future__ import annotations

import math

import pytest

from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    FloatLengthDto,
)


class TestFloatLengthDtoValidation:
    """FloatLengthDto.__post_init__ の境界値テスト。"""

    def test_accepts_zero(self) -> None:
        dto = FloatLengthDto(value=0.0, unit="m")
        assert dto.get_value() == 0.0

    def test_accepts_positive_finite(self) -> None:
        dto = FloatLengthDto(value=10.5, unit="ft")
        assert dto.get_value() == 10.5

    def test_rejects_nan(self) -> None:
        with pytest.raises(ValueError, match="finite"):
            FloatLengthDto(value=float("nan"), unit="m")

    def test_rejects_positive_inf(self) -> None:
        with pytest.raises(ValueError, match="finite"):
            FloatLengthDto(value=float("inf"), unit="m")

    def test_rejects_negative_inf(self) -> None:
        with pytest.raises(ValueError, match="finite"):
            FloatLengthDto(value=float("-inf"), unit="m")

    def test_rejects_negative_value(self) -> None:
        with pytest.raises(ValueError, match="non-negative"):
            FloatLengthDto(value=-1.0, unit="m")

    def test_rejects_invalid_unit(self) -> None:
        with pytest.raises(ValueError, match="invalid length unit"):
            FloatLengthDto(value=1.0, unit="invalid")

    @pytest.mark.parametrize(
        "value",
        [math.nan, math.inf, -math.inf],
    )
    def test_non_finite_values_raise_before_negative_check(
        self,
        value: float,
    ) -> None:
        with pytest.raises(ValueError, match="finite"):
            FloatLengthDto(value=value, unit="m")
