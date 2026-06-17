"""IM/cable system name DTO 群のバリデーションテスト。

カバー対象:
    - ``ImName`` / ``ImSeriesName`` / ``ImCableSystemName``
    - ``CableName`` / ``CableSectionName`` / ``CableSeriesName``

すべて ``BaseNameId`` を継承しており、``validate_non_blank_after_strip``
で「空文字 / 空白のみ拒否」を共通契約として持つ。
"""

from __future__ import annotations

import pytest

from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    CableName,
    CableSectionName,
    CableSeriesName,
    ImCableSystemName,
    ImName,
    ImSeriesName,
)


class TestImName:
    def test_valid_accepted(self) -> None:
        assert ImName(value="MOTOR_A").get_value() == "MOTOR_A"

    def test_empty_rejected(self) -> None:
        with pytest.raises(ValueError, match="induction motor name"):
            ImName(value="")

    def test_whitespace_only_rejected(self) -> None:
        with pytest.raises(ValueError, match="induction motor name"):
            ImName(value="   ")


class TestImSeriesName:
    def test_valid_accepted(self) -> None:
        assert ImSeriesName(value="SERIES_X").get_value() == "SERIES_X"

    def test_factory(self) -> None:
        assert ImSeriesName.create("SERIES_X").get_value() == "SERIES_X"

    def test_empty_rejected(self) -> None:
        with pytest.raises(ValueError, match="IM series name"):
            ImSeriesName(value="")


class TestImCableSystemName:
    def test_valid_accepted(self) -> None:
        ImCableSystemName(value="SYS-01")

    def test_empty_rejected(self) -> None:
        with pytest.raises(ValueError, match="IM cable system name"):
            ImCableSystemName(value="")


class TestCableName:
    def test_valid_accepted(self) -> None:
        CableName(value="MAIN")

    def test_empty_rejected(self) -> None:
        with pytest.raises(ValueError, match="cable name"):
            CableName(value="")


class TestCableSectionName:
    def test_valid_accepted(self) -> None:
        CableSectionName(value="SECTION_01")

    def test_empty_rejected(self) -> None:
        with pytest.raises(ValueError, match="cable section name"):
            CableSectionName(value="")


class TestCableSeriesName:
    def test_valid_accepted(self) -> None:
        CableSeriesName(value="SERIES_X")

    def test_empty_rejected(self) -> None:
        with pytest.raises(ValueError, match="cable series name"):
            CableSeriesName(value="")


class TestNameTypeIsolation:
    """異なる name 型同士は等価ではない（type identity 重要）。"""

    def test_im_name_not_equal_to_im_series_name(self) -> None:
        # BaseNameId の __eq__ は type が完全一致のときのみ True を返す。
        # ただし str との等価比較は許すため、片方が str ラッパでも同じ
        # value 同士なら == "value" 経由ではなく型一致が必要となる。
        a = ImName(value="X")
        b = ImSeriesName(value="X")
        assert a != b
        assert a == "X"
        assert b == "X"
