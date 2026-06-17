"""Per-unit curve DTO for ratings that may exceed 1 (100%)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from im_cable_system.engine.shared.dto.generic.interfaces.i_value_with_unit_dto import (
    IArrayWithUnitDto,
)

_VALID_UNITS: frozenset[str] = frozenset({"[-]", "%"})


@dataclass(frozen=True)
class ArrayCurvePerUnitDto(IArrayWithUnitDto):
    """Dimensionless performance curve without an upper cap (e.g. P / P_rated).

    Separate from bounded ratio types (0–1 or 0–100%). Used when nameplate
    ratios can exceed 1 / 100% (for example starting current ratio).
    """

    value: np.ndarray
    unit: str = "[-]"

    def __post_init__(self) -> None:
        """Validate the instance."""
        arr = np.asarray(self.value, dtype=np.float64)
        if arr.size == 0:
            raise ValueError("array must not be empty")
        if not np.all(np.isfinite(arr)):
            raise ValueError("array must not contain NaN/inf")
        if np.any(arr < 0.0):
            raise ValueError("finite array elements must be non-negative")
        object.__setattr__(self, "value", arr)
        if self.unit not in _VALID_UNITS:
            msg = f"invalid unit: {self.unit!r}"
            raise ValueError(msg)

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

    def to_base_unit(self) -> ArrayCurvePerUnitDto:
        """Convert to the base unit (``[-]``, dimensionless per-unit)."""
        if self.unit == "[-]":
            return self
        return ArrayCurvePerUnitDto(value=self.value / 100.0, unit="[-]")

    def convert_to_unit(self, target_unit: str) -> ArrayCurvePerUnitDto:
        """Convert to the requested unit."""
        if target_unit not in _VALID_UNITS:
            msg = f"unsupported unit: {target_unit!r}"
            raise ValueError(msg)
        if target_unit == self.unit:
            return self
        base = self.to_base_unit().value
        if target_unit == "[-]":
            return ArrayCurvePerUnitDto(value=base, unit="[-]")
        return ArrayCurvePerUnitDto(value=base * 100.0, unit="%")
