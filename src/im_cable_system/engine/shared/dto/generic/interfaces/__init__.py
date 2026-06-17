"""DTO interface layer (public export).

Bundles leaf modules that define contracts (interfaces) for DTOs. For cross-layer
use, import from this package's ``__all__``.

Direct import from implementation modules (e.g. ``i_dto``) is allowed only
within the same ``interfaces`` tree.
"""

from im_cable_system.engine.shared.dto.generic.interfaces.i_dto import (
    IEntityDtos,
)
from im_cable_system.engine.shared.dto.generic.interfaces.i_entity_identifier import (  # noqa: E501
    IEntityIdentifier,
)
from im_cable_system.engine.shared.dto.generic.interfaces.i_event_dto import (
    IEventDto,
)
from im_cable_system.engine.shared.dto.generic.interfaces.i_value_with_unit_dto import (
    IArrayWithUnitDto,
    IFloatWithUnitDto,
)

__all__ = [
    "IArrayWithUnitDto",
    "IEntityDtos",
    "IEntityIdentifier",
    "IEventDto",
    "IFloatWithUnitDto",
]
