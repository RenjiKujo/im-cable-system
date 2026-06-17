from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")


class IEntityDtos(ABC, Generic[T]):
    """Interface for entity DTO collections."""

    @abstractmethod
    def get_by_id(self, id_value: str | object) -> T:
        """Return the DTO with the given ID.

        Args:
            id_value: ID of the DTO to retrieve. May be a string or a DTO
                object that implements ``get_value()``.
        """
        pass

    @abstractmethod
    def get_ids(self) -> list[str]:
        """Return the list of DTO IDs.

        Returns:
            list[str]: List of DTO IDs. When the id attribute is a DTO object
                with ``get_value()``, it is converted to a string automatically.
        """
        pass

    @abstractmethod
    def get_by_name(self, name_value: str | object) -> T:
        """Return the DTO with the given name.

        Args:
            name_value: Name of the DTO to retrieve. May be a string or a DTO
                object that implements ``get_value()``.
        """
        pass

    @abstractmethod
    def get_names(self) -> list[str]:
        """Return the list of DTO names.

        Returns:
            list[str]: List of DTO names. When the name attribute is a DTO
                object with ``get_value()``, it is converted to a string
                automatically.
        """
        pass
