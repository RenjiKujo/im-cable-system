import math
from dataclasses import dataclass

from im_cable_system.engine.shared.dto.generic.interfaces.i_value_with_unit_dto import (
    IFloatWithUnitDto,
)

# SI length conversion factors (base unit: m)
SI_UNITS_TO_METER: dict[str, float] = {
    "km": 1000.0,
    "m": 1.0,
    "cm": 0.01,
    "mm": 0.001,
}

# Field length conversion factors (base unit: m)
# 1 ft = 0.3048 m
# 1 in = 0.0254 m = 1/12 ft
# 1 yd = 0.9144 m = 3 ft
# 1 mi = 1609.344 m = 5280 ft
FIELD_UNITS_TO_METER: dict[str, float] = {
    "mi": 1609.344,
    "yd": 0.9144,
    "ft": 0.3048,
    "in": 0.0254,
}


@dataclass(frozen=True)
class FloatLengthDto(IFloatWithUnitDto):
    """DTO for a scalar length or distance value.

    Supports both SI and field unit systems.

    Attributes:
        value: Length or distance value.
        unit: Length unit.
            SI: m, km, cm, mm.
            Field: ft, in, yd, mi.
    """

    value: float
    unit: str

    def __post_init__(self) -> None:
        """Validate the instance."""
        if not math.isfinite(self.value):
            raise ValueError("length value must be finite")
        if self.value < 0:
            raise ValueError("length value must be non-negative")

        all_valid_units = list(SI_UNITS_TO_METER.keys()) + list(
            FIELD_UNITS_TO_METER.keys()
        )
        if self.unit not in all_valid_units:
            raise ValueError(
                f"invalid length unit: {self.unit}. "
                f"valid units: {all_valid_units}"
            )

    def get_value(self) -> float:
        """Return the length value."""
        return self.value

    def get_unit(self) -> str:
        """Return the length unit."""
        return self.unit

    def _get_all_conversion_factors(self) -> dict[str, float]:
        """Return conversion factors for all supported unit systems."""
        return {
            **SI_UNITS_TO_METER,
            **FIELD_UNITS_TO_METER,
        }

    def to_base_unit(self) -> "FloatLengthDto":
        """Convert to the base-unit (m) DTO."""
        if self.unit == "m":
            return self
        conversion_factors = self._get_all_conversion_factors()
        base_value = self.value * conversion_factors.get(self.unit, 1.0)
        return FloatLengthDto(base_value, "m")

    def convert_to_unit(self, target_unit: str) -> "FloatLengthDto":
        """Convert to the specified unit."""
        all_valid_units = list(SI_UNITS_TO_METER.keys()) + list(
            FIELD_UNITS_TO_METER.keys()
        )
        if target_unit not in all_valid_units:
            raise ValueError(
                f"invalid length unit: {target_unit}. "
                f"valid units: {all_valid_units}"
            )
        if target_unit == self.unit:
            return self

        base_value = self.to_base_unit().value
        conversion_factors = self._get_all_conversion_factors()
        reverse_factors = {
            unit: 1.0 / factor for unit, factor in conversion_factors.items()
        }
        converted_value = base_value * reverse_factors.get(target_unit, 1.0)
        return FloatLengthDto(converted_value, target_unit)
