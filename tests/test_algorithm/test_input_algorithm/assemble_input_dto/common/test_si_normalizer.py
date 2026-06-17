"""``to_si_input_dto`` の単体テスト。

Forward / EstimateParams いずれの Assembler でも最終段で呼ぶ
:func:`to_si_input_dto` について、SI 基本単位への変換と冪等性を
直接検証する。実 :class:`InputDto` の用意には Forward Orchestrator を
経由する（``conftest.py`` の ``build_cartesian_dto`` fixture）。
"""

from __future__ import annotations

import dataclasses
from collections.abc import Callable

import numpy as np

from im_cable_system.engine.algorithm.input_algorithm.assemble_input_dto.common.si_normalizer import (  # noqa: E501, PLC2701
    to_si_input_dto,
)
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ArrayKey,
)
from im_cable_system.engine.shared.dto.input import (
    InputDto,
)


def _replace_voltage_axis(dto: InputDto, target_unit: str) -> InputDto:
    """電圧軸を ``convert_to_unit(target_unit)`` で別単位に差し替える。"""
    volt = dto.array_layout.arrays[ArrayKey.INPUT_LINE_VOLTAGE]
    converted = volt.convert_to_unit(target_unit)
    new_arrays = dict(dto.array_layout.arrays)
    new_arrays[ArrayKey.INPUT_LINE_VOLTAGE] = converted
    new_layout = dataclasses.replace(
        dto.array_layout,
        arrays=new_arrays,
    )
    return dataclasses.replace(dto, array_layout=new_layout)


class TestToSiInputDtoBaseUnits:
    """SI 化後に各 DTO の現在単位が SI 基本単位になっていることの確認。"""

    def test_array_layout_arrays_in_si_base_units(
        self,
        build_cartesian_dto: Callable[..., InputDto],
    ) -> None:
        dto = build_cartesian_dto()
        si_dto = to_si_input_dto(dto)
        arrays = si_dto.array_layout.arrays
        assert arrays[ArrayKey.SLIP].get_unit() == "-"
        assert arrays[ArrayKey.FREQUENCY].get_unit() == "Hz"
        assert arrays[ArrayKey.INPUT_LINE_VOLTAGE].get_unit() == "V"

    def test_im_series_floats_in_si_base_units(
        self,
        build_cartesian_dto: Callable[..., InputDto],
    ) -> None:
        dto = build_cartesian_dto()
        si_dto = to_si_input_dto(dto)
        series = si_dto.im.im_series
        assert series.nameplate_voltage.get_unit() == "V"
        assert series.nameplate_current.get_unit() == "A"
        assert series.nameplate_power.get_unit() == "W"
        assert series.nameplate_frequency.get_unit() == "Hz"
        assert series.primary_resistance.get_unit() == "Ω"
        assert series.primary_inductance.get_unit() == "H"
        for r in series.secondary_resistances.values():
            assert r.get_unit() == "Ω"
        for x in series.secondary_inductances.values():
            assert x.get_unit() == "H"


class TestToSiInputDtoConvertsNonSiInput:
    """非 SI 単位を持つ DTO を渡しても SI に揃うことの確認。"""

    def test_kv_voltage_axis_is_converted_to_volt(
        self,
        build_cartesian_dto: Callable[..., InputDto],
    ) -> None:
        dto = build_cartesian_dto()
        in_kv = _replace_voltage_axis(dto, target_unit="kV")
        assert (
            in_kv.array_layout.arrays[ArrayKey.INPUT_LINE_VOLTAGE].get_unit()
            == "kV"
        )
        si_dto = to_si_input_dto(in_kv)
        volt = si_dto.array_layout.arrays[ArrayKey.INPUT_LINE_VOLTAGE]
        assert volt.get_unit() == "V"
        original = dto.array_layout.arrays[
            ArrayKey.INPUT_LINE_VOLTAGE
        ].get_value()
        assert np.allclose(volt.get_value(), original)


class TestToSiInputDtoIdempotency:
    """既に SI 単位の DTO に再適用しても値・単位が変化しない。"""

    def test_si_already_dto_is_unchanged_after_reapplication(
        self,
        build_cartesian_dto: Callable[..., InputDto],
    ) -> None:
        dto = build_cartesian_dto()
        once = to_si_input_dto(dto)
        twice = to_si_input_dto(once)
        arrays_once = once.array_layout.arrays
        arrays_twice = twice.array_layout.arrays
        for key in arrays_once:
            assert arrays_once[key].get_unit() == arrays_twice[key].get_unit()
            assert np.allclose(
                arrays_once[key].get_value(),
                arrays_twice[key].get_value(),
            )
        series_once = once.im.im_series
        series_twice = twice.im.im_series
        assert (
            series_once.nameplate_voltage.get_value()
            == series_twice.nameplate_voltage.get_value()
        )
        assert (
            series_once.nameplate_power.get_value()
            == series_twice.nameplate_power.get_value()
        )

    def test_cable_section_units_are_idempotent(
        self,
        build_cartesian_dto: Callable[..., InputDto],
    ) -> None:
        dto = build_cartesian_dto(
            series_path="slipdependent01_ideal_feeder30m_ideal_lead10m.tsv",
        )
        once = to_si_input_dto(dto)
        twice = to_si_input_dto(once)
        assert once.cable is not None
        assert twice.cable is not None
        for s_once, s_twice in zip(
            once.cable.sections.get_all(),
            twice.cable.sections.get_all(),
            strict=True,
        ):
            assert s_once.length.get_unit() == s_twice.length.get_unit() == "m"
            assert s_once.length.get_value() == s_twice.length.get_value()
