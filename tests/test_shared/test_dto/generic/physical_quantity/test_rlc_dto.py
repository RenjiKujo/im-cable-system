"""RLC スカラ DTO テスト（FloatResistance/Conductance/Inductance/Capacitance）。"""

from __future__ import annotations

import math

import pytest

from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    FloatCapacitanceDto,
    FloatConductanceDto,
    FloatInductanceDto,
    FloatResistanceDto,
)


class TestFloatResistanceDto:
    @pytest.mark.parametrize("unit", ["mΩ", "Ω", "kΩ", "MΩ"])
    def test_valid_unit_accepted(self, unit: str) -> None:
        FloatResistanceDto(value=1.0, unit=unit)

    def test_negative_rejected(self) -> None:
        with pytest.raises(ValueError, match="non-negative"):
            FloatResistanceDto(value=-1.0, unit="Ω")

    def test_nan_rejected(self) -> None:
        with pytest.raises(ValueError, match="must not be NaN"):
            FloatResistanceDto(value=math.nan, unit="Ω")

    def test_inf_accepted(self) -> None:
        # 開放/完全絶縁は inf 抵抗で表し、下流でクランプされる。
        dto = FloatResistanceDto(value=math.inf, unit="Ω")
        assert math.isinf(dto.get_value())

    def test_invalid_unit_rejected(self) -> None:
        with pytest.raises(ValueError, match="invalid resistance unit"):
            FloatResistanceDto(value=1.0, unit="bogus")

    def test_round_trip(self) -> None:
        original = FloatResistanceDto(value=2.5, unit="kΩ")
        round_trip = original.convert_to_unit("Ω").convert_to_unit("kΩ")
        assert round_trip.get_value() == pytest.approx(2.5)

    def test_to_base_unit(self) -> None:
        dto = FloatResistanceDto(value=1.0, unit="kΩ")
        assert dto.to_base_unit().get_value() == pytest.approx(1000.0)


class TestFloatConductanceDto:
    @pytest.mark.parametrize("unit", ["uS", "mS", "S", "kS", "MS"])
    def test_valid_unit_accepted(self, unit: str) -> None:
        FloatConductanceDto(value=1.0, unit=unit)

    def test_negative_rejected(self) -> None:
        with pytest.raises(ValueError, match="non-negative"):
            FloatConductanceDto(value=-1.0, unit="S")

    def test_nan_rejected(self) -> None:
        with pytest.raises(ValueError, match="must not be NaN"):
            FloatConductanceDto(value=math.nan, unit="S")

    def test_inf_accepted(self) -> None:
        # 完全導体/短絡は inf コンダクタンスで表し、下流でクランプされる。
        dto = FloatConductanceDto(value=math.inf, unit="S")
        assert math.isinf(dto.get_value())

    def test_round_trip(self) -> None:
        original = FloatConductanceDto(value=1.5, unit="mS")
        round_trip = original.convert_to_unit("S").convert_to_unit("mS")
        assert round_trip.get_value() == pytest.approx(1.5)

    def test_invalid_unit_rejected(self) -> None:
        with pytest.raises(ValueError, match="invalid conductance unit"):
            FloatConductanceDto(value=1.0, unit="bogus")


class TestFloatInductanceDto:
    @pytest.mark.parametrize("unit", ["mH", "H", "kH", "MH"])
    def test_valid_unit_accepted(self, unit: str) -> None:
        FloatInductanceDto(value=1.0, unit=unit)

    def test_negative_rejected(self) -> None:
        with pytest.raises(ValueError, match="non-negative"):
            FloatInductanceDto(value=-1.0, unit="H")

    def test_nan_rejected(self) -> None:
        with pytest.raises(ValueError, match="must not be NaN"):
            FloatInductanceDto(value=math.nan, unit="H")

    def test_inf_accepted(self) -> None:
        dto = FloatInductanceDto(value=math.inf, unit="H")
        assert math.isinf(dto.get_value())

    def test_round_trip(self) -> None:
        original = FloatInductanceDto(value=10.0, unit="mH")
        round_trip = original.convert_to_unit("H").convert_to_unit("mH")
        assert round_trip.get_value() == pytest.approx(10.0)


class TestFloatCapacitanceDto:
    @pytest.mark.parametrize("unit", ["pF", "nF", "uF", "mF", "F"])
    def test_valid_unit_accepted(self, unit: str) -> None:
        FloatCapacitanceDto(value=1.0, unit=unit)

    def test_negative_rejected(self) -> None:
        with pytest.raises(ValueError, match="non-negative"):
            FloatCapacitanceDto(value=-1.0, unit="F")

    def test_nan_rejected(self) -> None:
        with pytest.raises(ValueError, match="must not be NaN"):
            FloatCapacitanceDto(value=math.nan, unit="F")

    def test_inf_accepted(self) -> None:
        # 地絡は inf キャパシタンスで表し、下流でクランプされる。
        dto = FloatCapacitanceDto(value=math.inf, unit="F")
        assert math.isinf(dto.get_value())

    def test_round_trip(self) -> None:
        original = FloatCapacitanceDto(value=2.5, unit="uF")
        round_trip = original.convert_to_unit("F").convert_to_unit("uF")
        assert round_trip.get_value() == pytest.approx(2.5)

    def test_invalid_unit_rejected(self) -> None:
        with pytest.raises(ValueError, match="invalid capacitance unit"):
            FloatCapacitanceDto(value=1.0, unit="bogus")
