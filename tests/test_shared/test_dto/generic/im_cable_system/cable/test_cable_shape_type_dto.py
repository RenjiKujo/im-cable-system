"""``CableShapeTypeDto`` の正規化と検証テスト。"""

from __future__ import annotations

import pytest

from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    CableShapeType,
    CableShapeTypeDto,
)


class TestCableShapeTypeDto:
    def test_enum_value_accepted(self) -> None:
        dto = CableShapeTypeDto(value=CableShapeType.ROUND)
        assert dto.get_value() == "ROUND"

    def test_string_value_normalized(self) -> None:
        dto = CableShapeTypeDto(value="FLAT")
        # __post_init__ 内で frozen dataclass への object.__setattr__ で
        # CableShapeType に正規化される
        assert dto.get_value() == "FLAT"
        assert isinstance(dto.value, CableShapeType)

    def test_empty_string_rejected(self) -> None:
        with pytest.raises(ValueError, match="non-empty string"):
            CableShapeTypeDto(value="")

    def test_invalid_value_rejected(self) -> None:
        with pytest.raises(ValueError, match=r"\['ROUND', 'FLAT'\]"):
            CableShapeTypeDto(value="OVAL")

    def test_get_value_returns_string(self) -> None:
        dto = CableShapeTypeDto(value=CableShapeType.ROUND)
        assert isinstance(dto.get_value(), str)


class TestCableShapeType:
    def test_round_value(self) -> None:
        assert CableShapeType.ROUND.value == "ROUND"

    def test_flat_value(self) -> None:
        assert CableShapeType.FLAT.value == "FLAT"

    def test_str_subclass(self) -> None:
        # CableShapeType は str 派生 Enum なので str との等価比較が可能
        assert CableShapeType.ROUND == "ROUND"
