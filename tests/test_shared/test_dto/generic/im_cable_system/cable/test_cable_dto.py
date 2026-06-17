"""``CableSeriesDto`` / ``CableSectionDto`` / ``CableDto`` テスト。

カバー対象:
    - ``CableSectionDto.__post_init__``: ``series`` 必須, allowed-series 検証
    - ``CableDto.calculate_total_length``: 単位混在/空セクションの合算動作
    - 各 collection DTO（``*Dtos``）の lookup・enumeration
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    CableConductorModelDto,
    CableDto,
    CableDtos,
    CableName,
    CableSectionDto,
    CableSectionDtos,
    CableSectionName,
    CableSeriesDto,
    CableSeriesDtos,
    CableSeriesName,
    CableShapeType,
    CableShapeTypeDto,
    ConductorModelType,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    FloatCapacitancePerLengthDto,
    FloatInductancePerLengthDto,
    FloatLengthDto,
    FloatResistanceLengthDto,
    FloatResistancePerLengthDto,
)


def _make_series(name: str = "SERIES_X") -> CableSeriesDto:
    return CableSeriesDto(
        name=CableSeriesName(value=name),
        shape_type=CableShapeTypeDto(value=CableShapeType.ROUND),
        conductor_resistance_per_length=FloatResistancePerLengthDto(
            value=0.1, unit="Ω/m"
        ),
        conductor_inductance_per_length=FloatInductancePerLengthDto(
            value=1.0, unit="mH/km"
        ),
        ground_resistance_length=FloatResistanceLengthDto(
            value=1.0, unit="kΩ*km"
        ),
        ground_capacitance_per_length=FloatCapacitancePerLengthDto(
            value=100.0, unit="nF/km"
        ),
    )


def _make_section(
    name: str,
    length_value: float,
    length_unit: str,
    series: CableSeriesDto,
) -> CableSectionDto:
    return CableSectionDto(
        name=CableSectionName(value=name),
        length=FloatLengthDto(value=length_value, unit=length_unit),
        series=series,
    )


def _make_basic_conductor_model() -> CableConductorModelDto:
    return CableConductorModelDto(name=ConductorModelType.BASIC)


class TestCableSectionDtoPostInit:
    def test_valid_section_accepted(self) -> None:
        series = _make_series()
        section = _make_section("S1", 100.0, "m", series)
        assert section.series is series

    def test_series_required(self) -> None:
        with pytest.raises(ValueError, match="series is required"):
            CableSectionDto(
                name=CableSectionName(value="S1"),
                length=FloatLengthDto(value=100.0, unit="m"),
                series=None,  # type: ignore[arg-type]
            )

    def test_allowed_series_constraint_when_provided(self) -> None:
        """duck typing 経由で section name から ``get_allowed_series_names`` が
        提供されたとき、許可リスト外の series を拒否する。
        """

        @dataclass(frozen=True, eq=False)
        class _RestrictedSectionName(CableSectionName):
            def get_allowed_series_names(self) -> list[str]:
                return ["ALLOWED_X"]

        bad_series = _make_series(name="WRONG")
        with pytest.raises(
            ValueError,
            match="cable series name 'WRONG' is not allowed",
        ):
            CableSectionDto(
                name=_RestrictedSectionName(value="S1"),
                length=FloatLengthDto(value=100.0, unit="m"),
                series=bad_series,
            )

    def test_allowed_series_empty_skips_check(self) -> None:
        """allowed list が空のときは検証をスキップする。"""

        @dataclass(frozen=True, eq=False)
        class _OpenSectionName(CableSectionName):
            def get_allowed_series_names(self) -> list[str]:
                return []

        CableSectionDto(
            name=_OpenSectionName(value="S1"),
            length=FloatLengthDto(value=100.0, unit="m"),
            series=_make_series("ANY"),
        )


class TestCableDtoCalculateTotalLength:
    def test_single_section(self) -> None:
        series = _make_series()
        sections = CableSectionDtos(
            objects=[_make_section("S1", 100.0, "m", series)],
        )
        cable = CableDto(
            name=CableName(value="C1"),
            sections=sections,
            conductor_model=_make_basic_conductor_model(),
        )
        total = cable.calculate_total_length()
        assert total.get_unit() == "m"
        assert total.get_value() == pytest.approx(100.0)

    def test_multiple_sections_mixed_units(self) -> None:
        series = _make_series()
        sections = CableSectionDtos(
            objects=[
                _make_section("S1", 100.0, "m", series),
                _make_section("S2", 0.5, "km", series),
                _make_section("S3", 50.0, "cm", series),
            ],
        )
        cable = CableDto(
            name=CableName(value="C1"),
            sections=sections,
            conductor_model=_make_basic_conductor_model(),
        )
        total = cable.calculate_total_length()
        # 100 m + 500 m + 0.5 m = 600.5 m
        assert total.get_value() == pytest.approx(600.5)
        assert total.get_unit() == "m"

    def test_empty_sections_returns_zero(self) -> None:
        sections = CableSectionDtos(objects=[])
        cable = CableDto(
            name=CableName(value="C1"),
            sections=sections,
            conductor_model=_make_basic_conductor_model(),
        )
        total = cable.calculate_total_length()
        assert total.get_value() == pytest.approx(0.0)


class TestCableSeriesDtosCollection:
    def test_lookup_by_name(self) -> None:
        a = _make_series("A")
        b = _make_series("B")
        coll = CableSeriesDtos(objects=[a, b])
        assert len(coll) == 2
        assert coll.get_by_name("A") is a
        assert coll.get_by_name("B") is b

    def test_get_names(self) -> None:
        coll = CableSeriesDtos(objects=[_make_series("A"), _make_series("B")])
        assert coll.get_names() == ["A", "B"]

    def test_get_by_unknown_raises(self) -> None:
        coll = CableSeriesDtos(objects=[_make_series("A")])
        with pytest.raises(ValueError, match="No item found"):
            coll.get_by_name("missing")


class TestCableDtosCollection:
    def test_lookup_by_name(self) -> None:
        series = _make_series()
        sections = CableSectionDtos(
            objects=[_make_section("S1", 100.0, "m", series)],
        )
        cable_a = CableDto(
            name=CableName(value="A"),
            sections=sections,
            conductor_model=_make_basic_conductor_model(),
        )
        cable_b = CableDto(
            name=CableName(value="B"),
            sections=sections,
            conductor_model=_make_basic_conductor_model(),
        )
        coll = CableDtos(objects=[cable_a, cable_b])
        assert coll.get_by_name("A") is cable_a
        assert coll.get_by_name("B") is cable_b
