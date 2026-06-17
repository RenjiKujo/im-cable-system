from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from im_cable_system.engine.shared.dto.generic.interfaces.i_value_with_unit_dto import (
    IArrayWithUnitDto,
)

# Admittance unit factors (base unit: S)
ADMITTANCE_FACTORS: dict[str, float] = {
    "MS": 1_000_000.0,
    "kS": 1_000.0,
    "S": 1.0,
    "mS": 0.001,
    "uS": 0.000001,
}

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


@dataclass(frozen=True)
class ArrayComplexAdmittanceDto(IArrayWithUnitDto):
    """DTO for a complex admittance array.

    All methods accept only ``np.ndarray`` values for admittance calculations.

    Attributes:
        value: Complex admittance array.
        unit: Unit (siemens: S, mS, kS, MS, uS).

    Raises:
        ValueError: When any of the following holds:
            - The admittance array has size zero.
            - The admittance array contains NaN/inf.
            - The admittance unit is invalid (allowed: S, mS, kS, MS, uS).
            - An axis name is missing or axis metadata is absent.
            - An axis name index is out of range.

    """

    value: np.ndarray
    unit: str = "S"

    def __post_init__(self) -> None:
        """Validate and coerce the internal array type.

        - Coerces ``value`` to ``np.ndarray[np.complex128]``.
        - Rejects NaN/inf.
        - Rejects zero-length arrays.
        - Allows only siemens-family units.
        """
        arr = np.asarray(self.value, dtype=np.complex128)
        if arr.size == 0:
            raise ValueError("admittance array must not be empty")
        if not np.all(np.isfinite(arr)):
            raise ValueError("admittance array must not contain NaN/inf")
        # Allow internal update on frozen dataclass
        object.__setattr__(self, "value", arr)

        if self.unit not in ADMITTANCE_FACTORS:
            raise ValueError(
                f"invalid admittance unit: {self.unit}. "
                f"allowed: {list(ADMITTANCE_FACTORS.keys())}"
            )

    def get_value(self) -> np.ndarray:
        """Return the admittance array."""
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

    def to_base_unit(self) -> ArrayComplexAdmittanceDto:
        """Convert to the base-unit (S) DTO.

        Returns:
            DTO with the complex admittance array normalized to S.

        Notes:
            - Returned ``unit`` is always ``"S"``.
            - Shape matches the input.
        """
        factors = ADMITTANCE_FACTORS
        if self.unit == "S":
            return self
        base_value = self.value * factors[self.unit]
        return ArrayComplexAdmittanceDto(value=base_value, unit="S")

    def convert_to_unit(self, target_unit: str) -> ArrayComplexAdmittanceDto:
        """Return a new DTO converted to the specified unit.

        Args:
            target_unit: Target unit (S, mS, kS, MS, uS).

        Returns:
            Converted DTO.

        Notes:
            - Returned ``unit`` is ``target_unit``.
            - Shape matches the input.
        """
        factors = ADMITTANCE_FACTORS
        if target_unit not in factors:
            raise ValueError(f"invalid admittance unit: {target_unit}")
        if target_unit == self.unit:
            return self

        base = self.to_base_unit().value
        reverse = {unit: (1.0 / factor) for unit, factor in factors.items()}
        converted = base * reverse[target_unit]
        return ArrayComplexAdmittanceDto(value=converted, unit=target_unit)

    def get_magnitude(self) -> np.ndarray:
        """Return admittance magnitude."""
        return np.abs(self.value)

    def get_phase(self) -> np.ndarray:
        """Return admittance phase in radians."""
        return np.angle(self.value)

    def get_real_part(self) -> np.ndarray:
        """Return the real part of the admittance."""
        return np.real(self.value)

    def get_imaginary_part(self) -> np.ndarray:
        """Return the imaginary part of the admittance."""
        return np.imag(self.value)
