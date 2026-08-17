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
    """``base`` / ``discriminator`` の合成と、表示用・識別子用の使い分け。"""

    def test_valid_accepted(self) -> None:
        ImCableSystemName(base="SYS-01")

    def test_empty_base_rejected(self) -> None:
        with pytest.raises(ValueError, match="IM cable system base name"):
            ImCableSystemName(base="")

    def test_value_without_discriminator_equals_base(self) -> None:
        """discriminator 無し（forward 相当）では value == base。"""
        name = ImCableSystemName(base="SYS-01")
        assert name.get_value() == "SYS-01"
        assert name.get_base() == "SYS-01"

    def test_value_with_discriminator_appends_suffix(self) -> None:
        """discriminator 有り（estimate_params 相当）では value != base。"""
        name = ImCableSystemName(base="SYS-01", discriminator="1_1_1_0_0_1_1_0")
        assert name.get_value() == "SYS-01_1_1_1_0_0_1_1_0"
        assert name.get_base() == "SYS-01"

    def test_empty_discriminator_rejected(self) -> None:
        with pytest.raises(
            ValueError, match="IM cable system name discriminator"
        ):
            ImCableSystemName(base="SYS-01", discriminator="")

    def test_candidates_sharing_base_differ_by_value(self) -> None:
        """同一 base を共有する複数候補は value（識別子）で一意に区別される。"""
        candidate_1 = ImCableSystemName(base="SYS-01", discriminator="1_1")
        candidate_2 = ImCableSystemName(base="SYS-01", discriminator="1_2")
        assert candidate_1.get_base() == candidate_2.get_base()
        assert candidate_1.get_value() != candidate_2.get_value()
        assert candidate_1 != candidate_2


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
