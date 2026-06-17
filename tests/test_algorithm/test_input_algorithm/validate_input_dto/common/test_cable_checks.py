"""``check_cable_section_lengths`` の経路非依存テスト。

ケーブルセクション長が ``> 0`` であることを直接検証する。``length == 0``
は :class:`FloatLengthDto` 側を通る（``>= 0`` 契約）ため、common 関数が
``> 0`` を強制していることを直接示す。
"""

from __future__ import annotations

import dataclasses
from collections.abc import Callable

import pytest

from im_cable_system.engine.algorithm.input_algorithm.validate_input_dto.common.cable_checks import (  # noqa: E501, PLC2701
    check_cable_section_lengths,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    FloatLengthDto,
)
from im_cable_system.engine.shared.dto.input import (
    InputDto,
)

_WITH_CABLE_SERIES = "slipdependent01_ideal_feeder30m_ideal_lead10m.tsv"


def _replace_section_length_at(
    dto: InputDto,
    *,
    index: int,
    length: FloatLengthDto,
) -> InputDto:
    assert dto.cable is not None
    sections = list(dto.cable.sections.get_all())
    new_section = dataclasses.replace(sections[index], length=length)
    new_sections = dto.cable.sections.__class__(
        objects=[
            *sections[:index],
            new_section,
            *sections[index + 1 :],
        ]
    )
    new_cable = dataclasses.replace(dto.cable, sections=new_sections)
    return dataclasses.replace(dto, cable=new_cable)


class TestCheckCableSectionLengths:
    """``check_cable_section_lengths`` の単体テスト。"""

    def test_pass_when_cable_is_none(
        self,
        build_cartesian_dto: Callable[..., InputDto],
    ) -> None:
        """``cable is None`` のとき何もせずに通る。"""
        dto = build_cartesian_dto()
        assert dto.cable is None
        check_cable_section_lengths(dto)

    def test_accepts_all_positive_lengths(
        self,
        build_cartesian_dto: Callable[..., InputDto],
    ) -> None:
        """全セクション長が正のとき pass する。"""
        dto = build_cartesian_dto(series_path=_WITH_CABLE_SERIES)
        check_cable_section_lengths(dto)

    def test_rejects_zero_length_first_section(
        self,
        build_cartesian_dto: Callable[..., InputDto],
    ) -> None:
        """先頭セクション長 0 で raise する。"""
        dto = build_cartesian_dto(series_path=_WITH_CABLE_SERIES)
        invalid = _replace_section_length_at(
            dto,
            index=0,
            length=FloatLengthDto(value=0.0, unit="m"),
        )
        with pytest.raises(
            ValueError, match=r"cable\.sections\[0\]\.length.*正"
        ):
            check_cable_section_lengths(invalid)

    def test_rejects_zero_length_non_first_section(
        self,
        build_cartesian_dto: Callable[..., InputDto],
    ) -> None:
        """1 件目以外のセクション長 0 でも raise する（添字が報告される）。"""
        dto = build_cartesian_dto(series_path=_WITH_CABLE_SERIES)
        assert dto.cable is not None
        sections = dto.cable.sections.get_all()
        assert len(sections) >= 2
        invalid = _replace_section_length_at(
            dto,
            index=1,
            length=FloatLengthDto(value=0.0, unit="m"),
        )
        with pytest.raises(
            ValueError, match=r"cable\.sections\[1\]\.length.*正"
        ):
            check_cable_section_lengths(invalid)
