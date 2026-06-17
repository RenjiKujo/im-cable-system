from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from im_cable_system.engine.shared.dto.generic.interfaces.i_value_with_unit_dto import (
    IArrayWithUnitDto,
)

# Impedance unit factors (base unit: Ω)
IMPEDANCE_FACTORS: dict[str, float] = {
    "MΩ": 1_000_000.0,
    "kΩ": 1_000.0,
    "Ω": 1.0,
    "mΩ": 0.001,
}

# Inductance unit factors (base unit: H)
INDUCTANCE_FACTORS: dict[str, float] = {
    "MH": 1_000_000.0,
    "kH": 1_000.0,
    "H": 1.0,
    "mH": 0.001,
}

# Capacitance unit factors (base unit: F)
CAPACITANCE_FACTORS: dict[str, float] = {
    "F": 1.0,
    "mF": 1e-3,
    "uF": 1e-6,
    "nF": 1e-9,
    "pF": 1e-12,
}

# Frequency unit factors (base unit: Hz)
FREQUENCY_FACTORS: dict[str, float] = {
    "MHz": 1_000_000.0,
    "kHz": 1_000.0,
    "Hz": 1.0,
}

# Admittance unit factors (base unit: S)
ADMITTANCE_FACTORS: dict[str, float] = {
    "MS": 1_000_000.0,
    "kS": 1_000.0,
    "S": 1.0,
    "mS": 0.001,
    "uS": 0.000001,
}


@dataclass(frozen=True)
class ArrayComplexImpedanceDto(IArrayWithUnitDto):
    """DTO for a complex impedance array.

    All methods accept only ``np.ndarray`` values for impedance calculations.

    Attributes:
        value: Complex impedance array.
        unit: Unit (ohms: Ω, mΩ, kΩ, MΩ).

    Raises:
        ValueError: When any of the following holds:
            - The impedance array has size zero.
            - The impedance array contains NaN/inf.
            - The impedance unit is invalid (allowed: Ω, mΩ, kΩ, MΩ).
            - An axis name is missing or axis metadata is absent.
            - An axis name index is out of range.
    """

    value: np.ndarray
    unit: str = "Ω"

    def __post_init__(self) -> None:
        """Validate and coerce the internal array type.

        - Coerces ``value`` to ``np.ndarray[np.complex128]``.
        - Rejects NaN/inf.
        - Rejects zero-length arrays.
        - Allows only ohm-family units.
        """
        arr = np.asarray(self.value, dtype=np.complex128)
        if arr.size == 0:
            raise ValueError("impedance array must not be empty")
        if not np.all(np.isfinite(arr)):
            raise ValueError("impedance array must not contain NaN/inf")
        # Allow internal update on frozen dataclass
        object.__setattr__(self, "value", arr)

        if self.unit not in IMPEDANCE_FACTORS:
            raise ValueError(
                f"invalid impedance unit: {self.unit}. "
                f"allowed: {list(IMPEDANCE_FACTORS.keys())}"
            )

    def get_value(self) -> np.ndarray:
        """Return the impedance array."""
        return self.value

    def get_unit(self) -> str:
        """Return the unit."""
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

    def to_base_unit(self) -> ArrayComplexImpedanceDto:
        """Convert to the base-unit (Ω) DTO.

        Returns:
            DTO with the complex impedance array normalized to Ω.

        Notes:
            - Returned ``unit`` is always ``"Ω"``.
            - Shape matches the input.
        """
        factors = IMPEDANCE_FACTORS
        if self.unit == "Ω":
            return self
        base_value = self.value * factors[self.unit]
        return ArrayComplexImpedanceDto(value=base_value, unit="Ω")

    def convert_to_unit(self, target_unit: str) -> ArrayComplexImpedanceDto:
        """Return a new DTO converted to the specified unit.

        Args:
            target_unit: Target unit (Ω, mΩ, kΩ, MΩ).

        Returns:
            Converted DTO.

        Notes:
            - Returned ``unit`` is ``target_unit``.
            - Shape matches the input.
        """
        factors = IMPEDANCE_FACTORS
        if target_unit not in factors:
            raise ValueError(f"invalid impedance unit: {target_unit}")
        if target_unit == self.unit:
            return self

        base = self.to_base_unit().value
        reverse = {unit: (1.0 / factor) for unit, factor in factors.items()}
        converted = base * reverse[target_unit]
        return ArrayComplexImpedanceDto(value=converted, unit=target_unit)

    def get_magnitude(self) -> np.ndarray:
        """Return impedance magnitude."""
        return np.abs(self.value)

    def get_phase(self) -> np.ndarray:
        """Return impedance phase in radians."""
        return np.angle(self.value)

    def get_real_part(self) -> np.ndarray:
        """Return the real part of the impedance."""
        return np.real(self.value)

    def get_imaginary_part(self) -> np.ndarray:
        """Return the imaginary part of the impedance."""
        return np.imag(self.value)
