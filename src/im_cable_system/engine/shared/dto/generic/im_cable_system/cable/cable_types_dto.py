from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class CableShapeType(str, Enum):
    """Cable shape type enumeration.

    Common cable shapes are ROUND and FLAT only; the contract is fixed via
    Enum rather than free-form strings.
    """

    ROUND = "ROUND"
    FLAT = "FLAT"


@dataclass(frozen=True)
class CableShapeTypeDto:
    """DTO for cable shape type.

    Attributes:
        value: Cable shape type (FLAT or ROUND).
    """

    value: CableShapeType | str

    def __post_init__(self) -> None:
        """Validate and normalize the shape type."""
        if isinstance(self.value, CableShapeType):
            return

        if not isinstance(self.value, str) or len(self.value) == 0:
            raise ValueError(
                f"Cable shape type must be a non-empty string: {self.value}"
            )
        try:
            normalized = CableShapeType(self.value)
        except ValueError as e:
            valid_shapes = [shape.value for shape in CableShapeType]
            raise ValueError(
                f"Cable shape type must be one of {valid_shapes}: {self.value}"
            ) from e

        object.__setattr__(self, "value", normalized)

    def get_value(self) -> str:
        """Return the cable shape type as a string."""
        if isinstance(self.value, CableShapeType):
            return self.value.value
        return self.value
