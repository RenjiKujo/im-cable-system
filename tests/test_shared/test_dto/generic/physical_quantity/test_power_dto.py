"""Power 系 DTO テスト。

カバー対象:
    - FloatActivePowerDto / FloatReactivePowerDto / FloatApparentPowerDto
    - ArrayActivePowerDto / ArrayReactivePowerDto / ArrayApparentPowerDto
    - ArrayComplexPowerDto（各 array 変換）

NOTE:
    力率計算（旧 ``ArrayComplexPowerDto.calculate_power_factor``）は数値ガード・
    数値安定化イベント記録を伴うため、DTO から domain 層
    （``physics.calculate_power_factor``）へ移設した。テストは
    ``tests/test_domain/test_physics/test_characteristic.py`` を参照。
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayActivePowerDto,
    ArrayApparentPowerDto,
    ArrayComplexPowerDto,
    ArrayReactivePowerDto,
    FloatActivePowerDto,
    FloatApparentPowerDto,
    FloatReactivePowerDto,
)


class TestFloatActivePowerDto:
    """FloatActivePowerDto バリデーションと変換。"""

    @pytest.mark.parametrize("unit", ["W", "kW", "MW", "HP"])
    def test_valid_unit_accepted(self, unit: str) -> None:
        FloatActivePowerDto(value=1.0, unit=unit)

    def test_negative_rejected(self) -> None:
        with pytest.raises(ValueError, match="non-negative"):
            FloatActivePowerDto(value=-1.0, unit="W")

    def test_nan_rejected(self) -> None:
        with pytest.raises(ValueError, match="NaN/inf"):
            FloatActivePowerDto(value=math.nan, unit="W")

    def test_inf_rejected(self) -> None:
        with pytest.raises(ValueError, match="NaN/inf"):
            FloatActivePowerDto(value=math.inf, unit="W")

    def test_invalid_unit_rejected(self) -> None:
        with pytest.raises(ValueError, match="invalid active power unit"):
            FloatActivePowerDto(value=1.0, unit="bogus")

    def test_round_trip(self) -> None:
        original = FloatActivePowerDto(value=2.5, unit="kW")
        round_trip = original.convert_to_unit("W").convert_to_unit("kW")
        assert round_trip.get_value() == pytest.approx(2.5)

    def test_hp_conversion(self) -> None:
        dto = FloatActivePowerDto(value=1.0, unit="HP")
        assert dto.to_base_unit().get_value() == pytest.approx(745.699872)


class TestFloatReactivePowerDto:
    @pytest.mark.parametrize("unit", ["var", "kvar", "Mvar"])
    def test_valid_unit_accepted(self, unit: str) -> None:
        FloatReactivePowerDto(value=1.0, unit=unit)

    def test_negative_rejected(self) -> None:
        with pytest.raises(ValueError, match="non-negative"):
            FloatReactivePowerDto(value=-1.0, unit="var")

    def test_round_trip(self) -> None:
        original = FloatReactivePowerDto(value=3.0, unit="kvar")
        round_trip = original.convert_to_unit("var").convert_to_unit("kvar")
        assert round_trip.get_value() == pytest.approx(3.0)


class TestFloatApparentPowerDto:
    @pytest.mark.parametrize("unit", ["VA", "kVA", "MVA"])
    def test_valid_unit_accepted(self, unit: str) -> None:
        FloatApparentPowerDto(value=1.0, unit=unit)

    def test_negative_rejected(self) -> None:
        with pytest.raises(ValueError, match="non-negative"):
            FloatApparentPowerDto(value=-1.0, unit="VA")


class TestArrayActivePowerDto:
    def test_valid_array_accepted(self) -> None:
        ArrayActivePowerDto(value=np.array([1.0, 2.0]), unit="W")

    def test_empty_rejected(self) -> None:
        with pytest.raises(ValueError, match="must not be empty"):
            ArrayActivePowerDto(value=np.array([]), unit="W")

    def test_nan_rejected(self) -> None:
        with pytest.raises(ValueError, match="NaN/inf"):
            ArrayActivePowerDto(value=np.array([1.0, np.nan]), unit="W")

    def test_round_trip(self) -> None:
        arr = np.array([1.0, 2.0])
        original = ArrayActivePowerDto(value=arr, unit="W")
        round_trip = original.convert_to_unit("kW").convert_to_unit("W")
        assert np.allclose(round_trip.get_value(), arr)

    def test_invalid_unit_rejected_on_convert(self) -> None:
        dto = ArrayActivePowerDto(value=np.array([1.0]), unit="W")
        with pytest.raises(ValueError, match="invalid active power unit"):
            dto.convert_to_unit("bogus")

    def test_from_base_value_factory(self) -> None:
        dto = ArrayActivePowerDto.from_base_value(
            value=np.array([1000.0]), target_unit="kW"
        )
        assert dto.get_unit() == "kW"
        assert dto.get_value()[0] == pytest.approx(1.0)


class TestArrayReactivePowerDto:
    def test_valid_array_accepted(self) -> None:
        ArrayReactivePowerDto(value=np.array([1.0]), unit="var")

    def test_round_trip(self) -> None:
        arr = np.array([1.0, 2.0])
        original = ArrayReactivePowerDto(value=arr, unit="var")
        round_trip = original.convert_to_unit("kvar").convert_to_unit("var")
        assert np.allclose(round_trip.get_value(), arr)


class TestArrayApparentPowerDto:
    def test_valid_array_accepted(self) -> None:
        ArrayApparentPowerDto(value=np.array([1.0]), unit="VA")

    def test_round_trip(self) -> None:
        arr = np.array([1.0, 2.0])
        original = ArrayApparentPowerDto(value=arr, unit="VA")
        round_trip = original.convert_to_unit("kVA").convert_to_unit("VA")
        assert np.allclose(round_trip.get_value(), arr)


class TestArrayComplexPowerDto:
    def test_valid_complex_accepted(self) -> None:
        arr = np.array([100.0 + 50.0j], dtype=np.complex128)
        ArrayComplexPowerDto(value=arr, unit="VA")

    def test_invalid_unit_rejected(self) -> None:
        arr = np.array([1.0 + 0j], dtype=np.complex128)
        with pytest.raises(ValueError, match="invalid power unit"):
            ArrayComplexPowerDto(value=arr, unit="W")

    def test_to_active_power_array(self) -> None:
        arr = np.array([100.0 + 50.0j], dtype=np.complex128)
        dto = ArrayComplexPowerDto(value=arr, unit="VA")
        active = dto.to_active_power_array(unit="W")
        assert active.get_value()[0] == pytest.approx(100.0)

    def test_to_reactive_power_array(self) -> None:
        arr = np.array([100.0 + 50.0j], dtype=np.complex128)
        dto = ArrayComplexPowerDto(value=arr, unit="VA")
        reactive = dto.to_reactive_power_array(unit="var")
        assert reactive.get_value()[0] == pytest.approx(50.0)

    def test_to_apparent_power_array(self) -> None:
        arr = np.array([3.0 + 4.0j], dtype=np.complex128)
        dto = ArrayComplexPowerDto(value=arr, unit="VA")
        apparent = dto.to_apparent_power_array(unit="VA")
        assert apparent.get_value()[0] == pytest.approx(5.0)
