"""Cable series name identifier."""

from __future__ import annotations

from dataclasses import dataclass

from im_cable_system.engine.shared.dto.generic.im_cable_system.base.base_name_id import (  # noqa: E501
    BaseNameId,
    validate_non_blank_after_strip,
)


@dataclass(frozen=True, eq=False)
class CableSeriesName(BaseNameId):
    """Cable series name."""

    value: str

    def __post_init__(self) -> None:
        """Validate the name value."""
        validate_non_blank_after_strip(self.value, "cable series name")
