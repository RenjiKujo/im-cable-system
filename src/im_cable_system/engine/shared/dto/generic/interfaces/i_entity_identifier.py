"""Entity identifier interface.

Defines a generic interface for entity identifiers (name or id). Implementations
must expose ``get_value()`` returning a string for compatibility with
``BaseEntityDto``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class IEntityIdentifier(ABC):
    """Interface for entity identifiers.

    Generic contract for identifiers such as name or id. Implementations must
    provide ``get_value()`` returning a string for use with ``BaseEntityDto``.

    Implementations enable unified handling of identifiers such as:
    - IM series names (``ImSeriesName``)
    - IM cable system names (``ImCableSystemName``)
    - Cable series names (``CableSeriesName``)
    - Other name/id attributes in the catalog and simulation DTOs
    """

    @abstractmethod
    def get_value(self) -> str:
        """Return the identifier as a string.

        Required for ``BaseEntityDto`` compatibility; used by
        ``BaseEntityDto.get_by_id()`` and ``get_by_name()``.

        Returns:
            str: String value of the identifier.
        """
        pass

    @abstractmethod
    def __eq__(self, other: object) -> bool:
        """Test equality.

        Args:
            other: Object to compare. May be another ``IEntityIdentifier``,
                a string, or another type.

        Returns:
            bool: True if equal, False otherwise.
        """
        pass

    @abstractmethod
    def __hash__(self) -> int:
        """Return the hash value.

        Returns:
            int: Hash value.
        """
        pass

    def __str__(self) -> str:
        """Return the string representation.

        Returns:
            str: String value of the identifier.
        """
        return self.get_value()
