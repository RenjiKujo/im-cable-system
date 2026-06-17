"""ArrayTorqueDto テスト。

Generic DTO レベルでは NaN を許容するが（コンテナ DTO で厳格化）、inf は
常に拒否する。単位変換は Nm/N·m/kgf·m で実装。
"""

from __future__ import annotations

import numpy as np
import pytest

from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayTorqueDto,
)


class TestArrayTorqueDtoValidation:
    @pytest.mark.parametrize("unit", ["Nm", "N·m", "kgf·m"])
    def test_valid_unit_accepted(self, unit: str) -> None:
        ArrayTorqueDto(value=np.array([10.0]), unit=unit)

    def test_empty_rejected(self) -> None:
        with pytest.raises(ValueError, match="must not be empty"):
            ArrayTorqueDto(value=np.array([]), unit="Nm")

    def test_nan_allowed_at_generic_level(self) -> None:
        # NaN は Catalog DTO で初めて拒否されるので Generic では許容
        dto = ArrayTorqueDto(value=np.array([10.0, np.nan]), unit="Nm")
        assert np.isnan(dto.get_value()[1])

    def test_positive_inf_rejected(self) -> None:
        with pytest.raises(ValueError, match="must not contain inf"):
            ArrayTorqueDto(value=np.array([10.0, np.inf]), unit="Nm")

    def test_negative_inf_rejected(self) -> None:
        with pytest.raises(ValueError, match="must not contain inf"):
            ArrayTorqueDto(value=np.array([10.0, -np.inf]), unit="Nm")

    def test_invalid_unit_rejected(self) -> None:
        with pytest.raises(ValueError, match="invalid torque unit"):
            ArrayTorqueDto(value=np.array([10.0]), unit="bogus")


class TestArrayTorqueDtoConversion:
    def test_to_base_unit_from_kgfm(self) -> None:
        dto = ArrayTorqueDto(value=np.array([1.0]), unit="kgf·m")
        assert dto.to_base_unit().get_value()[0] == pytest.approx(9.80665)

    def test_round_trip(self) -> None:
        arr = np.array([10.0, 20.0])
        original = ArrayTorqueDto(value=arr, unit="Nm")
        round_trip = original.convert_to_unit("kgf·m").convert_to_unit("Nm")
        assert np.allclose(round_trip.get_value(), arr)

    def test_invalid_target_unit_rejected(self) -> None:
        dto = ArrayTorqueDto(value=np.array([10.0]), unit="Nm")
        with pytest.raises(ValueError, match="invalid torque unit"):
            dto.convert_to_unit("bogus")

    def test_synonym_units_equivalent(self) -> None:
        # 単位 "Nm" と "N·m" は同義
        a = ArrayTorqueDto(value=np.array([10.0]), unit="Nm").to_base_unit()
        b = ArrayTorqueDto(value=np.array([10.0]), unit="N·m").to_base_unit()
        assert np.allclose(a.get_value(), b.get_value())
