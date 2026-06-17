"""Unit-aware DTOs for rotational speed."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from im_cable_system.engine.shared.dto.generic.interfaces.i_value_with_unit_dto import (
    IArrayWithUnitDto,
    IFloatWithUnitDto,
)

ROTATIONAL_SPEED_FACTORS: dict[str, float] = {
    "rad/s": 1.0,
    "rpm": 9.5492965855,
}


@dataclass(frozen=True)
class FloatRotationalSpeedDto(IFloatWithUnitDto):
    """Scalar rotational speed DTO.

    Attributes:
        value: Rotational speed (non-negative).
        unit: ``rad/s`` or ``rpm``.
    """

    value: float
    unit: str = "rad/s"

    def __post_init__(self) -> None:
        """Validate the instance."""
        if not isinstance(self.value, (int, float)):
            raise ValueError("rotational speed value must be numeric")
        if not np.isfinite(self.value):
            raise ValueError("rotational speed value must not contain NaN/inf")
        if self.value < 0:
            raise ValueError("rotational speed must be non-negative")

        valid_units = list(ROTATIONAL_SPEED_FACTORS.keys())
        if self.unit not in valid_units:
            raise ValueError(f"invalid rotational speed unit: {self.unit}")

    def get_value(self) -> float:
        """Return the rotational speed value."""
        return self.value

    def get_unit(self) -> str:
        """Return the rotational speed unit."""
        return self.unit

    def to_base_unit(self) -> FloatRotationalSpeedDto:
        """Convert to the base unit (``rad/s``)."""
        if self.unit == "rad/s":
            return self
        if self.unit == "rpm":
            base_value = self.value * (2.0 * np.pi / 60.0)
        else:
            base_value = self.value * ROTATIONAL_SPEED_FACTORS[self.unit]
        return FloatRotationalSpeedDto(value=base_value, unit="rad/s")

    def convert_to_unit(self, target_unit: str) -> FloatRotationalSpeedDto:
        """Return a new DTO in the requested unit."""
        if target_unit not in ROTATIONAL_SPEED_FACTORS:
            raise ValueError(f"invalid rotational speed unit: {target_unit}")
        if target_unit == self.unit:
            return self

        base = self.to_base_unit().value
        if target_unit == "rpm":
            converted = base * (60.0 / (2.0 * np.pi))
        else:
            converted = base
        return FloatRotationalSpeedDto(value=converted, unit=target_unit)


@dataclass(frozen=True)
class ArrayRotationalSpeedDto(IArrayWithUnitDto):
    """Rotational speed array DTO.

    Attributes:
        value: Rotational speed array (each element non-negative).
        unit: ``rad/s`` or ``rpm``.
    """

    value: np.ndarray
    unit: str = "rad/s"

    def __post_init__(self) -> None:
        """Validate the instance."""
        arr = np.asarray(self.value, dtype=np.float64)
        if arr.size == 0:
            raise ValueError("rotational speed array must not be empty")
        if not np.all(np.isfinite(arr)):
            raise ValueError("rotational speed array must not contain NaN/inf")
        if np.any(arr < 0):
            raise ValueError(
                "rotational speed array elements must be non-negative"
            )
        object.__setattr__(self, "value", arr)

        valid_units = list(ROTATIONAL_SPEED_FACTORS.keys())
        if self.unit not in valid_units:
            raise ValueError(f"invalid rotational speed unit: {self.unit}")

    def get_value(self) -> np.ndarray:
        """Return the rotational speed array."""
        return self.value

    def get_unit(self) -> str:
        """Return the rotational speed unit."""
        return self.unit

    def get_shape(self) -> tuple[int, ...]:
        """Return the array shape."""
        return self.value.shape

    def get_ndim(self) -> int:
        """Return the number of dimensions."""
        return self.value.ndim

    def to_base_unit(self) -> ArrayRotationalSpeedDto:
        """Convert to the base unit (``rad/s``)."""
        if self.unit == "rad/s":
            return self
        if self.unit == "rpm":
            base_value = self.value * (2.0 * np.pi / 60.0)
        else:
            base_value = self.value * ROTATIONAL_SPEED_FACTORS[self.unit]
        return ArrayRotationalSpeedDto(value=base_value, unit="rad/s")

    def convert_to_unit(self, target_unit: str) -> ArrayRotationalSpeedDto:
        """Return a new DTO in the requested unit."""
        if target_unit not in ROTATIONAL_SPEED_FACTORS:
            raise ValueError(f"invalid rotational speed unit: {target_unit}")
        if target_unit == self.unit:
            return self

        base = self.to_base_unit().value
        if target_unit == "rpm":
            converted = base * (60.0 / (2.0 * np.pi))
        else:
            converted = base
        return ArrayRotationalSpeedDto(value=converted, unit=target_unit)
