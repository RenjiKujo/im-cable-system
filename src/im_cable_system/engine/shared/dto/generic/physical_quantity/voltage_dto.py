"""Voltage DTO module.

Defines DTO classes for voltage values (float and array).

DTOs are limited to value-object responsibilities (data holding and unit
conversion). Calculation logic (Ohm's law, Kirchhoff's laws, and so on) lives
in the domain layer.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast

import numpy as np

from im_cable_system.engine.shared.dto.generic.interfaces.i_value_with_unit_dto import (
    IArrayWithUnitDto,
    IFloatWithUnitDto,
)

_VOLTAGE_UNITS = ["mV", "V", "kV", "MV"]

# Voltage unit factors (base unit: V)
VOLTAGE_FACTORS: dict[str, float] = {
    "MV": 1_000_000.0,
    "kV": 1_000.0,
    "V": 1.0,
    "mV": 0.001,
}


@dataclass(frozen=True)
class FloatVoltageDto(IFloatWithUnitDto):
    """DTO for a scalar voltage value.

    Attributes:
        value: Voltage value.
        unit: Voltage unit (mV, V, kV, MV).
    """

    value: float
    unit: str

    def __post_init__(self) -> None:
        """Validate the instance."""
        if not isinstance(self.value, (int, float)):
            raise ValueError("voltage value must be numeric")
        if not np.isfinite(self.value):
            raise ValueError("voltage value must not contain NaN/inf")
        if self.value < 0:
            raise ValueError("voltage value must be non-negative")

        if self.unit not in _VOLTAGE_UNITS:
            raise ValueError(f"invalid voltage unit: {self.unit}")

    def get_value(self) -> float:
        """Return the voltage value."""
        return self.value

    def get_unit(self) -> str:
        """Return the voltage unit."""
        return self.unit

    def to_base_unit(self) -> FloatVoltageDto:
        """Convert to the base-unit (V) DTO."""
        if self.unit == "V":
            return self
        base_value = self.value * VOLTAGE_FACTORS[self.unit]
        return FloatVoltageDto(base_value, "V")

    def convert_to_unit(self, target_unit: str) -> FloatVoltageDto:
        """Convert to the specified unit."""
        if target_unit not in _VOLTAGE_UNITS:
            raise ValueError(f"invalid voltage unit: {target_unit}")
        if target_unit == self.unit:
            return self

        base_value = self.to_base_unit().value
        reverse = {
            unit: (1.0 / factor) for unit, factor in VOLTAGE_FACTORS.items()
        }
        converted_value = base_value * reverse[target_unit]
        return FloatVoltageDto(converted_value, target_unit)


@dataclass(frozen=True)
class ArrayComplexVoltageDto(IArrayWithUnitDto):
    """DTO for a complex voltage array.

    Attributes:
        value: Complex voltage array.
        unit: Voltage unit (mV, V, kV, MV).
    """

    value: np.ndarray
    unit: str

    def __post_init__(self) -> None:
        """Validate and coerce the internal array type."""
        if not isinstance(self.value, np.ndarray):
            raise ValueError("voltage array must be a NumPy array")

        arr = np.asarray(self.value, dtype=np.complex128)
        if arr.size == 0:
            raise ValueError("voltage array must not be empty")
        if not np.all(np.isfinite(arr)):
            raise ValueError("voltage array must not contain NaN/inf")

        object.__setattr__(self, "value", arr)

        if self.unit not in _VOLTAGE_UNITS:
            raise ValueError(f"invalid voltage unit: {self.unit}")

    def get_value(self) -> np.ndarray:
        """Return the voltage array."""
        return self.value

    def get_unit(self) -> str:
        """Return the voltage unit."""
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

    def get_magnitude(self) -> np.ndarray:
        """Return voltage magnitude."""
        return cast(np.ndarray, np.abs(self.value))

    def get_phase(self) -> np.ndarray:
        """Return voltage phase in radians."""
        return cast(np.ndarray, np.angle(self.value))

    def get_real_part(self) -> np.ndarray:
        """Return the real part of the voltage."""
        return cast(np.ndarray, np.real(self.value))

    def get_imaginary_part(self) -> np.ndarray:
        """Return the imaginary part of the voltage."""
        return cast(np.ndarray, np.imag(self.value))

    def to_base_unit(self) -> ArrayComplexVoltageDto:
        """Convert to the base-unit (V) DTO."""
        if self.unit == "V":
            return self
        base_value = self.value * VOLTAGE_FACTORS[self.unit]
        return ArrayComplexVoltageDto(value=base_value, unit="V")

    def convert_to_unit(self, target_unit: str) -> ArrayComplexVoltageDto:
        """Return a new DTO converted to the specified unit."""
        if target_unit not in _VOLTAGE_UNITS:
            raise ValueError(f"invalid voltage unit: {target_unit}")
        if target_unit == self.unit:
            return self

        base_value = self.to_base_unit().value
        reverse = {
            unit: (1.0 / factor) for unit, factor in VOLTAGE_FACTORS.items()
        }
        converted_value = base_value * reverse[target_unit]
        return ArrayComplexVoltageDto(value=converted_value, unit=target_unit)
