"""Base implementation for entity DTO collections."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Generic, TypeVar

from im_cable_system.engine.shared.dto.generic.interfaces.i_dto import (
    IEntityDtos,
)

T = TypeVar("T")


class BaseEntityDto(Generic[T], IEntityDtos[T]):
    """Base class for DTO entity collections.

    Provides common DTO operations. Special methods enable list-like usage.
    """

    def __init__(self, objects: list[T], attribute_name: str) -> None:
        """Initialize the collection.

        Args:
            objects: Initial list of DTO objects.
            attribute_name: Identifier attribute on each object
                (e.g. ``id`` or ``name``).
        """
        self._objects = objects
        self._attribute_name = attribute_name

    def __len__(self) -> int:
        """Return the number of objects.

        Returns:
            int: Number of objects.
        """
        return len(self._objects)

    def __iter__(self) -> Iterator[T]:
        """Return an iterator over objects.

        Returns:
            Iterator[T]: Iterator over contained objects.
        """
        return iter(self._objects)

    def get_by_id(self, id_value: str | object) -> T:
        """Return the DTO with the given ID.

        Args:
            id_value: ID of the DTO to retrieve. May be a string or a DTO
                object that implements ``get_value()``.

        Returns:
            T: DTO with the specified ID.

        Raises:
            ValueError: If no DTO with the specified ID exists.
        """
        search_value = self._extract_string_value(id_value)
        return self._get_from_list(
            self._objects, search_value, attribute_name=self._attribute_name
        )

    def _extract_string_value(self, attr_value: object) -> str:
        """Extract a string value from an attribute value.

        Args:
            attr_value: Attribute value (string or DTO object).

        Returns:
            str: String representation of the value.
        """
        if hasattr(attr_value, "get_value"):
            return attr_value.get_value()
        if isinstance(attr_value, str):
            return attr_value
        return str(attr_value)

    def _get_from_list(
        self, items: list[T], attribute_value: str, attribute_name: str
    ) -> T:
        """Return the item in ``items`` with the given attribute value.

        Args:
            items: List to search.
            attribute_value: Attribute value to match.
            attribute_name: Name of the attribute to compare.

        Returns:
            T: Item with the specified attribute value.

        Raises:
            ValueError: If no matching item exists.
        """
        for item in items:
            if hasattr(item, attribute_name):
                attr_value = getattr(item, attribute_name)
                if hasattr(attr_value, "get_value"):
                    if attr_value.get_value() == attribute_value:
                        return item
                elif attr_value == attribute_value:
                    return item

        raise ValueError(
            f"No item found with attribute '{attribute_name}' "
            f"equal to '{attribute_value}'"
        )

    def get_ids(self) -> list[str]:
        """Return the list of DTO IDs.

        Returns:
            list[str]: List of DTO IDs.
        """
        result = []
        for obj in self._objects:
            if hasattr(obj, self._attribute_name):
                attr_value = getattr(obj, self._attribute_name)
                result.append(self._extract_string_value(attr_value))
        return result

    def get_by_name(self, name_value: str | object) -> T:
        """Return the DTO with the given name.

        Args:
            name_value: Name of the DTO to retrieve.

        Returns:
            T: DTO with the specified name.

        Raises:
            ValueError: If no DTO with the specified name exists.
        """
        search_value = self._extract_string_value(name_value)
        return self._get_from_list(
            self._objects, search_value, attribute_name=self._attribute_name
        )

    def get_names(self) -> list[str]:
        """Return the list of DTO names.

        Returns:
            list[str]: List of DTO names.
        """
        result = []
        for obj in self._objects:
            if hasattr(obj, self._attribute_name):
                attr_value = getattr(obj, self._attribute_name)
                result.append(self._extract_string_value(attr_value))
        return result

    def get_all(self) -> list[T]:
        """Return all contained objects.

        Returns:
            list[T]: Copy of all DTO objects.
        """
        return self._objects.copy()
