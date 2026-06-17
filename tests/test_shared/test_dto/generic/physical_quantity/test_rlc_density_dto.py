"""RLC 線密度（per length）DTO テスト。

カバー対象:
    - FloatResistancePerLengthDto / FloatInductancePerLengthDto /
      FloatCapacitancePerLengthDto: 単位は ``Ω/m`` のような ``r/l`` 形式
    - FloatResistanceLengthDto: 単位は ``Ω*m`` のような ``r*l`` 形式
"""

from __future__ import annotations

import math

import pytest

from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    FloatCapacitancePerLengthDto,
    FloatInductancePerLengthDto,
    FloatResistanceLengthDto,
    FloatResistancePerLengthDto,
)


class TestFloatResistancePerLengthDto:
    def test_valid_si_unit(self) -> None:
        FloatResistancePerLengthDto(value=0.1, unit="Ω/m")
        FloatResistancePerLengthDto(value=100.0, unit="mΩ/km")

    def test_valid_field_unit(self) -> None:
        FloatResistancePerLengthDto(value=0.1, unit="Ω/ft")
        FloatResistancePerLengthDto(value=100.0, unit="mΩ/mi")

    def test_negative_rejected(self) -> None:
        with pytest.raises(ValueError, match="non-negative"):
            FloatResistancePerLengthDto(value=-0.1, unit="Ω/m")

    def test_nan_rejected(self) -> None:
        with pytest.raises(ValueError, match="must not be NaN"):
            FloatResistancePerLengthDto(value=math.nan, unit="Ω/m")

    def test_inf_accepted(self) -> None:
        # passive immittance DTO として inf を許容（下流でクランプ）。
        dto = FloatResistancePerLengthDto(value=math.inf, unit="Ω/m")
        assert math.isinf(dto.get_value())

    def test_no_slash_rejected(self) -> None:
        with pytest.raises(
            ValueError,
            match="resistance_unit/length_unit",
        ):
            FloatResistancePerLengthDto(value=0.1, unit="Ωm")

    def test_invalid_resistance_unit_rejected(self) -> None:
        with pytest.raises(ValueError, match="invalid resistance unit"):
            FloatResistancePerLengthDto(value=0.1, unit="bogus/m")

    def test_invalid_length_unit_rejected(self) -> None:
        with pytest.raises(ValueError, match="invalid length unit"):
            FloatResistancePerLengthDto(value=0.1, unit="Ω/bogus")

    def test_round_trip(self) -> None:
        original = FloatResistancePerLengthDto(value=0.1, unit="Ω/m")
        round_trip = original.convert_to_unit("mΩ/km").convert_to_unit("Ω/m")
        assert round_trip.get_value() == pytest.approx(0.1)

    def test_to_base_unit_si(self) -> None:
        # 100 Ω/km = 0.1 Ω/m
        dto = FloatResistancePerLengthDto(value=100.0, unit="Ω/km")
        assert dto.to_base_unit().get_value() == pytest.approx(0.1)


class TestFloatInductancePerLengthDto:
    def test_valid_si_unit(self) -> None:
        FloatInductancePerLengthDto(value=1e-3, unit="H/m")
        FloatInductancePerLengthDto(value=1.0, unit="mH/km")

    def test_negative_rejected(self) -> None:
        with pytest.raises(ValueError, match="non-negative"):
            FloatInductancePerLengthDto(value=-1.0, unit="H/m")

    def test_nan_rejected(self) -> None:
        with pytest.raises(ValueError, match="must not be NaN"):
            FloatInductancePerLengthDto(value=math.nan, unit="H/m")

    def test_inf_accepted(self) -> None:
        # passive immittance DTO として inf を許容（下流でクランプ）。
        dto = FloatInductancePerLengthDto(value=math.inf, unit="H/m")
        assert math.isinf(dto.get_value())

    def test_round_trip(self) -> None:
        original = FloatInductancePerLengthDto(value=1.0, unit="mH/km")
        round_trip = original.convert_to_unit("H/m").convert_to_unit("mH/km")
        assert round_trip.get_value() == pytest.approx(1.0)


class TestFloatCapacitancePerLengthDto:
    def test_valid_si_unit(self) -> None:
        FloatCapacitancePerLengthDto(value=1e-9, unit="F/m")
        FloatCapacitancePerLengthDto(value=100.0, unit="nF/km")

    def test_negative_rejected(self) -> None:
        with pytest.raises(ValueError, match="non-negative"):
            FloatCapacitancePerLengthDto(value=-1.0, unit="F/m")

    def test_nan_rejected(self) -> None:
        with pytest.raises(ValueError, match="must not be NaN"):
            FloatCapacitancePerLengthDto(value=math.nan, unit="F/m")

    def test_inf_accepted_as_ground_fault(self) -> None:
        # 接地キャパシタンスの inf は地絡を表すため許容する。
        dto = FloatCapacitancePerLengthDto(value=math.inf, unit="F/m")
        assert math.isinf(dto.get_value())

    def test_invalid_capacitance_unit_rejected(self) -> None:
        with pytest.raises(ValueError, match="invalid capacitance unit"):
            FloatCapacitancePerLengthDto(value=1.0, unit="bogus/m")

    def test_round_trip(self) -> None:
        original = FloatCapacitancePerLengthDto(value=100.0, unit="nF/km")
        round_trip = original.convert_to_unit("F/m").convert_to_unit("nF/km")
        assert round_trip.get_value() == pytest.approx(100.0)


class TestFloatResistanceLengthDto:
    def test_valid_si_unit(self) -> None:
        FloatResistanceLengthDto(value=1.0, unit="Ω*m")
        FloatResistanceLengthDto(value=100.0, unit="kΩ*km")

    def test_no_asterisk_rejected(self) -> None:
        with pytest.raises(
            ValueError,
            match="resistance_unit\\*length_unit",
        ):
            FloatResistanceLengthDto(value=1.0, unit="Ωm")

    def test_negative_rejected(self) -> None:
        with pytest.raises(ValueError, match="non-negative"):
            FloatResistanceLengthDto(value=-1.0, unit="Ω*m")

    def test_nan_rejected(self) -> None:
        with pytest.raises(ValueError, match="must not be NaN"):
            FloatResistanceLengthDto(value=math.nan, unit="Ω*m")

    def test_inf_accepted_as_ground_insulation(self) -> None:
        # 接地抵抗の inf は完全絶縁を表すため許容する。
        dto = FloatResistanceLengthDto(value=math.inf, unit="Ω*m")
        assert math.isinf(dto.get_value())

    def test_invalid_resistance_unit_rejected(self) -> None:
        with pytest.raises(ValueError, match="invalid resistance unit"):
            FloatResistanceLengthDto(value=1.0, unit="bogus*m")

    def test_invalid_length_unit_rejected(self) -> None:
        with pytest.raises(ValueError, match="invalid length unit"):
            FloatResistanceLengthDto(value=1.0, unit="Ω*bogus")

    def test_round_trip(self) -> None:
        original = FloatResistanceLengthDto(value=2.5, unit="kΩ*km")
        round_trip = original.convert_to_unit("Ω*m").convert_to_unit("kΩ*km")
        assert round_trip.get_value() == pytest.approx(2.5)

    def test_to_base_unit(self) -> None:
        # 1 kΩ*km = 1000 * 1000 = 1e6 Ω*m
        dto = FloatResistanceLengthDto(value=1.0, unit="kΩ*km")
        assert dto.to_base_unit().get_value() == pytest.approx(1e6)
