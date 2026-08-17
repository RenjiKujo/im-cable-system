"""``fixed_section_helpers`` の単体テスト。

純関数群（``fixed_required_str`` / ``fixed_required_int`` /
``resolve_cable_length``）について、``EstimateParamsParsedTables.fixed``
の状態に応じた正常・異常系を網羅する。
"""

from __future__ import annotations

import pytest

from im_cable_system.engine.algorithm.input_algorithm.load_data.estimate_params.fixed_section_helpers import (  # noqa: E501
    fixed_required_int,
    fixed_required_str,
    resolve_cable_length,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data.estimate_params.unified_input_parser import (  # noqa: E501
    EstimateParamsParsedTables,
    FixedCell,
)


def _make_parsed(fixed: dict[str, FixedCell]) -> EstimateParamsParsedTables:
    """``fixed`` セクションだけ意味のあるダミー ParsedTables を組む。

    他のフィールドはテスト対象外のため空・空タプル相当で埋める。
    """
    return EstimateParamsParsedTables(
        im_performance_curve_name="dummy",
        nameplate_block={},
        fixed=fixed,
        candidate_primary=(),
        candidate_excitation=(),
        candidate_secondary_single=(),
        candidate_secondary_double_inner=(),
        candidate_secondary_double_outer=(),
        candidate_friction_windage=(),
        candidate_stray_load=(),
        candidate_cable_conductor=(),
        supply_block={},
        curve_header_row=[],
        curve_unit_row=[],
        curve_data_rows=[],
    )


class TestFixedRequiredStr:
    """``fixed_required_str`` の正常・異常系。"""

    def test_returns_value_when_key_exists(self) -> None:
        parsed = _make_parsed(
            {"im_circuit_type": FixedCell(value="STAR", unit=None)},
        )
        assert fixed_required_str(parsed, "im_circuit_type") == "STAR"

    def test_raises_when_key_missing(self) -> None:
        parsed = _make_parsed({})
        with pytest.raises(ValueError, match="必須キー 'im_poles'"):
            fixed_required_str(parsed, "im_poles")


class TestFixedRequiredInt:
    """``fixed_required_int`` の正常・異常系。"""

    def test_converts_int_when_value_is_integer_literal(self) -> None:
        parsed = _make_parsed({"im_poles": FixedCell(value="4", unit=None)})
        assert fixed_required_int(parsed, "im_poles") == 4

    def test_raises_when_key_missing(self) -> None:
        parsed = _make_parsed({})
        with pytest.raises(ValueError, match="必須キー 'im_poles'"):
            fixed_required_int(parsed, "im_poles")

    def test_raises_when_value_is_not_integer(self) -> None:
        parsed = _make_parsed(
            {"im_poles": FixedCell(value="4.5", unit=None)},
        )
        with pytest.raises(ValueError, match="整数である必要が"):
            fixed_required_int(parsed, "im_poles")


class TestResolveCableLength:
    """``resolve_cable_length`` の正常・異常系。"""

    def test_returns_zero_when_key_missing(self) -> None:
        parsed = _make_parsed({})
        assert resolve_cable_length(parsed) == (0.0, "m")

    def test_returns_zero_when_value_empty(self) -> None:
        parsed = _make_parsed(
            {"cable_length": FixedCell(value="", unit="m")},
        )
        assert resolve_cable_length(parsed) == (0.0, "m")

    def test_returns_value_and_unit(self) -> None:
        parsed = _make_parsed(
            {"cable_length": FixedCell(value="123.0", unit="ft")},
        )
        assert resolve_cable_length(parsed) == (123.0, "ft")

    def test_defaults_unit_to_meter_when_unit_none(self) -> None:
        parsed = _make_parsed(
            {"cable_length": FixedCell(value="50", unit=None)},
        )
        assert resolve_cable_length(parsed) == (50.0, "m")

    def test_raises_when_value_not_numeric(self) -> None:
        parsed = _make_parsed(
            {"cable_length": FixedCell(value="abc", unit="m")},
        )
        with pytest.raises(ValueError, match="数値である必要が"):
            resolve_cable_length(parsed)

    def test_raises_when_value_is_negative(self) -> None:
        """負値は silent failure を避けるため raise する。"""
        parsed = _make_parsed(
            {"cable_length": FixedCell(value="-100.0", unit="m")},
        )
        with pytest.raises(ValueError, match="非負である必要が"):
            resolve_cable_length(parsed)
