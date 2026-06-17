"""``BaseNameId`` 共通実装と name バリデータのテスト。

内部実装の単体テスト。``generic.im_cable_system.base`` は非公開パッケージのため
リーフ直 import とする。

カバー対象:
    - ``BaseNameId`` の ``__eq__`` / ``__hash__`` / ``__str__`` / ``get_value``
    - ``validate_non_blank_after_strip``
    - ``validate_non_empty_string``
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from im_cable_system.engine.shared.dto.generic.im_cable_system.base.base_name_id import (  # noqa: E501
    BaseNameId,
    validate_non_blank_after_strip,
    validate_non_empty_string,
)


@dataclass(frozen=True, eq=False)
class _DummyName(BaseNameId):
    """テスト用の最小実装。"""

    value: str


class TestBaseNameIdBehavior:
    def test_get_value(self) -> None:
        assert _DummyName(value="abc").get_value() == "abc"

    def test_str_returns_value(self) -> None:
        assert str(_DummyName(value="abc")) == "abc"

    def test_equal_with_same_type(self) -> None:
        a = _DummyName(value="abc")
        b = _DummyName(value="abc")
        assert a == b

    def test_equal_with_str(self) -> None:
        # BaseNameId は str との等価比較を許す
        assert _DummyName(value="abc") == "abc"

    def test_not_equal_with_different_string(self) -> None:
        assert _DummyName(value="abc") != "xyz"

    def test_not_equal_with_other_object(self) -> None:
        assert _DummyName(value="abc") != 123

    def test_hash_consistent_with_value(self) -> None:
        assert hash(_DummyName(value="abc")) == hash("abc")

    def test_hashable_and_usable_as_dict_key(self) -> None:
        d = {_DummyName(value="a"): 1}
        assert d[_DummyName(value="a")] == 1


class TestValidateNonBlankAfterStrip:
    def test_valid_accepted(self) -> None:
        validate_non_blank_after_strip("abc", "field")

    def test_empty_rejected(self) -> None:
        with pytest.raises(
            ValueError, match="field must be a non-empty string"
        ):
            validate_non_blank_after_strip("", "field")

    def test_whitespace_only_rejected(self) -> None:
        with pytest.raises(
            ValueError, match="field must be a non-empty string"
        ):
            validate_non_blank_after_strip("   ", "field")

    def test_non_string_rejected(self) -> None:
        with pytest.raises(
            ValueError, match="field must be a non-empty string"
        ):
            validate_non_blank_after_strip(None, "field")  # type: ignore[arg-type]


class TestValidateNonEmptyString:
    def test_valid_accepted(self) -> None:
        validate_non_empty_string("abc", "field")

    def test_whitespace_only_accepted(self) -> None:
        # blank と異なり、空白文字のみは許容される
        validate_non_empty_string("   ", "field")

    def test_empty_rejected(self) -> None:
        with pytest.raises(
            ValueError, match="field must be a non-empty string"
        ):
            validate_non_empty_string("", "field")

    def test_non_string_rejected(self) -> None:
        with pytest.raises(
            ValueError, match="field must be a non-empty string"
        ):
            validate_non_empty_string(None, "field")  # type: ignore[arg-type]
