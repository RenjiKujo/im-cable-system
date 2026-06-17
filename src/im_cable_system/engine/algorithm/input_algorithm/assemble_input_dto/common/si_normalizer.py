""":class:`InputDto` を SI 基本単位へ正規化する共通ヘルパー。

Forward / EstimateParams いずれの ``InputDtoAssembler.assemble()`` でも
最終段で呼び出し、各 builder が返した DTO 内の物理量 DTO
（:class:`IFloatWithUnitDto` / :class:`IArrayWithUnitDto` 実装）を
``to_base_unit()`` で SI 基本単位（V / A / W / Hz / Ω / H / m / rad/s
/ Nm 等）に揃える。

これにより、下流の processor / pipeline と
:mod:`validate_input_dto.common.si_execute_input_contract` の SI 基本単位
契約は、受け取った時点で SI 基本単位だと仮定してよい。

設計メモ:
    - DTO はすべて ``@dataclass(frozen=True)`` なので
      :func:`dataclasses.replace` で部分置換した新インスタンスを作る。
    - 各 ``to_base_unit()`` は同じ具象型を返す契約
      （:class:`IFloatWithUnitDto` / :class:`IArrayWithUnitDto`）なので、
      型ヒントを崩さずに置換できる。
    - ``replace`` のたびに ``__post_init__`` が再走するが、単位以外の
      attribute（``reference_axes`` や secondary dict キー、性能曲線の
      ``P=T·ω`` 整合性等）は SI 化で変化しないので問題ない。
"""

from __future__ import annotations

import dataclasses
from typing import TypeVar, cast

from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ArrayLayoutDto,
    CableDto,
    CableSectionDto,
    CableSectionDtos,
    ImDto,
    ImPerformanceCurveCatalogDto,
    ImPerformanceCurveCatalogDtos,
)
from im_cable_system.engine.shared.dto.generic.interfaces import (
    IArrayWithUnitDto,
    IFloatWithUnitDto,
)
from im_cable_system.engine.shared.dto.input import (
    InputDto,
)

_UnitDtoT = TypeVar("_UnitDtoT", bound="IFloatWithUnitDto | IArrayWithUnitDto")


def to_si_input_dto(dto: InputDto) -> InputDto:
    """``InputDto`` 内の物理量 DTO を SI 基本単位に揃えた新インスタンスを返す。

    本関数は冪等である。すでに SI 基本単位に揃った ``InputDto`` に対して
    再度呼び出しても、物理量としての値と単位は変化しない。

    Args:
        dto: SI 化したい InputDto。

    Returns:
        単位だけ SI 基本単位へ揃えた InputDto（その他の attribute は同値）。
    """
    return dataclasses.replace(
        dto,
        array_layout=_to_si_array_layout(dto.array_layout),
        im=_to_si_im(dto.im),
        cable=(_to_si_cable(dto.cable) if dto.cable is not None else None),
        im_pc_catalogs=_to_si_im_pc_catalogs(dto.im_pc_catalogs),
    )


def _to_si_array_layout(layout: ArrayLayoutDto) -> ArrayLayoutDto:
    """``arrays`` dict の各 ``IArrayWithUnitDto`` を SI 基本単位に揃える。"""
    new_arrays = {key: arr.to_base_unit() for key, arr in layout.arrays.items()}
    return dataclasses.replace(layout, arrays=new_arrays)


def _to_si_im(im: ImDto) -> ImDto:
    """``ImDto.im_series`` 内の各 ``Float*Dto`` を SI 基本単位に揃える。"""
    series = im.im_series
    new_series = dataclasses.replace(
        series,
        nameplate_voltage=series.nameplate_voltage.to_base_unit(),
        nameplate_current=series.nameplate_current.to_base_unit(),
        nameplate_power=series.nameplate_power.to_base_unit(),
        nameplate_frequency=series.nameplate_frequency.to_base_unit(),
        primary_resistance=series.primary_resistance.to_base_unit(),
        primary_inductance=series.primary_inductance.to_base_unit(),
        excitation_resistance=series.excitation_resistance.to_base_unit(),
        excitation_inductance=series.excitation_inductance.to_base_unit(),
        secondary_resistances={
            branch: dto.to_base_unit()
            for branch, dto in series.secondary_resistances.items()
        },
        secondary_inductances={
            branch: dto.to_base_unit()
            for branch, dto in series.secondary_inductances.items()
        },
    )
    return dataclasses.replace(im, im_series=new_series)


def _to_si_cable(cable: CableDto) -> CableDto:
    """``CableDto.sections`` の各 ``CableSectionDto`` を SI 基本単位に揃える。"""
    new_sections = [
        _to_si_cable_section(section) for section in cable.sections.get_all()
    ]
    return dataclasses.replace(
        cable,
        sections=CableSectionDtos(objects=new_sections),
    )


def _to_si_cable_section(section: CableSectionDto) -> CableSectionDto:
    """``CableSectionDto`` の ``length`` と ``series`` 内の各 Float* を SI 化。"""
    series = section.series
    new_series = dataclasses.replace(
        series,
        conductor_resistance_per_length=(
            series.conductor_resistance_per_length.to_base_unit()
        ),
        conductor_inductance_per_length=(
            series.conductor_inductance_per_length.to_base_unit()
        ),
        ground_resistance_length=(
            series.ground_resistance_length.to_base_unit()
        ),
        ground_capacitance_per_length=(
            series.ground_capacitance_per_length.to_base_unit()
        ),
    )
    return dataclasses.replace(
        section,
        length=section.length.to_base_unit(),
        series=new_series,
    )


def _to_si_im_pc_catalogs(
    catalogs: ImPerformanceCurveCatalogDtos,
) -> ImPerformanceCurveCatalogDtos:
    """``ImPerformanceCurveCatalogDtos`` 内の各カタログを SI 基本単位に揃える。"""
    return ImPerformanceCurveCatalogDtos(
        objects=[_to_si_im_pc_catalog(c) for c in catalogs.get_all()],
    )


def _to_si_im_pc_catalog(
    catalog: ImPerformanceCurveCatalogDto,
) -> ImPerformanceCurveCatalogDto:
    """1 カタログ分のスカラー単位・系列単位を SI 基本単位に揃える。

    optional な系列は ``None`` のまま保持する。
    """
    return dataclasses.replace(
        catalog,
        supply_frequency=catalog.supply_frequency.to_base_unit(),
        supply_voltage=catalog.supply_voltage.to_base_unit(),
        slip_series=catalog.slip_series.to_base_unit(),
        power_series=_to_si_optional(catalog.power_series),
        torque_series=_to_si_optional(catalog.torque_series),
        current_series=_to_si_optional(catalog.current_series),
        power_factor_series=_to_si_optional(catalog.power_factor_series),
        efficiency_series=_to_si_optional(catalog.efficiency_series),
        rotational_speed_series=_to_si_optional(
            catalog.rotational_speed_series
        ),
    )


def _to_si_optional(dto: _UnitDtoT | None) -> _UnitDtoT | None:
    """``None`` をスキップしつつ ``to_base_unit()`` を呼ぶ薄いラッパー。

    ``IFloatWithUnitDto`` / ``IArrayWithUnitDto`` の ``to_base_unit()`` は
    同じ具象型を返す契約なので、TypeVar 経由で具象型を保ったまま返す。
    """
    return None if dto is None else cast(_UnitDtoT, dto.to_base_unit())
