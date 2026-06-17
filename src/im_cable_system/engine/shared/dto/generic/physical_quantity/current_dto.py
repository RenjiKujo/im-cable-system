"""Current DTO module.

Defines DTO classes for current values (float and array).

DTOs are limited to value-object responsibilities (data holding and unit
conversion). Calculation logic (Ohm's law, Kirchhoff's laws, and so on) lives
in the domain layer.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from im_cable_system.engine.shared.dto.generic.interfaces.i_value_with_unit_dto import (
    IArrayWithUnitDto,
    IFloatWithUnitDto,
)

_CURRENT_UNITS = ["mA", "A", "kA"]

# Current unit factors (base unit: A)
CURRENT_FACTORS: dict[str, float] = {
    "kA": 1_000.0,
    "A": 1.0,
    "mA": 0.001,
}


@dataclass(frozen=True)
class FloatCurrentDto(IFloatWithUnitDto):
    """DTO for a scalar current value.

    Attributes:
        value: Current value.
        unit: Current unit (A, kA, mA).
    """

    value: float
    unit: str

    def __post_init__(self) -> None:
        """Validate the instance."""
        if not isinstance(self.value, (int, float)):
            raise ValueError("current value must be numeric")
        if not np.isfinite(self.value):
            raise ValueError("current value must not contain NaN/inf")
        if self.value < 0:
            raise ValueError("current value must be non-negative")

        if self.unit not in _CURRENT_UNITS:
            raise ValueError(f"invalid current unit: {self.unit}")

    def get_value(self) -> float:
        """Return the current value."""
        return self.value

    def get_unit(self) -> str:
        """Return the current unit."""
        return self.unit

    def to_base_unit(self) -> FloatCurrentDto:
        """Convert to the base-unit (A) DTO."""
        if self.unit == "A":
            return self
        base_value = self.value * CURRENT_FACTORS[self.unit]
        return FloatCurrentDto(base_value, "A")

    def convert_to_unit(self, target_unit: str) -> FloatCurrentDto:
        """Convert to the specified unit."""
        if target_unit not in _CURRENT_UNITS:
            raise ValueError(f"invalid current unit: {target_unit}")
        if target_unit == self.unit:
            return self

        base_value = self.to_base_unit().value
        reverse = {
            unit: (1.0 / factor) for unit, factor in CURRENT_FACTORS.items()
        }
        converted_value = base_value * reverse[target_unit]
        return FloatCurrentDto(converted_value, target_unit)


@dataclass(frozen=True)
class ArrayComplexCurrentDto(IArrayWithUnitDto):
    """DTO for a complex current array.

    All methods accept only ``np.ndarray`` values for current calculations.

    Attributes:
        value: Complex current array.
        unit: Current unit (mA, A, kA).
    """

    value: np.ndarray
    unit: str

    def __post_init__(self) -> None:
        """Validate and coerce the internal array type.

        - Coerces ``value`` to ``np.ndarray[np.complex128]``.
        - Rejects NaN/inf.
        - Rejects zero-length arrays.
        - Ensures magnitude (absolute value) is non-negative.
        """
        arr = np.asarray(self.value, dtype=np.complex128)
        if arr.size == 0:
            raise ValueError("current array must not be empty")
        if not np.all(np.isfinite(np.real(arr))) or not np.all(
            np.isfinite(np.imag(arr))
        ):
            raise ValueError("current array must not contain NaN/inf")
        if np.any(np.abs(arr) < 0):
            raise ValueError(
                "current array element magnitudes must be non-negative"
            )
        # Allow internal update on frozen dataclass
        object.__setattr__(self, "value", arr)

        if self.unit not in _CURRENT_UNITS:
            raise ValueError(f"invalid current unit: {self.unit}")

    def get_value(self) -> np.ndarray:
        """Return the current array."""
        return self.value

    def get_unit(self) -> str:
        """Return the current unit."""
        return self.unit

    def get_shape(self) -> tuple[int, ...]:
        """Return the array shape.

        Returns:
            Tuple of sizes for each dimension.
        """
        return self.value.shape

    def get_ndim(self) -> int:
        """Return the number of array dimensions.

        Returns:
            Number of dimensions.
        """
        return self.value.ndim

    def to_base_unit(self) -> ArrayComplexCurrentDto:
        """Convert to the base-unit (A) DTO."""
        if self.unit == "A":
            return self
        base_value = self.value * CURRENT_FACTORS[self.unit]
        return ArrayComplexCurrentDto(value=base_value, unit="A")

    def convert_to_unit(self, target_unit: str) -> ArrayComplexCurrentDto:
        """Return a new DTO converted to the specified unit."""
        if target_unit not in _CURRENT_UNITS:
            raise ValueError(f"invalid current unit: {target_unit}")
        if target_unit == self.unit:
            return self

        base_value = self.to_base_unit().value
        reverse = {
            unit: (1.0 / factor) for unit, factor in CURRENT_FACTORS.items()
        }
        converted_value = base_value * reverse[target_unit]
        return ArrayComplexCurrentDto(value=converted_value, unit=target_unit)

    def get_magnitude(self) -> np.ndarray:
        """Return current magnitude.

        Returns:
            Array of current magnitudes (absolute values).
        """
        return np.abs(self.value)

    def get_phase(self) -> np.ndarray:
        """Return current phase in radians.

        Returns:
            Array of current phases in radians.
        """
        return np.angle(self.value)

    def get_real_part(self) -> np.ndarray:
        """Return the real part of the current.

        Returns:
            Array of real parts.
        """
        return np.real(self.value)

    def get_imaginary_part(self) -> np.ndarray:
        """Return the imaginary part of the current.

        Returns:
            Array of imaginary parts.
        """
        return np.imag(self.value)


@dataclass(frozen=True)
class ArrayCurrentMagnitudeDto(IArrayWithUnitDto):
    """DTO for a current magnitude (absolute value) array.

    Holds the absolute-value array of complex current. Units are A family
    (mA, A, kA).

    Attributes:
        value: Current magnitude array (real).
        unit: Current unit (mA, A, kA).
    """

    value: np.ndarray
    unit: str

    def __post_init__(self) -> None:
        """Validate and coerce the internal array type."""
        arr = np.asarray(self.value, dtype=np.float64)
        if arr.size == 0:
            raise ValueError("current magnitude array must not be empty")
        if not np.all(np.isfinite(arr)):
            raise ValueError("current magnitude array must not contain NaN/inf")
        if np.any(arr < 0.0):
            raise ValueError(
                "current magnitude finite array elements must be non-negative"
            )
        object.__setattr__(self, "value", arr)
        if self.unit not in _CURRENT_UNITS:
            raise ValueError(f"invalid current unit: {self.unit}")

    def get_value(self) -> np.ndarray:
        """Return the current magnitude array."""
        return self.value

    def get_unit(self) -> str:
        """Return the current unit."""
        return self.unit

    def get_shape(self) -> tuple[int, ...]:
        """Return the array shape."""
        return self.value.shape

    def get_ndim(self) -> int:
        """Return the number of array dimensions."""
        return self.value.ndim

    def to_base_unit(self) -> ArrayCurrentMagnitudeDto:
        """Convert to the base-unit (A) DTO."""
        if self.unit == "A":
            return self
        base_value = self.value * CURRENT_FACTORS[self.unit]
        return ArrayCurrentMagnitudeDto(value=base_value, unit="A")

    def convert_to_unit(self, target_unit: str) -> ArrayCurrentMagnitudeDto:
        """Return a new DTO converted to the specified unit."""
        if target_unit not in _CURRENT_UNITS:
            raise ValueError(f"invalid current unit: {target_unit}")
        if target_unit == self.unit:
            return self
        base_value = self.to_base_unit().value
        reverse = {
            unit: (1.0 / factor) for unit, factor in CURRENT_FACTORS.items()
        }
        converted_value = base_value * reverse[target_unit]
        return ArrayCurrentMagnitudeDto(value=converted_value, unit=target_unit)
