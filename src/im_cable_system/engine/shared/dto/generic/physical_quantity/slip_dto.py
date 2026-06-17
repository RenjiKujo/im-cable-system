"""Unit-aware DTOs for slip (dimensionless or percent)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from im_cable_system.engine.shared.dto.generic.interfaces.i_value_with_unit_dto import (
    IArrayWithUnitDto,
)


@dataclass(frozen=True)
class ArraySlipDto(IArrayWithUnitDto):
    """Slip array DTO.

    Attributes:
        value: Slip array. For unit ``"-"``, each element in 0.0–1.0; for
            ``"%"``, each element in 0–100.
        unit: ``"-"`` or ``"%"``.

    Notes:
        This DTO only validates the input state (range / NaN / inf / unit).
        Near-zero handling for slip is the responsibility of the downstream
        model-conversion (secondary immittance) calculators, which detect and
        clamp near-zero slip and record the corresponding numerical-stability
        events. Slip may legitimately be exactly 0; clamping is not done here.
    """

    value: np.ndarray
    unit: str

    def __post_init__(self) -> None:
        """Validate the instance."""
        arr = np.asarray(self.value, dtype=np.float64)
        if arr.size == 0:
            raise ValueError("slip array must not be empty")
        if not np.all(np.isfinite(arr)):
            raise ValueError("slip array must not contain NaN/inf")
        object.__setattr__(self, "value", arr)

        if self.unit not in ("-", "%"):
            raise ValueError(f"slip unit must be '-' or '%': {self.unit}")
        if self.unit == "-":
            if np.any(arr < 0.0) or np.any(arr > 1.0):
                raise ValueError(
                    "all slip elements must be between 0.0 and 1.0"
                )
        elif np.any(arr < 0.0) or np.any(arr > 100.0):
            raise ValueError("all slip elements must be between 0 and 100")

    def get_value(self) -> np.ndarray:
        """Return the array values."""
        return self.value

    def get_unit(self) -> str:
        """Return the unit string."""
        return self.unit

    def get_shape(self) -> tuple[int, ...]:
        """Return the array shape."""
        return self.value.shape

    def get_ndim(self) -> int:
        """Return the number of dimensions."""
        return self.value.ndim

    def to_base_unit(self) -> ArraySlipDto:
        """Convert to the base unit (``"-"``)."""
        if self.unit == "-":
            return self
        base_value = self.value if self.unit == "-" else (self.value / 100.0)
        return ArraySlipDto(value=base_value, unit="-")

    def convert_to_unit(self, target_unit: str) -> ArraySlipDto:
        """Return a new DTO in the requested unit."""
        if target_unit not in ("-", "%"):
            raise ValueError(f"invalid slip unit: {target_unit}")
        if target_unit == self.unit:
            return self
        base = self.to_base_unit().value
        if target_unit == "-":
            return ArraySlipDto(value=base, unit="-")
        return ArraySlipDto(value=base * 100.0, unit="%")
