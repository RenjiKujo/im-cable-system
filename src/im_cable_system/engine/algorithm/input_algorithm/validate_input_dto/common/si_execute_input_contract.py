"""ExecuteStage / ExecuteAlgorithm 入力の SI 基本単位契約（共通検証）。

Forward / EstimateParams 入力では ``assemble_input_dto`` 段の最後に
SI 基本単位へ正規化する。本モジュールでは、ExecuteStage /
ExecuteAlgorithm へ渡す直前の DTO が **現在の単位として** SI 基本単位
に揃っていることを検証する。
"""

from __future__ import annotations

from typing import cast

from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ArrayKey,
    CableSeriesDto,
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

SI_BASE_HZ: str = "Hz"
SI_BASE_V: str = "V"
SI_BASE_W: str = "W"
SI_BASE_A: str = "A"
SI_BASE_RAD_PER_S: str = "rad/s"
SI_BASE_NM: str = "Nm"
SI_BASE_DIMLESS: str = "-"
SI_BASE_OHM: str = "Ω"
SI_BASE_H: str = "H"
SI_BASE_OHM_PER_M: str = "Ω/m"
SI_BASE_H_PER_M: str = "H/m"
SI_BASE_OHM_M: str = "Ω*m"
SI_BASE_F_PER_M: str = "F/m"
SI_BASE_M: str = "m"


def dto_current_unit_str(dto: IFloatWithUnitDto | IArrayWithUnitDto) -> str:
    """物理量 DTO の現在の単位文字列を返す。"""
    return str(dto.get_unit())


def require_base_unit(
    dto: IFloatWithUnitDto | IArrayWithUnitDto,
    path: str,
    expected: str,
) -> None:
    """現在の ``get_unit()`` が expected と一致することを検証する。"""
    got = dto_current_unit_str(dto)
    if got != expected:
        raise ValueError(
            f"{path} の単位は {expected!r} である必要がありますが {got!r} でした。"
        )


# 入力軸ごとに期待する SI 基本単位。``arrays`` に存在するキーのみ検証する。
_AXIS_EXPECTED_SI_BASE_UNITS: tuple[tuple[ArrayKey, str], ...] = (
    (ArrayKey.SLIP, SI_BASE_DIMLESS),
    (ArrayKey.FREQUENCY, SI_BASE_HZ),
    (ArrayKey.INPUT_LINE_VOLTAGE, SI_BASE_V),
    (ArrayKey.INPUT_LINE_CURRENT, SI_BASE_A),
)


def validate_array_layout_reference_axes_si_base_or_raise(
    input_dto: InputDto,
) -> None:
    """入力軸配列が現在の単位として SI 基本単位に揃っていることを検証する。

    ``arrays`` に存在する既知の入力軸（slip / frequency /
    input_line_voltage / input_line_current）すべてについて、
    現在の ``get_unit()`` が SI 基本単位と一致することを確認する。
    期待単位は :data:`_AXIS_EXPECTED_SI_BASE_UNITS` に定義する。
    マッピングに無い軸キーはここでは扱わない。
    """
    arrays = input_dto.array_layout.arrays
    for axis_key, expected_unit in _AXIS_EXPECTED_SI_BASE_UNITS:
        if axis_key not in arrays:
            continue
        require_base_unit(
            arrays[axis_key],
            f"array_layout.arrays[{axis_key.value!r}]",
            expected_unit,
        )


