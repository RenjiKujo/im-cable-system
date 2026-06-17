from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from im_cable_system.engine.shared.dto.generic.interfaces.i_value_with_unit_dto import (
    IArrayWithUnitDto,
    IFloatWithUnitDto,
)

# Frequency unit factors (base unit: Hz)
FREQUENCY_FACTORS: dict[str, float] = {
    "MHz": 1_000_000.0,
    "kHz": 1_000.0,
    "Hz": 1.0,
}


@dataclass(frozen=True)
class FloatFrequencyDto(IFloatWithUnitDto):
    """DTO for a scalar frequency value.

    Attributes:
        value: Frequency value.
        unit: Frequency unit (Hz, kHz, MHz).
    """

    value: float
    unit: str = "Hz"

    def __post_init__(self) -> None:
        """Validate the instance."""
        if not isinstance(self.value, (int, float)):
            raise ValueError("frequency value must be numeric")
        if not np.isfinite(self.value):
            raise ValueError("frequency value must not contain NaN/inf")
        if self.value <= 0:
            raise ValueError("frequency value must be greater than zero")

        if self.unit not in FREQUENCY_FACTORS:
            raise ValueError(f"invalid frequency unit: {self.unit}")

    def get_value(self) -> float:
        """Return the frequency value."""
        return self.value

    def get_unit(self) -> str:
        """Return the frequency unit."""
        return self.unit

    def to_base_unit(self) -> FloatFrequencyDto:
        """Convert to the base-unit (Hz) DTO."""
        if self.unit == "Hz":
            return self
        base_value = self.value * FREQUENCY_FACTORS[self.unit]
        return FloatFrequencyDto(base_value, "Hz")

    def convert_to_unit(self, target_unit: str) -> FloatFrequencyDto:
        """Convert to the specified unit."""
        if target_unit not in FREQUENCY_FACTORS:
            raise ValueError(f"invalid frequency unit: {target_unit}")
        if target_unit == self.unit:
            return self

        base_value = self.to_base_unit().value
        reverse = {
            unit: (1.0 / factor) for unit, factor in FREQUENCY_FACTORS.items()
        }
        converted_value = base_value * reverse[target_unit]
        return FloatFrequencyDto(converted_value, target_unit)


@dataclass(frozen=True)
class ArrayFrequencyDto(IArrayWithUnitDto):
    """DTO for a frequency array.

    Attributes:
        value: Frequency array.
        unit: Frequency unit (Hz, kHz, MHz).
    """

    value: np.ndarray
    unit: str = "Hz"

    def __post_init__(self) -> None:
        """Validate the instance."""
        arr = np.asarray(self.value, dtype=np.float64)
        if arr.size == 0:
            raise ValueError("frequency array must not be empty")
        if not np.all(np.isfinite(arr)):
            raise ValueError("frequency array must not contain NaN/inf")
        if np.any(arr <= 0):
            raise ValueError(
                "all frequency array elements must be greater than zero"
            )
        object.__setattr__(self, "value", arr)

        if self.unit not in FREQUENCY_FACTORS:
            raise ValueError(f"invalid frequency unit: {self.unit}")

    def get_value(self) -> np.ndarray:
        """Return the frequency array."""
        return self.value

    def get_unit(self) -> str:
        """Return the frequency unit."""
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

    def to_base_unit(self) -> ArrayFrequencyDto:
        """Convert to the base-unit (Hz) DTO."""
        if self.unit == "Hz":
            return self
        base_value = self.value * FREQUENCY_FACTORS[self.unit]
        return ArrayFrequencyDto(value=base_value, unit="Hz")

    def convert_to_unit(self, target_unit: str) -> ArrayFrequencyDto:
        """Return a new DTO converted to the specified unit."""
        if target_unit not in FREQUENCY_FACTORS:
            raise ValueError(f"invalid frequency unit: {target_unit}")
        if target_unit == self.unit:
            return self

        base = self.to_base_unit().value
        reverse = {
            unit: (1.0 / factor) for unit, factor in FREQUENCY_FACTORS.items()
        }
        converted = base * reverse[target_unit]
        return ArrayFrequencyDto(value=converted, unit=target_unit)
