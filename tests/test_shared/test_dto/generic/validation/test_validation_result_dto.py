"""Tests for :class:`ValidationResultDto`.

成功/失敗 DTO の生成正常系と、``__post_init__`` で課される整合性ルール
（失敗時は message 必須）を担保する。frozen であることも確認する。
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from im_cable_system.engine.shared.dto.generic.validation import (
    ValidationResultDto,
)


class TestValidationResultDtoSuccess:
    """成功ケースの構築。"""

    def test_success_dto(self) -> None:
        dto = ValidationResultDto(
            is_valid=True,
            message="",
        )
        assert dto.is_valid is True
        assert dto.message == ""


class TestValidationResultDtoFailure:
    """失敗ケースの構築。"""

    def test_failure_dto_with_message(self) -> None:
        dto = ValidationResultDto(
            is_valid=False,
            message="3 outliers detected",
        )
        assert dto.is_valid is False
        assert dto.message == "3 outliers detected"


class TestValidationResultDtoConstraints:
    """``__post_init__`` の不変条件違反。"""

    def test_failure_without_message_raises(self) -> None:
        with pytest.raises(ValueError, match="message is required"):
            ValidationResultDto(
                is_valid=False,
                message="",
            )


class TestValidationResultDtoIsFrozen:
    """凍結 dataclass であることの担保。"""

    def test_assignment_raises(self) -> None:
        dto = ValidationResultDto(
            is_valid=True,
            message="",
        )
        with pytest.raises(FrozenInstanceError):
            dto.is_valid = False  # type: ignore[misc]
