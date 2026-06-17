"""Event DTO interface module.

Defines the base DTO interface for timestamped domain events in the simulation
engine.

## Category

This module defines interfaces for the **event DTO** category. Event DTOs hold
occurrence time, name, and optional metadata under a shared contract.

## Rationale

This interface exists because:

1. **Interface-driven design**: Every implementation class implements an
   interface so callers depend on contracts, not concrete types.

2. **Type safety**: Interfaces let type checkers verify that implementations
   expose required attributes and methods.

3. **Extensibility**: New event types can be added as new implementation classes
   without changing existing code.

4. **Clear contract**: Event DTO obligations (attributes and methods) are
   explicit, keeping implementations consistent.

## Why not use ``@dataclass``

This interface inherits from ``ABC`` only, not ``@dataclass``, because:

1. **Role of interfaces**: Interfaces define contracts (method signatures), not
   data-structure details. Implementations use ``@dataclass(frozen=True)`` for
   their fields.

2. **Separation of contract and data**: Interfaces declare abstract methods
   only; concrete data layout belongs in implementation classes.

3. **Flexibility**: Without ``@dataclass`` on the interface, implementations
   can choose different data shapes and initialization.

4. **Avoiding errors**: Putting ``@dataclass`` on an interface forces attribute
   redefinition in subclasses and can cause type or field-order issues. ``ABC``
   alone avoids that.

Implementations use ``@dataclass(frozen=True)`` for data and implement this
interface's abstract methods.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime  # noqa: F401

    from im_cable_system.engine.shared.dto.generic.interfaces.i_entity_identifier import (  # noqa: E501, F401
        IEntityIdentifier,
    )


class IEventDto(ABC):  # noqa: B024
    """Interface for event DTOs.

    All event DTOs implement this interface and carry basic event information
    (name and occurrence datetime).

    Attributes:
        name (IEntityIdentifier): Event name. Must be an ``IEntityIdentifier``
            implementation.
        event_datetime (datetime): Event occurrence time. Use 00:00:00 on that
            day when the time is unknown.
        description (str | None): Optional event description.
        metadata (dict[str, str] | None): Optional key-value metadata.
    """

    @abstractmethod
    def get_name(self) -> IEntityIdentifier:
        """Return the event name.

        Returns:
            IEntityIdentifier: Event name.
        """
        raise NotImplementedError

    @abstractmethod
    def get_event_datetime(self) -> datetime:
        """Return the event occurrence datetime.

        Returns:
            datetime: Event occurrence datetime.
        """
        raise NotImplementedError

    @abstractmethod
    def get_description(self) -> str | None:
        """Return the event description.

        Returns:
            str | None: Event description.
        """
        raise NotImplementedError

    @abstractmethod
    def get_metadata(self) -> dict[str, str] | None:
        """Return optional event metadata.

        Returns:
            dict[str, str] | None: Additional metadata.
        """
        raise NotImplementedError
