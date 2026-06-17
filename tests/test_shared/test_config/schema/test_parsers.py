"""Tests for schema internal parsers (``_parsers``).

内部実装の単体テスト。``schema/_parsers`` は config 窓口に載せない非公開
モジュールのためリーフ直 import とする。
"""

from __future__ import annotations

import math
from enum import Enum

import pytest

from im_cable_system.engine.shared.config.schema._parsers import (
    parse_bool,
    parse_dict,
    parse_enum,
    parse_float,
    parse_int,
    parse_required_str,
)


class _SeverityForTest(str, Enum):
    A = "A"
    B = "B"


class TestParseDict:
    def test_none_returns_empty_dict(self) -> None:
        assert parse_dict(None, key_path="x") == {}

    def test_dict_returned_as_is(self) -> None:
        assert parse_dict({"k": 1}, key_path="x") == {"k": 1}

    def test_non_dict_raises(self) -> None:
        with pytest.raises(ValueError, match="x は dict"):
            parse_dict("not-a-dict", key_path="x")


class TestParseRequiredStr:
    def test_missing_without_default_raises(self) -> None:
        with pytest.raises(ValueError, match="は必須"):
            parse_required_str(None, key_path="k")

    def test_missing_uses_default(self) -> None:
        assert parse_required_str(None, key_path="k", default="d") == "d"

    def test_choices_violation_raises(self) -> None:
        with pytest.raises(ValueError, match="のいずれか"):
            parse_required_str("c", key_path="k", choices=("a", "b"))

    def test_choices_passes(self) -> None:
        assert parse_required_str("a", key_path="k", choices=("a", "b")) == "a"


class TestParseInt:
    def test_basic_int(self) -> None:
        assert parse_int(3, key_path="k") == 3

    def test_string_int_is_accepted(self) -> None:
        assert parse_int("3", key_path="k") == 3

    def test_default_used_when_missing(self) -> None:
        assert parse_int(None, key_path="k", default=7) == 7

    def test_missing_without_default_raises(self) -> None:
        with pytest.raises(ValueError, match="は必須"):
            parse_int(None, key_path="k")

    def test_bool_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="bool を受け取り"):
            parse_int(True, key_path="k", default=1)

    def test_non_numeric_raises(self) -> None:
        with pytest.raises(ValueError, match="整数に変換可能"):
            parse_int("not-an-int", key_path="k", default=1)

    def test_positive_violation_raises(self) -> None:
        with pytest.raises(ValueError, match="正の整数"):
            parse_int(0, key_path="k", positive=True)

    def test_allow_none_returns_none(self) -> None:
        assert parse_int(None, key_path="k", allow_none=True) is None


class TestParseFloat:
    def test_basic_float(self) -> None:
        assert parse_float(1.5, key_path="k") == pytest.approx(1.5)

    def test_default_used_when_missing(self) -> None:
        assert parse_float(None, key_path="k", default=2.0) == pytest.approx(
            2.0,
        )

    def test_bool_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="bool を受け取り"):
            parse_float(True, key_path="k", default=1.0)

    def test_non_numeric_raises(self) -> None:
        with pytest.raises(ValueError, match="数値に変換可能"):
            parse_float("nope", key_path="k", default=1.0)

    def test_positive_violation_raises(self) -> None:
        with pytest.raises(ValueError, match="正の数値"):
            parse_float(0.0, key_path="k", positive=True)

    def test_non_negative_violation_raises(self) -> None:
        with pytest.raises(ValueError, match="非負"):
            parse_float(-0.1, key_path="k", non_negative=True)

    def test_finite_violation_raises(self) -> None:
        with pytest.raises(ValueError, match="有限値"):
            parse_float(math.inf, key_path="k")

    def test_allow_none_returns_none(self) -> None:
        assert parse_float(None, key_path="k", allow_none=True) is None


class TestParseBool:
    def test_basic_bool(self) -> None:
        assert parse_bool(True, key_path="k") is True
        assert parse_bool(False, key_path="k") is False

    def test_default_used_when_missing(self) -> None:
        assert parse_bool(None, key_path="k", default=True) is True

    def test_missing_without_default_raises(self) -> None:
        with pytest.raises(ValueError, match="は必須"):
            parse_bool(None, key_path="k")

    def test_non_bool_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="bool"):
            parse_bool("true", key_path="k", default=False)


class TestParseEnum:
    def test_value_string_converts(self) -> None:
        assert (
            parse_enum("A", _SeverityForTest, key_path="k")
            is _SeverityForTest.A
        )

    def test_default_used_when_missing(self) -> None:
        assert (
            parse_enum(
                None,
                _SeverityForTest,
                key_path="k",
                default=_SeverityForTest.B,
            )
            is _SeverityForTest.B
        )

    def test_strip_whitespace(self) -> None:
        assert (
            parse_enum("  A  ", _SeverityForTest, key_path="k")
            is _SeverityForTest.A
        )

    def test_unknown_value_raises(self) -> None:
        with pytest.raises(ValueError, match="のいずれか"):
            parse_enum("X", _SeverityForTest, key_path="k")

    def test_missing_without_default_raises(self) -> None:
        with pytest.raises(ValueError, match="は必須"):
            parse_enum(None, _SeverityForTest, key_path="k")
