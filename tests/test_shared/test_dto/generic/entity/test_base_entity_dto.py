"""``BaseEntityDto`` のテスト。

カバー対象:
    - 文字列属性での lookup / enumeration / iteration
    - DTO 属性（``get_value()`` を持つ name オブジェクト）での lookup
    - 未知 ID/Name は :class:`ValueError`
    - ``get_all`` がコピーを返すこと
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from im_cable_system.engine.shared.dto.generic.entity import BaseEntityDto


@dataclass(frozen=True)
class _StrIdItem:
    name: str
    payload: int


@dataclass(frozen=True)
class _DtoNameItem:
    name: object  # value-bearing object with .get_value()
    payload: int


class _NameValue:
    """``get_value()`` のみを公開する最小の name 風オブジェクト。"""

    def __init__(self, value: str) -> None:
        self._value = value

    def get_value(self) -> str:
        return self._value


class TestBaseEntityDtoStringAttribute:
    def _make(self) -> BaseEntityDto[_StrIdItem]:
        return BaseEntityDto(
            objects=[
                _StrIdItem(name="A", payload=1),
                _StrIdItem(name="B", payload=2),
                _StrIdItem(name="C", payload=3),
            ],
            attribute_name="name",
        )

    def test_len(self) -> None:
        assert len(self._make()) == 3

    def test_iter_in_order(self) -> None:
        assert [item.payload for item in self._make()] == [1, 2, 3]

    def test_get_by_name(self) -> None:
        coll = self._make()
        assert coll.get_by_name("B").payload == 2

    def test_get_by_id_alias(self) -> None:
        coll = self._make()
        assert coll.get_by_id("C").payload == 3

    def test_get_names(self) -> None:
        assert self._make().get_names() == ["A", "B", "C"]

    def test_get_ids(self) -> None:
        assert self._make().get_ids() == ["A", "B", "C"]

    def test_get_all_returns_copy(self) -> None:
        coll = self._make()
        copy = coll.get_all()
        copy.append(_StrIdItem(name="X", payload=99))
        # 原本は変化していない
        assert len(coll) == 3

    def test_get_by_unknown_raises(self) -> None:
        coll = self._make()
        with pytest.raises(ValueError, match="No item found"):
            coll.get_by_name("missing")


class TestBaseEntityDtoDtoAttribute:
    """``name`` 属性が ``get_value()`` を持つオブジェクトの場合。"""

    def _make(self) -> BaseEntityDto[_DtoNameItem]:
        return BaseEntityDto(
            objects=[
                _DtoNameItem(name=_NameValue("A"), payload=1),
                _DtoNameItem(name=_NameValue("B"), payload=2),
            ],
            attribute_name="name",
        )

    def test_lookup_by_str(self) -> None:
        coll = self._make()
        assert coll.get_by_name("A").payload == 1

    def test_lookup_by_dto_object(self) -> None:
        coll = self._make()
        assert coll.get_by_name(_NameValue("B")).payload == 2

    def test_get_names_uses_get_value(self) -> None:
        coll = self._make()
        assert coll.get_names() == ["A", "B"]

    def test_unknown_raises(self) -> None:
        coll = self._make()
        with pytest.raises(ValueError, match="No item found"):
            coll.get_by_name(_NameValue("missing"))


class TestBaseEntityDtoEmpty:
    def test_empty_collection_has_zero_length(self) -> None:
        coll: BaseEntityDto[_StrIdItem] = BaseEntityDto(
            objects=[], attribute_name="name"
        )
        assert len(coll) == 0
        assert coll.get_names() == []
        assert coll.get_all() == []

    def test_lookup_in_empty_raises(self) -> None:
        coll: BaseEntityDto[_StrIdItem] = BaseEntityDto(
            objects=[], attribute_name="name"
        )
        with pytest.raises(ValueError, match="No item found"):
            coll.get_by_name("anything")
