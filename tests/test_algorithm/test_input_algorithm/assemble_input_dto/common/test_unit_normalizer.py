"""共通 ``unit_normalizer`` の純粋関数テスト。

``normalize_loaded_unit_cell`` は LoadedData の単位セル
（例: ``[m]``）から外側角括弧だけ剥がす純粋関数。
LoadData 段の ``strip()`` 残し方針と DTO 段の単位値域チェックの
境界を担うため、文字列処理の角ケースをここで網羅的に固定する。
"""

from __future__ import annotations

import pytest

from im_cable_system.engine.algorithm.input_algorithm.assemble_input_dto.common.unit_normalizer import (  # noqa: E501
    normalize_loaded_unit_cell,
)


class TestNormalizeLoadedUnitCellBracketStripping:
    """外側 ``[...]`` の剥がし。"""

    def test_brackets_around_short_unit_are_stripped(self) -> None:
        assert normalize_loaded_unit_cell("[m]") == "m"

    def test_brackets_around_multichar_unit_are_stripped(self) -> None:
        assert normalize_loaded_unit_cell("[rpm]") == "rpm"

    def test_brackets_around_compound_unit_are_stripped(self) -> None:
        assert normalize_loaded_unit_cell("[N*m]") == "N*m"


class TestNormalizeLoadedUnitCellStripping:
    """外側スペースの ``strip()``。"""

    def test_outer_whitespace_is_stripped_without_brackets(self) -> None:
        assert normalize_loaded_unit_cell("  Nm  ") == "Nm"

    def test_outer_whitespace_around_brackets_is_stripped(self) -> None:
        assert normalize_loaded_unit_cell("  [rpm]  ") == "rpm"

    def test_inner_whitespace_inside_brackets_is_stripped(self) -> None:
        assert normalize_loaded_unit_cell("[  rpm  ]") == "rpm"


class TestNormalizeLoadedUnitCellPassThrough:
    """角括弧の無い文字列は ``strip()`` のみで素通り。"""

    def test_no_bracket_unit_passes_through(self) -> None:
        assert normalize_loaded_unit_cell("Nm") == "Nm"

    def test_empty_string_stays_empty(self) -> None:
        assert normalize_loaded_unit_cell("") == ""

    def test_whitespace_only_collapses_to_empty(self) -> None:
        assert normalize_loaded_unit_cell("   ") == ""

    def test_partial_brackets_are_kept(self) -> None:
        """前後のうち片側だけの ``[`` / ``]`` は剥がさない。"""
        assert normalize_loaded_unit_cell("[m") == "[m"
        assert normalize_loaded_unit_cell("m]") == "m]"


class TestNormalizeLoadedUnitCellEdgeCases:
    """角ケースの安定挙動を固定する。"""

    def test_empty_brackets_collapse_to_empty(self) -> None:
        """``[]`` は内側空文字に正規化される。"""
        assert normalize_loaded_unit_cell("[]") == ""

    def test_brackets_with_whitespace_only_collapse_to_empty(self) -> None:
        """``[   ]`` も内側を strip して空文字に正規化される。"""
        assert normalize_loaded_unit_cell("[   ]") == ""

    @pytest.mark.parametrize(
        "raw, expected",
        [
            ("[V]", "V"),
            ("[Hz]", "Hz"),
            ("[Ω]", "Ω"),
            ("[Nm]", "Nm"),
            ("[rad/s]", "rad/s"),
            ("[-]", "-"),
            ("[%]", "%"),
        ],
    )
    def test_typical_loaded_units_normalize(
        self, raw: str, expected: str
    ) -> None:
        """LoadedData で典型的に現れる単位がすべて素直に剥がれる。"""
        assert normalize_loaded_unit_cell(raw) == expected
