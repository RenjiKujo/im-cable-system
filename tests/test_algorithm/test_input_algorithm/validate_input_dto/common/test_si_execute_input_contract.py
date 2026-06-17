"""``si_execute_input_contract`` の経路非依存テスト。

``get_unit()`` が期待する SI 基本単位と一致するか、というシンプルな
契約のみを担うため、対象 DTO は最小限の ``get_unit()`` 互換スタブで
代用する。検査対象は ``InputDto`` / ``ImDto`` / ``CableSeriesDto`` /
``ImPerformanceCurveCatalogDtos`` であり、ここでは関数単位で正常系と
代表的な異常系を 1 件ずつ確認する。
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from im_cable_system.engine.algorithm.input_algorithm.validate_input_dto.common.si_execute_input_contract import (  # noqa: E501, PLC2701
    validate_array_layout_reference_axes_si_base_or_raise,
    validate_cable_section_lengths_si_base_or_raise,
    validate_cable_series_si_base_or_raise,
    validate_im_pc_catalogs_channels_si_base_or_raise,
    validate_im_series_si_base_or_raise,
)
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ArrayKey,
)


class _UnitStub:
    """``get_unit()`` だけを返すスタブ。"""

    def __init__(self, unit: str) -> None:
        self._unit = unit

    def get_unit(self) -> str:
        return self._unit


def _array_layout_dto(unit_overrides: dict[ArrayKey, str] | None = None):
    units: dict[ArrayKey, str] = {
        ArrayKey.SLIP: "-",
        ArrayKey.FREQUENCY: "Hz",
        ArrayKey.INPUT_LINE_VOLTAGE: "V",
        ArrayKey.INPUT_LINE_CURRENT: "A",
    }
    if unit_overrides is not None:
        units.update(unit_overrides)
    mock_dto = MagicMock()
    mock_dto.array_layout = MagicMock()
    mock_dto.array_layout.arrays = {
        axis_key: _UnitStub(unit) for axis_key, unit in units.items()
    }
    return mock_dto


def _im_dto(unit_overrides: dict[str, str] | None = None):
    base_units: dict[str, str] = {
        "nameplate_voltage": "V",
        "nameplate_current": "A",
        "nameplate_power": "W",
        "nameplate_frequency": "Hz",
        "primary_resistance": "Ω",
        "primary_inductance": "H",
        "excitation_resistance": "Ω",
        "excitation_inductance": "H",
        "secondary_resistance": "Ω",
        "secondary_inductance": "H",
    }
    if unit_overrides is not None:
        base_units.update(unit_overrides)
    series = MagicMock()
    for attr, unit in base_units.items():
        if attr.startswith("secondary_"):
            continue
        setattr(series, attr, _UnitStub(unit))
    series.secondary_resistances = {
        "SINGLE": _UnitStub(base_units["secondary_resistance"]),
    }
    series.secondary_inductances = {
        "SINGLE": _UnitStub(base_units["secondary_inductance"]),
    }
    im = MagicMock()
    im.im_series = series
    return im


def _cable_series_dto(unit_overrides: dict[str, str] | None = None):
    base_units: dict[str, str] = {
        "conductor_resistance_per_length": "Ω/m",
        "conductor_inductance_per_length": "H/m",
        "ground_resistance_length": "Ω*m",
        "ground_capacitance_per_length": "F/m",
    }
    if unit_overrides is not None:
        base_units.update(unit_overrides)
    cable_series = MagicMock()
    for attr, unit in base_units.items():
        setattr(cable_series, attr, _UnitStub(unit))
    return cable_series


def _catalog_stub(*, name: str = "cat0", unit_overrides=None):
    base_units: dict[str, str] = {
        "supply_frequency": "Hz",
        "supply_voltage": "V",
        "slip_series": "-",
        "power_series": "W",
        "current_series": "A",
        "power_factor_series": "-",
        "efficiency_series": "-",
        "rotational_speed_series": "rad/s",
        "torque_series": "Nm",
    }
    if unit_overrides is not None:
        base_units.update(unit_overrides)
    cat = MagicMock()
    cat.name = name
    for attr, unit in base_units.items():
        setattr(cat, attr, _UnitStub(unit))
    return cat


def _input_dto_with_cable_section_units(units: list[str]):
    sections = []
    for unit in units:
        section = MagicMock()
        section.length = _UnitStub(unit)
        sections.append(section)
    cable = MagicMock()
    cable.sections.get_all.return_value = sections
    dto = MagicMock()
    dto.cable = cable
    return dto


class TestValidateArrayLayoutReferenceAxesSiBase:
    """``validate_array_layout_reference_axes_si_base_or_raise``。"""

    def test_accepts_si_base_units(self) -> None:
        validate_array_layout_reference_axes_si_base_or_raise(
            _array_layout_dto()
        )

    def test_rejects_non_si_slip_unit(self) -> None:
        with pytest.raises(ValueError, match="slip"):
            validate_array_layout_reference_axes_si_base_or_raise(
                _array_layout_dto({ArrayKey.SLIP: "Hz"})
            )

    def test_rejects_non_si_voltage_unit(self) -> None:
        with pytest.raises(ValueError, match="input_line_voltage"):
            validate_array_layout_reference_axes_si_base_or_raise(
                _array_layout_dto({ArrayKey.INPUT_LINE_VOLTAGE: "kV"})
            )

    def test_skips_missing_axis(self) -> None:
        """``arrays`` に無い軸キーはスキップする。"""
        mock_dto = MagicMock()
        mock_dto.array_layout = MagicMock()
        mock_dto.array_layout.arrays = {
            ArrayKey.SLIP: _UnitStub("-"),
        }
        validate_array_layout_reference_axes_si_base_or_raise(mock_dto)


class TestValidateImSeriesSiBase:
    """``validate_im_series_si_base_or_raise``。"""

    def test_accepts_si_base_units(self) -> None:
        validate_im_series_si_base_or_raise(_im_dto())

    def test_rejects_non_si_nameplate_voltage(self) -> None:
        with pytest.raises(ValueError, match="nameplate_voltage"):
            validate_im_series_si_base_or_raise(
                _im_dto({"nameplate_voltage": "kV"})
            )

    def test_rejects_non_si_secondary_resistance(self) -> None:
        with pytest.raises(ValueError, match="secondary_resistances"):
            validate_im_series_si_base_or_raise(
                _im_dto({"secondary_resistance": "kΩ"})
            )


class TestValidateImPcCatalogsChannelsSiBase:
    """``validate_im_pc_catalogs_channels_si_base_or_raise``。"""

    def test_accepts_empty_catalogs(self) -> None:
        empty = MagicMock()
        empty.get_all.return_value = []
        validate_im_pc_catalogs_channels_si_base_or_raise(empty)

    def test_accepts_si_base_units(self) -> None:
        catalogs = MagicMock()
        catalogs.get_all.return_value = [_catalog_stub()]
        validate_im_pc_catalogs_channels_si_base_or_raise(catalogs)

    def test_rejects_non_si_supply_voltage(self) -> None:
        catalogs = MagicMock()
        catalogs.get_all.return_value = [
            _catalog_stub(unit_overrides={"supply_voltage": "kV"})
        ]
        with pytest.raises(ValueError, match="supply_voltage"):
            validate_im_pc_catalogs_channels_si_base_or_raise(catalogs)

    def test_skips_optional_series_when_none(self) -> None:
        """``power_series`` などが ``None`` のときはスキップする。"""
        cat = _catalog_stub()
        cat.power_series = None
        cat.current_series = None
        cat.power_factor_series = None
        cat.efficiency_series = None
        cat.rotational_speed_series = None
        cat.torque_series = None
        catalogs = MagicMock()
        catalogs.get_all.return_value = [cat]
        validate_im_pc_catalogs_channels_si_base_or_raise(catalogs)


class TestValidateCableSeriesSiBase:
    """``validate_cable_series_si_base_or_raise``。"""

    def test_accepts_si_base_units(self) -> None:
        validate_cable_series_si_base_or_raise(_cable_series_dto())

    def test_rejects_non_si_conductor_resistance(self) -> None:
        with pytest.raises(ValueError, match="conductor_resistance_per_length"):
            validate_cable_series_si_base_or_raise(
                _cable_series_dto({"conductor_resistance_per_length": "kΩ/m"})
            )

    def test_rejects_non_si_ground_capacitance(self) -> None:
        with pytest.raises(ValueError, match="ground_capacitance_per_length"):
            validate_cable_series_si_base_or_raise(
                _cable_series_dto({"ground_capacitance_per_length": "uF/m"})
            )


class TestValidateCableSectionLengthsSiBase:
    """``validate_cable_section_lengths_si_base_or_raise``。"""

    def test_pass_when_cable_is_none(self) -> None:
        mock_dto = MagicMock()
        mock_dto.cable = None
        validate_cable_section_lengths_si_base_or_raise(mock_dto)

    def test_accepts_si_base_units(self) -> None:
        validate_cable_section_lengths_si_base_or_raise(
            _input_dto_with_cable_section_units(["m", "m"])
        )

    def test_rejects_non_si_section_length_unit(self) -> None:
        with pytest.raises(ValueError, match=r"cable\.sections\[1\]\.length"):
            validate_cable_section_lengths_si_base_or_raise(
                _input_dto_with_cable_section_units(["m", "mm"])
            )
