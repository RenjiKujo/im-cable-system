"""Unit-aware DTOs for efficiency (dimensionless or percent)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from im_cable_system.engine.shared.dto.generic.interfaces.i_value_with_unit_dto import (
    IArrayWithUnitDto,
    IFloatWithUnitDto,
)

EFFICIENCY_FACTORS: dict[str, float] = {
    "%": 1.0,
    "-": 1.0,
}


@dataclass(frozen=True)
class FloatEfficiencyDto(IFloatWithUnitDto):
    """Scalar efficiency DTO.

    Attributes:
        value: Efficiency. For unit ``"-"``, range 0.0–1.0; for ``"%"``,
            range 0–100.
        unit: ``"-"`` (dimensionless) or ``"%"``.
    """

    value: float
    unit: str = "-"

    def __post_init__(self) -> None:
        """Validate the instance."""
        if not isinstance(self.value, (int, float)):
            raise ValueError("efficiency value must be numeric")
        if not np.isfinite(self.value):
            raise ValueError("efficiency value must not contain NaN/inf")

        valid_units = list(EFFICIENCY_FACTORS.keys())
        if self.unit not in valid_units:
            raise ValueError(f"invalid efficiency unit: {self.unit}")

        if self.unit == "-":
            if self.value < 0.0 or self.value > 1.0:
                raise ValueError(
                    "efficiency must be between 0.0 and 1.0 inclusive"
                )
        elif self.value < 0.0 or self.value > 100.0:
            raise ValueError("efficiency must be between 0 and 100 inclusive")

    def get_value(self) -> float:
        """Return the efficiency value."""
        return self.value

    def get_unit(self) -> str:
        """Return the efficiency unit."""
        return self.unit

    def to_base_unit(self) -> FloatEfficiencyDto:
        """Convert to the base unit (``"-"``, dimensionless)."""
        if self.unit == "-":
            return self
        base_value = self.value if self.unit == "-" else (self.value / 100.0)
        return FloatEfficiencyDto(value=base_value, unit="-")

    def convert_to_unit(self, target_unit: str) -> FloatEfficiencyDto:
        """Return a new DTO in the requested unit."""
        if target_unit not in ("-", "%"):
            raise ValueError(f"invalid efficiency unit: {target_unit}")
        if target_unit == self.unit:
            return self

        base = self.to_base_unit().value
        if target_unit == "-":
            return FloatEfficiencyDto(value=base, unit="-")
        return FloatEfficiencyDto(value=base * 100.0, unit="%")


@dataclass(frozen=True)
class ArrayEfficiencyDto(IArrayWithUnitDto):
    """Array efficiency DTO.

    Attributes:
        value: Efficiency array. For unit ``"-"``, each element in 0.0–1.0;
            for ``"%"``, each element in 0–100.
        unit: ``"-"`` (dimensionless) or ``"%"``.
    """

    value: np.ndarray
    unit: str = "-"

    def __post_init__(self) -> None:
        """Validate the instance."""
        arr = np.asarray(self.value, dtype=np.float64)
        if arr.size == 0:
            raise ValueError("efficiency array must not be empty")
        if not np.all(np.isfinite(arr)):
            raise ValueError("efficiency array must not contain NaN/inf")
        object.__setattr__(self, "value", arr)

        valid_units = list(EFFICIENCY_FACTORS.keys())
        if self.unit not in valid_units:
            raise ValueError(f"invalid efficiency unit: {self.unit}")

        if self.unit == "-":
            if np.any((arr < 0.0) | (arr > 1.0)):
                raise ValueError(
                    "finite efficiency elements must be between 0.0 and 1.0"
                )
        elif np.any((arr < 0.0) | (arr > 100.0)):
            raise ValueError(
                "finite efficiency elements must be between 0 and 100"
            )

    def get_value(self) -> np.ndarray:
        """Return the efficiency array."""
        return self.value

    def get_unit(self) -> str:
        """Return the efficiency unit."""
        return self.unit

    def get_shape(self) -> tuple[int, ...]:
        """Return the array shape."""
        return self.value.shape

    def get_ndim(self) -> int:
        """Return the number of dimensions."""
        return self.value.ndim

    def to_base_unit(self) -> ArrayEfficiencyDto:
        """Convert to the base unit (``"-"``, dimensionless)."""
        if self.unit == "-":
            return self
        base_value = self.value if self.unit == "-" else (self.value / 100.0)
        return ArrayEfficiencyDto(value=base_value, unit="-")

    def convert_to_unit(self, target_unit: str) -> ArrayEfficiencyDto:
        """Return a new DTO in the requested unit."""
        if target_unit not in ("-", "%"):
            raise ValueError(f"invalid efficiency unit: {target_unit}")
        if target_unit == self.unit:
            return self

        base = self.to_base_unit().value
        if target_unit == "-":
            return ArrayEfficiencyDto(value=base, unit="-")
        return ArrayEfficiencyDto(value=base * 100.0, unit="%")
