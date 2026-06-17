"""IM series name identifier."""

from __future__ import annotations

from dataclasses import dataclass

from im_cable_system.engine.shared.dto.generic.im_cable_system.base.base_name_id import (  # noqa: E501
    BaseNameId,
    validate_non_blank_after_strip,
)


@dataclass(frozen=True, eq=False)
class ImSeriesName(BaseNameId):
    """Induction motor series name; holds a catalog or input series key."""

    value: str

    def __post_init__(self) -> None:
        """Validate the name value."""
        validate_non_blank_after_strip(self.value, "IM series name")

    @classmethod
    def create(cls, value: str) -> ImSeriesName:
        """Create an instance."""
        return cls(value=value)
