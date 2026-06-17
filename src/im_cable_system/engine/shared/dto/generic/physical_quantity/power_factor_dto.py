"""Power factor DTO module.

Defines DTO classes for power factor values (float and array).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from im_cable_system.engine.shared.dto.generic.interfaces.i_value_with_unit_dto import (
    IArrayWithUnitDto,
    IFloatWithUnitDto,
)

# Power factor unit factors (base unit: "-" dimensionless)
POWER_FACTOR_FACTORS: dict[str, float] = {
    "%": 1.0,
    "-": 1.0,
}


@dataclass(frozen=True)
class FloatPowerFactorDto(IFloatWithUnitDto):
    """DTO for a scalar power factor value.

    Attributes:
        value: Power factor (-1.0 to 1.0 or -100 to 100%). Negative values
            indicate leading/generator-side power factor, and so on.
        unit: Power factor unit ("-" dimensionless, or "%").
    """

    value: float
    unit: str = "-"

    def __post_init__(self) -> None:
        """Validate the instance."""
        if not isinstance(self.value, (int, float)):
            raise ValueError("power factor value must be numeric")
        if not np.isfinite(self.value):
            raise ValueError("power factor value must not contain NaN/inf")

        valid_units = list(POWER_FACTOR_FACTORS.keys())
        if self.unit not in valid_units:
            raise ValueError(f"invalid power factor unit: {self.unit}")

        if self.unit == "-":
            if self.value < -1.0 or self.value > 1.0:
                raise ValueError(
                    "power factor value must be between -1.0 and 1.0"
                )
        elif self.value < -100.0 or self.value > 100.0:
            raise ValueError("power factor value must be between -100 and 100")

    def get_value(self) -> float:
        """Return the power factor value."""
        return self.value

    def get_unit(self) -> str:
        """Return the power factor unit."""
        return self.unit

    def to_base_unit(self) -> FloatPowerFactorDto:
        """Convert to the base-unit ("-" dimensionless) DTO."""
        if self.unit == "-":
            return self
        base_value = self.value if self.unit == "-" else (self.value / 100.0)
        return FloatPowerFactorDto(value=base_value, unit="-")

    def convert_to_unit(self, target_unit: str) -> FloatPowerFactorDto:
        """Return a new DTO converted to the specified unit."""
        if target_unit not in ("-", "%"):
            raise ValueError(f"invalid power factor unit: {target_unit}")
        if target_unit == self.unit:
            return self

        base = self.to_base_unit().value
        if target_unit == "-":
            return FloatPowerFactorDto(value=base, unit="-")
        return FloatPowerFactorDto(value=base * 100.0, unit="%")

    def calculate_phase_angle(self) -> float:
        """Compute phase angle from power factor in radians.

        Computes phase angle θ from power factor cos(θ).
        Formula: θ = arccos(pf).

        Returns:
            Phase angle in radians.

        Raises:
            ValueError: If the power factor is outside [-1, 1] in base units.

        Notes:
            - When power factor is near 1 (cos(θ) ≈ 1), phase angle is near 0.
            - When power factor is near 0 (cos(θ) ≈ 0), phase angle is near π/2.
            - When power factor is near -1 (cos(θ) ≈ -1), phase angle is near π.
        """
        base_value = self.to_base_unit().value

        # Range check for arccos domain [-1, 1]
        if base_value < -1.0 or base_value > 1.0:
            raise ValueError(
                f"power factor value must be between -1.0 and 1.0: {base_value}"
            )

        phase_angle = np.arccos(base_value)
        return float(phase_angle)


@dataclass(frozen=True)
class ArrayPowerFactorDto(IArrayWithUnitDto):
    """DTO for a power factor array.

    Attributes:
        value: Power factor array (-1.0 to 1.0 or -100 to 100%). Negative
            values indicate leading/generator-side power factor, and so on.
        unit: Power factor unit ("-" dimensionless, or "%").
    """

    value: np.ndarray
    unit: str = "-"

    def __post_init__(self) -> None:
        """Validate the instance."""
        arr = np.asarray(self.value, dtype=np.float64)
        if arr.size == 0:
            raise ValueError("power factor array must not be empty")
        if not np.all(np.isfinite(arr)):
            raise ValueError("power factor array must not contain NaN/inf")
        object.__setattr__(self, "value", arr)

        valid_units = list(POWER_FACTOR_FACTORS.keys())
        if self.unit not in valid_units:
            raise ValueError(f"invalid power factor unit: {self.unit}")

        if self.unit == "-":
            if np.any((arr < -1.0) | (arr > 1.0)):
                raise ValueError(
                    "all power factor elements must be between -1.0 and 1.0"
                )
        elif np.any((arr < -100.0) | (arr > 100.0)):
            raise ValueError(
                "all power factor elements must be between -100 and 100"
            )

    def get_value(self) -> np.ndarray:
        """Return the power factor array."""
        return self.value

    def get_unit(self) -> str:
        """Return the power factor unit."""
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

    def to_base_unit(self) -> ArrayPowerFactorDto:
        """Convert to the base-unit ("-" dimensionless) DTO."""
        if self.unit == "-":
            return self
        base_value = self.value if self.unit == "-" else (self.value / 100.0)
        return ArrayPowerFactorDto(value=base_value, unit="-")

    def convert_to_unit(self, target_unit: str) -> ArrayPowerFactorDto:
        """Return a new DTO converted to the specified unit."""
        if target_unit not in ("-", "%"):
            raise ValueError(f"invalid power factor unit: {target_unit}")
        if target_unit == self.unit:
            return self

        base = self.to_base_unit().value
        if target_unit == "-":
            return ArrayPowerFactorDto(value=base, unit="-")
        return ArrayPowerFactorDto(value=base * 100.0, unit="%")

    def calculate_phase_angle(self) -> np.ndarray:
        """Compute phase angle from power factor in radians.

        Computes phase angle θ from power factor cos(θ).
        Formula: θ = arccos(pf).

        Returns:
            Array of phase angles in radians.

        Raises:
            ValueError: If any power factor is outside [-1, 1] in base units.

        Notes:
            - When power factor is near 1 (cos(θ) ≈ 1), phase angle is near 0.
            - When power factor is near 0 (cos(θ) ≈ 0), phase angle is near π/2.
            - When power factor is near -1 (cos(θ) ≈ -1), phase angle is near π.
        """
        base_value = self.to_base_unit().value

        # Range check for arccos domain [-1, 1]
        if np.any(base_value < -1.0) or np.any(base_value > 1.0):
            raise ValueError(
                "power factor value must be between -1.0 and 1.0. "
                f"out-of-range values: min={np.min(base_value)}, "
                f"max={np.max(base_value)}"
            )

        return np.arccos(base_value)
