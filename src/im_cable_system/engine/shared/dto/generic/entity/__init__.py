"""Base types for entity DTO collections (public export).

Responsibilities:
  - Lookup and enumeration of DTO lists by name or ID (``BaseEntityDto``).

Implementation lives in ``entity_collections``. For cross-layer use,
import symbols from this package's ``__all__``.
"""

from im_cable_system.engine.shared.dto.generic.entity.entity_collections import (
    BaseEntityDto,
)

__all__ = [
    "BaseEntityDto",
]