def validate_im_pc_catalogs_channels_si_base_or_raise(
    im_pc_catalogs: ImPerformanceCurveCatalogDtos,
) -> None:
    """性能カタログの供給条件・系列が現在の単位として SI 基本に揃うことを検証する。"""
    for idx, raw in enumerate(im_pc_catalogs.get_all()):
        cat = cast(ImPerformanceCurveCatalogDto, raw)
        pfx = f"im_pc_catalogs[{idx}] ({cat.name!r})"
        require_base_unit(
            cat.supply_frequency, f"{pfx}.supply_frequency", SI_BASE_HZ
        )
        require_base_unit(
            cat.supply_voltage, f"{pfx}.supply_voltage", SI_BASE_V
        )
        require_base_unit(
            cat.slip_series, f"{pfx}.slip_series", SI_BASE_DIMLESS
        )
        if cat.power_series is not None:
            require_base_unit(
                cat.power_series, f"{pfx}.power_series", SI_BASE_W
            )
        if cat.current_series is not None:
            require_base_unit(
                cat.current_series,
                f"{pfx}.current_series",
                SI_BASE_A,
            )
        if cat.power_factor_series is not None:
            require_base_unit(
                cat.power_factor_series,
                f"{pfx}.power_factor_series",
                SI_BASE_DIMLESS,
            )
        if cat.efficiency_series is not None:
            require_base_unit(
                cat.efficiency_series,
                f"{pfx}.efficiency_series",
                SI_BASE_DIMLESS,
            )
        if cat.rotational_speed_series is not None:
            require_base_unit(
                cat.rotational_speed_series,
                f"{pfx}.rotational_speed_series",
                SI_BASE_RAD_PER_S,
            )
        if cat.torque_series is not None:
            require_base_unit(
                cat.torque_series,
                f"{pfx}.torque_series",
                SI_BASE_NM,
            )


def validate_im_series_si_base_or_raise(im: ImDto) -> None:
    """ImSeries の名板・R/L が現在の単位として SI 基本に揃うことを検証する。"""
    series = im.im_series
    prefix = "im.im_series"
    require_base_unit(
        series.nameplate_voltage,
        f"{prefix}.nameplate_voltage",
        SI_BASE_V,
    )
    require_base_unit(
        series.nameplate_current,
        f"{prefix}.nameplate_current",
        SI_BASE_A,
    )
    require_base_unit(
        series.nameplate_power,
        f"{prefix}.nameplate_power",
        SI_BASE_W,
    )
    require_base_unit(
        series.nameplate_frequency,
        f"{prefix}.nameplate_frequency",
        SI_BASE_HZ,
    )
    require_base_unit(
        series.primary_resistance, f"{prefix}.primary_resistance", SI_BASE_OHM
    )
    require_base_unit(
        series.primary_inductance, f"{prefix}.primary_inductance", SI_BASE_H
    )
    require_base_unit(
        series.excitation_resistance,
        f"{prefix}.excitation_resistance",
        SI_BASE_OHM,
    )
    require_base_unit(
        series.excitation_inductance,
        f"{prefix}.excitation_inductance",
        SI_BASE_H,
    )
    for branch, sec_r in series.secondary_resistances.items():
        require_base_unit(
            sec_r,
            f"{prefix}.secondary_resistances[{branch!s}]",
            SI_BASE_OHM,
        )
        require_base_unit(
            series.secondary_inductances[branch],
            f"{prefix}.secondary_inductances[{branch!s}]",
            SI_BASE_H,
        )


def validate_cable_series_si_base_or_raise(
    cable_series: CableSeriesDto,
) -> None:
    """ケーブルシリーズの π 型パラメータが現在の単位として SI 基本に揃うことを検証する。"""
    prefix = "cable_series"
    require_base_unit(
        cable_series.conductor_resistance_per_length,
        f"{prefix}.conductor_resistance_per_length",
        SI_BASE_OHM_PER_M,
    )
    require_base_unit(
        cable_series.conductor_inductance_per_length,
        f"{prefix}.conductor_inductance_per_length",
        SI_BASE_H_PER_M,
    )
    require_base_unit(
        cable_series.ground_resistance_length,
        f"{prefix}.ground_resistance_length",
        SI_BASE_OHM_M,
    )
    require_base_unit(
        cable_series.ground_capacitance_per_length,
        f"{prefix}.ground_capacitance_per_length",
        SI_BASE_F_PER_M,
    )


def validate_cable_section_lengths_si_base_or_raise(
    input_dto: InputDto,
) -> None:
    """各ケーブルセクション長が現在の単位として SI 基本単位 ``m`` に揃うことを検証する。"""
    cable = input_dto.cable
    if cable is None:
        return
    for idx, section in enumerate(cable.sections.get_all()):
        require_base_unit(
            section.length,
            f"cable.sections[{idx}].length",
            SI_BASE_M,
        )
