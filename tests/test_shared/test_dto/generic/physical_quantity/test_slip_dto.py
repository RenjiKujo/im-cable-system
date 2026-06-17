"""ArraySlipDto テスト。

NaN/inf 拒否、範囲（0..1 / 0..100）、単位変換を確認する。
slip の近接ゼロ判定・クランプ・イベント記録は二次イミタンスコンバーター側の
責務であり、本 DTO は入力状態の検証のみを行う（境界近傍値も受理する）。
"""

from __future__ import annotations

import numpy as np
import pytest

from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArraySlipDto,
)


class TestArraySlipDtoValidation:
    def test_valid_dimensionless_accepted(self) -> None:
        ArraySlipDto(value=np.array([0.0, 0.5, 1.0]), unit="-")

    def test_valid_percent_accepted(self) -> None:
        ArraySlipDto(value=np.array([0.0, 50.0, 100.0]), unit="%")

    def test_empty_rejected(self) -> None:
        with pytest.raises(ValueError, match="must not be empty"):
            ArraySlipDto(value=np.array([]), unit="-")

    def test_nan_rejected(self) -> None:
        with pytest.raises(ValueError, match="NaN/inf"):
            ArraySlipDto(value=np.array([0.5, np.nan]), unit="-")

    def test_inf_rejected(self) -> None:
        with pytest.raises(ValueError, match="NaN/inf"):
            ArraySlipDto(value=np.array([np.inf]), unit="-")

    def test_dimensionless_out_of_range_rejected(self) -> None:
        with pytest.raises(ValueError, match="between 0.0 and 1.0"):
            ArraySlipDto(value=np.array([0.5, 1.5]), unit="-")

    def test_dimensionless_negative_rejected(self) -> None:
        with pytest.raises(ValueError, match="between 0.0 and 1.0"):
            ArraySlipDto(value=np.array([0.5, -0.1]), unit="-")

    def test_percent_out_of_range_rejected(self) -> None:
        with pytest.raises(ValueError, match="between 0 and 100"):
            ArraySlipDto(value=np.array([50.0, 150.0]), unit="%")

    def test_invalid_unit_rejected(self) -> None:
        with pytest.raises(ValueError, match="slip unit must be"):
            ArraySlipDto(value=np.array([0.5]), unit="bogus")


class TestArraySlipDtoConversion:
    def test_dimensionless_to_percent(self) -> None:
        dto = ArraySlipDto(value=np.array([0.5]), unit="-")
        converted = dto.convert_to_unit("%")
        assert converted.get_unit() == "%"
        assert converted.get_value()[0] == pytest.approx(50.0)

    def test_percent_to_dimensionless(self) -> None:
        dto = ArraySlipDto(value=np.array([50.0]), unit="%")
        converted = dto.convert_to_unit("-")
        assert converted.get_value()[0] == pytest.approx(0.5)

    def test_round_trip(self) -> None:
        arr = np.array([0.05, 0.5, 0.95])
        original = ArraySlipDto(value=arr, unit="-")
        round_trip = original.convert_to_unit("%").convert_to_unit("-")
        assert np.allclose(round_trip.get_value(), arr)

    def test_same_unit_returns_self(self) -> None:
        dto = ArraySlipDto(value=np.array([0.5]), unit="-")
        assert dto.convert_to_unit("-") is dto

    def test_invalid_target_unit_rejected(self) -> None:
        dto = ArraySlipDto(value=np.array([0.5]), unit="-")
        with pytest.raises(ValueError, match="invalid slip unit"):
            dto.convert_to_unit("bogus")


class TestArraySlipDtoNearBoundaryAccepted:
    """境界近傍値（0/1 近傍）も入力として受理されることを確認。"""

    def test_near_zero_accepted(self) -> None:
        ArraySlipDto(value=np.array([1e-15, 0.5]), unit="-")

    def test_near_one_accepted(self) -> None:
        ArraySlipDto(value=np.array([0.5, 1.0 - 1e-15]), unit="-")
