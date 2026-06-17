"""Single-value RLC DTO module.

Defines DTO classes for scalar resistance, conductance, inductance, and
capacitance values.

Typical uses:
    - Motor circuit parameters (primary, excitation, and secondary R/L/C).
    - Building impedance and admittance.
    - Other scalar RLC parameters.

DTOs defined here:
    - FloatResistanceDto: scalar resistance (e.g. Ω, kΩ, MΩ).
    - FloatConductanceDto: scalar conductance (e.g. S, mS, kS, MS, uS).
    - FloatInductanceDto: scalar inductance (e.g. H, mH, kH).
    - FloatCapacitanceDto: scalar capacitance (e.g. F, mF, uF, nF, pF).

Note:
    RLC parameters are often fixed scalar circuit values, so array DTOs are
    not provided. When arrays are needed, convert to impedance/admittance
    first and treat them as arrays there.

Note:
    Per-length (line density) DTOs are defined in ``rlc_density_dto.py``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from im_cable_system.engine.shared.dto.generic.interfaces.i_value_with_unit_dto import (
    IFloatWithUnitDto,
)

# Resistance unit factors (base unit: Ω)
RESISTANCE_FACTORS: dict[str, float] = {
    "MΩ": 1_000_000.0,
    "kΩ": 1_000.0,
    "Ω": 1.0,
    "mΩ": 0.001,
}

# Conductance unit factors (base unit: S)
CONDUCTANCE_FACTORS: dict[str, float] = {
    "MS": 1_000_000.0,
    "kS": 1_000.0,
    "S": 1.0,
    "mS": 0.001,
    "uS": 0.000001,
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


@dataclass(frozen=True)
class FloatResistanceDto(IFloatWithUnitDto):
    """DTO for a scalar resistance value.

    Attributes:
        value: Resistance value.
        unit: Resistance unit (Ω, mΩ, kΩ, MΩ).
    """

    value: float
    unit: str = "Ω"

    def __post_init__(self) -> None:
        """Validate the instance.

        Note:
            ``inf`` is allowed: an open circuit / perfect insulation maps to
            an infinite resistance, and downstream immittance conversion
            clamps it via eps/max_mag. ``NaN`` is always rejected.
        """
        if math.isnan(self.value):
            raise ValueError("resistance value must not be NaN")
        if self.value < 0:
            raise ValueError("resistance value must be non-negative")

        if self.unit not in RESISTANCE_FACTORS:
            raise ValueError(
                f"invalid resistance unit: {self.unit}. "
                f"allowed: {list(RESISTANCE_FACTORS.keys())}"
            )

    def get_value(self) -> float:
        """Return the resistance value."""
        return self.value

    def get_unit(self) -> str:
        """Return the resistance unit."""
        return self.unit

    def to_base_unit(self) -> FloatResistanceDto:
        """Convert to the base-unit (Ω) DTO."""
        if self.unit == "Ω":
            return self
        base_value = self.value * RESISTANCE_FACTORS[self.unit]
        return FloatResistanceDto(value=base_value, unit="Ω")

    def convert_to_unit(self, target_unit: str) -> FloatResistanceDto:
        """Convert to the specified unit."""
        if target_unit not in RESISTANCE_FACTORS:
            raise ValueError(
                f"invalid resistance unit: {target_unit}. "
                f"allowed: {list(RESISTANCE_FACTORS.keys())}"
            )
        if target_unit == self.unit:
            return self

        base = self.to_base_unit()
        factor = RESISTANCE_FACTORS[target_unit]
        converted_value = base.value / factor
        return FloatResistanceDto(value=converted_value, unit=target_unit)


@dataclass(frozen=True)
class FloatConductanceDto(IFloatWithUnitDto):
    """DTO for a scalar conductance value.

    Attributes:
        value: Conductance value.
        unit: Conductance unit (S, mS, kS, MS, uS).
    """

    value: float
    unit: str = "S"

    def __post_init__(self) -> None:
        """Validate the instance.

        Note:
            ``inf`` is allowed: a perfect conductor / short maps to an
            infinite conductance, and downstream immittance conversion
            clamps it via eps/max_mag. ``NaN`` is always rejected.
        """
        if math.isnan(self.value):
            raise ValueError("conductance value must not be NaN")
        if self.value < 0:
            raise ValueError("conductance value must be non-negative")

        if self.unit not in CONDUCTANCE_FACTORS:
            raise ValueError(
                f"invalid conductance unit: {self.unit}. "
                f"allowed: {list(CONDUCTANCE_FACTORS.keys())}"
            )

    def get_value(self) -> float:
        """Return the conductance value."""
        return self.value

    def get_unit(self) -> str:
        """Return the conductance unit."""
        return self.unit

    def to_base_unit(self) -> FloatConductanceDto:
        """Convert to the base-unit (S) DTO."""
        if self.unit == "S":
            return self
        base_value = self.value * CONDUCTANCE_FACTORS[self.unit]
        return FloatConductanceDto(value=base_value, unit="S")

    def convert_to_unit(self, target_unit: str) -> FloatConductanceDto:
        """Convert to the specified unit."""
        if target_unit not in CONDUCTANCE_FACTORS:
            raise ValueError(
                f"invalid conductance unit: {target_unit}. "
                f"allowed: {list(CONDUCTANCE_FACTORS.keys())}"
            )
        if target_unit == self.unit:
            return self

        base = self.to_base_unit()
        factor = CONDUCTANCE_FACTORS[target_unit]
        converted_value = base.value / factor
        return FloatConductanceDto(value=converted_value, unit=target_unit)


@dataclass(frozen=True)
class FloatInductanceDto(IFloatWithUnitDto):
    """DTO for a scalar inductance value.

    Attributes:
        value: Inductance value.
        unit: Inductance unit (H, mH, kH, MH).
    """

    value: float
    unit: str = "H"

    def __post_init__(self) -> None:
        """Validate the instance.

        Note:
            ``inf`` is allowed for consistency with the other passive
            immittance DTOs; downstream conversion clamps extreme values
            via eps/max_mag. ``NaN`` is always rejected.
        """
        if math.isnan(self.value):
            raise ValueError("inductance value must not be NaN")
        if self.value < 0:
            raise ValueError("inductance value must be non-negative")

        if self.unit not in INDUCTANCE_FACTORS:
            raise ValueError(
                f"invalid inductance unit: {self.unit}. "
                f"allowed: {list(INDUCTANCE_FACTORS.keys())}"
            )

    def get_value(self) -> float:
        """Return the inductance value."""
        return self.value

    def get_unit(self) -> str:
        """Return the inductance unit."""
        return self.unit

    def to_base_unit(self) -> FloatInductanceDto:
        """Convert to the base-unit (H) DTO."""
        if self.unit == "H":
            return self
        base_value = self.value * INDUCTANCE_FACTORS[self.unit]
        return FloatInductanceDto(value=base_value, unit="H")

    def convert_to_unit(self, target_unit: str) -> FloatInductanceDto:
        """Convert to the specified unit."""
        if target_unit not in INDUCTANCE_FACTORS:
            raise ValueError(
                f"invalid inductance unit: {target_unit}. "
                f"allowed: {list(INDUCTANCE_FACTORS.keys())}"
            )
        if target_unit == self.unit:
            return self

        base = self.to_base_unit()
        factor = INDUCTANCE_FACTORS[target_unit]
        converted_value = base.value / factor
        return FloatInductanceDto(value=converted_value, unit=target_unit)


@dataclass(frozen=True)
class FloatCapacitanceDto(IFloatWithUnitDto):
    """DTO for a scalar capacitance value.

    Attributes:
        value: Capacitance value.
        unit: Capacitance unit (F, mF, uF, nF, pF).
    """

    value: float
    unit: str = "F"

    def __post_init__(self) -> None:
        """Validate the instance.

        Note:
            ``inf`` is allowed: a ground fault maps to an infinite
            capacitance, and downstream immittance conversion clamps it
            via eps/max_mag. ``NaN`` is always rejected.
        """
        if math.isnan(self.value):
            raise ValueError("capacitance value must not be NaN")
        if self.value < 0:
            raise ValueError("capacitance value must be non-negative")

        if self.unit not in CAPACITANCE_FACTORS:
            raise ValueError(
                f"invalid capacitance unit: {self.unit}. "
                f"allowed: {list(CAPACITANCE_FACTORS.keys())}"
            )

    def get_value(self) -> float:
        """Return the capacitance value."""
        return self.value

    def get_unit(self) -> str:
        """Return the capacitance unit."""
        return self.unit

    def to_base_unit(self) -> FloatCapacitanceDto:
        """Convert to the base-unit (F) DTO."""
        if self.unit == "F":
            return self
        base_value = self.value * CAPACITANCE_FACTORS[self.unit]
        return FloatCapacitanceDto(value=base_value, unit="F")

    def convert_to_unit(self, target_unit: str) -> FloatCapacitanceDto:
        """Convert to the specified unit."""
        if target_unit not in CAPACITANCE_FACTORS:
            raise ValueError(
                f"invalid capacitance unit: {target_unit}. "
                f"allowed: {list(CAPACITANCE_FACTORS.keys())}"
            )
        if target_unit == self.unit:
            return self

        base = self.to_base_unit()
        factor = CAPACITANCE_FACTORS[target_unit]
        converted_value = base.value / factor
        return FloatCapacitanceDto(value=converted_value, unit=target_unit)
