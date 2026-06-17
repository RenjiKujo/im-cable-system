"""RLC per-length (line density) DTO module.

Defines DTO classes for per-unit-length RLC parameters (resistance, inductance,
and capacitance) of cables and transmission lines.

Typical uses:
    - Cable conductor parameters (resistance and inductance per length).
    - Cable earth parameters (capacitance per length, resistance-length product).
    - Distributed parameters of transmission lines.

DTOs defined here:
    - FloatResistancePerLengthDto: resistance per length (e.g. Ω/m, Ω/km).
    - FloatInductancePerLengthDto: inductance per length (e.g. H/m, H/km).
    - FloatCapacitancePerLengthDto: capacitance per length (e.g. F/m, F/km).
    - FloatResistanceLengthDto: resistance times length (e.g. Ω*m, kΩ*ft).

Note:
    Scalar (non per-length) R/L/C DTOs are defined in ``rlc_dto.py``.
    RLC parameters are often fixed scalar circuit values, so array DTOs are
    not provided. When arrays are needed, convert to impedance/admittance
    first and treat them as arrays there.
"""

import math
from dataclasses import dataclass

from im_cable_system.engine.shared.dto.generic.interfaces.i_value_with_unit_dto import (
    IFloatWithUnitDto,
)

# Length conversion factors (base unit: m)
# SI units
SI_UNITS_TO_METER: dict[str, float] = {
    "km": 1000.0,
    "m": 1.0,
    "cm": 0.01,
    "mm": 0.001,
}

# Field units
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

# All supported length units
ALL_LENGTH_UNITS = list(SI_UNITS_TO_METER.keys()) + list(
    FIELD_UNITS_TO_METER.keys()
)

# Combined length conversion factors
ALL_LENGTH_FACTORS = {**SI_UNITS_TO_METER, **FIELD_UNITS_TO_METER}

# Resistance unit factors
RESISTANCE_FACTORS: dict[str, float] = {
    "MΩ": 1_000_000.0,
    "kΩ": 1_000.0,
    "Ω": 1.0,
    "mΩ": 0.001,
}

# Inductance unit factors
INDUCTANCE_FACTORS: dict[str, float] = {
    "MH": 1_000_000.0,
    "kH": 1_000.0,
    "H": 1.0,
    "mH": 0.001,
}

# Capacitance unit factors
CAPACITANCE_FACTORS: dict[str, float] = {
    "F": 1.0,
    "mF": 1e-3,
    "uF": 1e-6,
    "nF": 1e-9,
    "pF": 1e-12,
}


@dataclass(frozen=True)
class FloatResistancePerLengthDto(IFloatWithUnitDto):
    """DTO for resistance per unit length.

    Attributes:
        value: Resistance per length value.
        unit: Resistance per length unit (form: ``resistance_unit/length_unit``).
            Resistance units: Ω, mΩ, kΩ, MΩ.
            Length units (SI): m, km, cm, mm.
            Length units (field): ft, in, yd, mi.
            Examples: ``"Ω/m"``, ``"mΩ/ft"``, ``"kΩ/km"``.
    """

    value: float
    unit: str = "Ω/m"

    def __post_init__(self) -> None:
        """Validate the instance.

        Note:
            ``inf`` is allowed for consistency with the passive immittance
            DTOs; downstream conversion clamps extreme values via
            eps/max_mag. ``NaN`` is always rejected.
        """
        if math.isnan(self.value):
            raise ValueError("resistance per length value must not be NaN")
        if self.value < 0:
            raise ValueError("resistance per length value must be non-negative")

        self._validate_unit_format(self.unit)

    def _validate_unit_format(self, unit: str) -> None:
        """Validate unit string format.

        Args:
            unit: Unit string to validate.

        Raises:
            ValueError: If the unit format is invalid.
        """
        if "/" not in unit:
            raise ValueError(
                f"resistance per length unit must be "
                f"resistance_unit/length_unit: {unit}"
            )

        parts = unit.split("/")
        if len(parts) != 2:
            raise ValueError(
                f"resistance per length unit must be "
                f"resistance_unit/length_unit: {unit}"
            )

        resistance_unit, length_unit = parts

        # Validate resistance unit
        if resistance_unit not in RESISTANCE_FACTORS:
            raise ValueError(
                f"invalid resistance unit: {resistance_unit}. "
                f"allowed: {list(RESISTANCE_FACTORS.keys())}"
            )

        # Validate length unit
        if length_unit not in ALL_LENGTH_UNITS:
            raise ValueError(
                f"invalid length unit: {length_unit}. "
                f"allowed: {ALL_LENGTH_UNITS}"
            )

    def _parse_unit(self, unit: str) -> tuple[str, str]:
        """Split unit string into resistance and length units.

        Args:
            unit: Unit string (e.g. ``"Ω/m"``, ``"mΩ/ft"``).

        Returns:
            Tuple of (resistance unit, length unit).
        """
        parts = unit.split("/")
        if len(parts) != 2:
            raise ValueError(f"invalid unit format: {unit}")
        return parts[0], parts[1]

    def get_value(self) -> float:
        """Return the resistance per length value."""
        return self.value

    def get_unit(self) -> str:
        """Return the resistance per length unit."""
        return self.unit

    def to_base_unit(self) -> "FloatResistancePerLengthDto":
        """Convert to the base-unit (Ω/m) DTO."""
        if self.unit == "Ω/m":
            return self
        resistance_unit, length_unit = self._parse_unit(self.unit)

        # Convert resistance to base unit (Ω)
        resistance_factor = RESISTANCE_FACTORS[resistance_unit]
        resistance_base = self.value * resistance_factor

        # Convert length to base unit (m)
        length_factor = ALL_LENGTH_FACTORS[length_unit]
        # Larger length unit => smaller per-length density
        length_base = resistance_base / length_factor

        return FloatResistancePerLengthDto(value=length_base, unit="Ω/m")

    def convert_to_unit(
        self, target_unit: str
    ) -> "FloatResistancePerLengthDto":
        """Convert to the specified unit."""
        # Validate target unit format
        self._validate_unit_format(target_unit)
        if target_unit == self.unit:
            return self

        # Convert to base unit
        base = self.to_base_unit()

        # Parse target unit
        target_resistance_unit, target_length_unit = self._parse_unit(
            target_unit
        )

        # Resistance unit factors
        resistance_factor = RESISTANCE_FACTORS[target_resistance_unit]
        # From base Ω to target resistance unit
        resistance_converted = base.value / resistance_factor

        # Length conversion factor
        length_factor = ALL_LENGTH_FACTORS[target_length_unit]
        # Larger length unit => smaller per-length density
        length_converted = resistance_converted * length_factor

        return FloatResistancePerLengthDto(
            value=length_converted, unit=target_unit
        )


@dataclass(frozen=True)
class FloatResistanceLengthDto(IFloatWithUnitDto):
    """DTO for resistance times length (unit: resistance*length, e.g. Ω*m).

    Note:
        ``inf`` is allowed because an infinite ground resistance-length
        product represents perfect ground insulation (完全絶縁). ``NaN``
        is always rejected as a meaningless value.
    """

    value: float
    unit: str = "Ω*m"

    def __post_init__(self) -> None:
        """Validate the instance."""
        if math.isnan(self.value):
            raise ValueError("resistance-length product must not be NaN")
        if self.value < 0:
            raise ValueError("resistance-length product must be non-negative")
        self._validate_unit_format(self.unit)

    def _validate_unit_format(self, unit: str) -> None:
        """Validate unit string format."""
        if "*" not in unit:
            raise ValueError(
                f"resistance-length unit must be "
                f"resistance_unit*length_unit: {unit}"
            )
        parts = unit.split("*")
        if len(parts) != 2:
            raise ValueError(
                f"resistance-length unit must be "
                f"resistance_unit*length_unit: {unit}"
            )

        resistance_unit, length_unit = parts
        if resistance_unit not in RESISTANCE_FACTORS:
            raise ValueError(
                f"invalid resistance unit: {resistance_unit}. "
                f"allowed: {list(RESISTANCE_FACTORS.keys())}"
            )
        if length_unit not in ALL_LENGTH_UNITS:
            raise ValueError(
                f"invalid length unit: {length_unit}. "
                f"allowed: {ALL_LENGTH_UNITS}"
            )

    def _parse_unit(self, unit: str) -> tuple[str, str]:
        """Split unit string into resistance and length units."""
        parts = unit.split("*")
        if len(parts) != 2:
            raise ValueError(f"invalid unit format: {unit}")
        return parts[0], parts[1]

    def get_value(self) -> float:
        """Return the value."""
        return self.value

    def get_unit(self) -> str:
        """Return the unit."""
        return self.unit

    def to_base_unit(self) -> "FloatResistanceLengthDto":
        """Convert to the base-unit (Ω*m) DTO."""
        if self.unit == "Ω*m":
            return self
        resistance_unit, length_unit = self._parse_unit(self.unit)
        resistance_factor = RESISTANCE_FACTORS[resistance_unit]
        length_factor = ALL_LENGTH_FACTORS[length_unit]
        base_value = self.value * resistance_factor * length_factor
        return FloatResistanceLengthDto(value=base_value, unit="Ω*m")

    def convert_to_unit(self, target_unit: str) -> "FloatResistanceLengthDto":
        """Convert to the specified unit."""
        self._validate_unit_format(target_unit)
        if target_unit == self.unit:
            return self
        base = self.to_base_unit()
        target_resistance_unit, target_length_unit = self._parse_unit(
            target_unit
        )
        resistance_factor = RESISTANCE_FACTORS[target_resistance_unit]
        length_factor = ALL_LENGTH_FACTORS[target_length_unit]
        converted_value = base.value / (resistance_factor * length_factor)
        return FloatResistanceLengthDto(value=converted_value, unit=target_unit)


@dataclass(frozen=True)
class FloatInductancePerLengthDto(IFloatWithUnitDto):
    """DTO for inductance per unit length.

    Attributes:
        value: Inductance per length value.
        unit: Inductance per length unit (form: ``inductance_unit/length_unit``).
            Inductance units: H, mH, kH, MH.
            Length units (SI): m, km, cm, mm.
            Length units (field): ft, in, yd, mi.
            Examples: ``"H/m"``, ``"mH/ft"``, ``"kH/km"``.
    """

    value: float
    unit: str = "H/m"

    def __post_init__(self) -> None:
        """Validate the instance.

        Note:
            ``inf`` is allowed for consistency with the passive immittance
            DTOs; downstream conversion clamps extreme values via
            eps/max_mag. ``NaN`` is always rejected.
        """
        if math.isnan(self.value):
            raise ValueError("inductance per length value must not be NaN")
        if self.value < 0:
            raise ValueError("inductance per length value must be non-negative")

        self._validate_unit_format(self.unit)

    def _validate_unit_format(self, unit: str) -> None:
        """Validate unit string format.

        Args:
            unit: Unit string to validate.

        Raises:
            ValueError: If the unit format is invalid.
        """
        if "/" not in unit:
            raise ValueError(
                f"inductance per length unit must be "
                f"inductance_unit/length_unit: {unit}"
            )

        parts = unit.split("/")
        if len(parts) != 2:
            raise ValueError(
                f"inductance per length unit must be "
                f"inductance_unit/length_unit: {unit}"
            )

        inductance_unit, length_unit = parts

        # Validate inductance unit
        if inductance_unit not in INDUCTANCE_FACTORS:
            raise ValueError(
                f"invalid inductance unit: {inductance_unit}. "
                f"allowed: {list(INDUCTANCE_FACTORS.keys())}"
            )

        # Validate length unit
        if length_unit not in ALL_LENGTH_UNITS:
            raise ValueError(
                f"invalid length unit: {length_unit}. "
                f"allowed: {ALL_LENGTH_UNITS}"
            )

    def _parse_unit(self, unit: str) -> tuple[str, str]:
        """Split unit string into inductance and length units.

        Args:
            unit: Unit string (e.g. ``"H/m"``, ``"mH/ft"``).

        Returns:
            Tuple of (inductance unit, length unit).
        """
        parts = unit.split("/")
        if len(parts) != 2:
            raise ValueError(f"invalid unit format: {unit}")
        return parts[0], parts[1]

    def get_value(self) -> float:
        """Return the inductance per length value."""
        return self.value

    def get_unit(self) -> str:
        """Return the inductance per length unit."""
        return self.unit

    def to_base_unit(self) -> "FloatInductancePerLengthDto":
        """Convert to the base-unit (H/m) DTO."""
        if self.unit == "H/m":
            return self
        inductance_unit, length_unit = self._parse_unit(self.unit)

        # Convert inductance to base unit (H)
        inductance_factor = INDUCTANCE_FACTORS[inductance_unit]
        inductance_base = self.value * inductance_factor

        # Convert length to base unit (m)
        length_factor = ALL_LENGTH_FACTORS[length_unit]
        # Larger length unit => smaller per-length density
        length_base = inductance_base / length_factor

        return FloatInductancePerLengthDto(value=length_base, unit="H/m")

    def convert_to_unit(
        self, target_unit: str
    ) -> "FloatInductancePerLengthDto":
        """Convert to the specified unit."""
        # Validate target unit format
        self._validate_unit_format(target_unit)
        if target_unit == self.unit:
            return self

        # Convert to base unit
        base = self.to_base_unit()

        # Parse target unit
        target_inductance_unit, target_length_unit = self._parse_unit(
            target_unit
        )

        # Inductance unit factors
        inductance_factor = INDUCTANCE_FACTORS[target_inductance_unit]
        # From base H to target inductance unit
        inductance_converted = base.value / inductance_factor

        # Length conversion factor
        length_factor = ALL_LENGTH_FACTORS[target_length_unit]
        # Larger length unit => smaller per-length density
        length_converted = inductance_converted * length_factor

        return FloatInductancePerLengthDto(
            value=length_converted, unit=target_unit
        )


@dataclass(frozen=True)
class FloatCapacitancePerLengthDto(IFloatWithUnitDto):
    """DTO for capacitance per unit length.

    Attributes:
        value: Capacitance per length value.
        unit: Capacitance per length unit (form: ``capacitance_unit/length_unit``).
            Capacitance units: F, mF, uF, nF, pF.
            Length units (SI): m, km, cm, mm.
            Length units (field): ft, in, yd, mi.
            Examples: ``"F/m"``, ``"mF/ft"``, ``"uF/km"``.
    """

    value: float
    unit: str = "F/m"

    def __post_init__(self) -> None:
        """Validate the instance.

        Note:
            ``inf`` is allowed because an infinite ground capacitance per
            length represents a ground fault (地絡). ``NaN`` is always
            rejected as a meaningless value.
        """
        if math.isnan(self.value):
            raise ValueError("capacitance per length value must not be NaN")
        if self.value < 0:
            raise ValueError(
                "capacitance per length value must be non-negative"
            )

        self._validate_unit_format(self.unit)

    def _validate_unit_format(self, unit: str) -> None:
        """Validate unit string format.

        Args:
            unit: Unit string to validate.

        Raises:
            ValueError: If the unit format is invalid.
        """
        if "/" not in unit:
            raise ValueError(
                f"capacitance per length unit must be "
                f"capacitance_unit/length_unit: {unit}"
            )

        parts = unit.split("/")
        if len(parts) != 2:
            raise ValueError(
                f"capacitance per length unit must be "
                f"capacitance_unit/length_unit: {unit}"
            )

        capacitance_unit, length_unit = parts

        # Validate capacitance unit
        if capacitance_unit not in CAPACITANCE_FACTORS:
            raise ValueError(
                f"invalid capacitance unit: {capacitance_unit}. "
                f"allowed: {list(CAPACITANCE_FACTORS.keys())}"
            )

        # Validate length unit
        if length_unit not in ALL_LENGTH_UNITS:
            raise ValueError(
                f"invalid length unit: {length_unit}. "
                f"allowed: {ALL_LENGTH_UNITS}"
            )

    def _parse_unit(self, unit: str) -> tuple[str, str]:
        """Split unit string into capacitance and length units.

        Args:
            unit: Unit string (e.g. ``"F/m"``, ``"mF/ft"``).

        Returns:
            Tuple of (capacitance unit, length unit).
        """
        parts = unit.split("/")
        if len(parts) != 2:
            raise ValueError(f"invalid unit format: {unit}")
        return parts[0], parts[1]

    def get_value(self) -> float:
        """Return the capacitance per length value."""
        return self.value

    def get_unit(self) -> str:
        """Return the capacitance per length unit."""
        return self.unit

    def to_base_unit(self) -> "FloatCapacitancePerLengthDto":
        """Convert to the base-unit (F/m) DTO."""
        if self.unit == "F/m":
            return self
        capacitance_unit, length_unit = self._parse_unit(self.unit)

        # Convert capacitance to base unit (F)
        capacitance_factor = CAPACITANCE_FACTORS[capacitance_unit]
        capacitance_base = self.value * capacitance_factor

        # Convert length to base unit (m)
        length_factor = ALL_LENGTH_FACTORS[length_unit]
        # Larger length unit => smaller per-length density
        length_base = capacitance_base / length_factor

        return FloatCapacitancePerLengthDto(value=length_base, unit="F/m")

    def convert_to_unit(
        self, target_unit: str
    ) -> "FloatCapacitancePerLengthDto":
        """Convert to the specified unit."""
        # Validate target unit format
        self._validate_unit_format(target_unit)
        if target_unit == self.unit:
            return self

        # Convert to base unit
        base = self.to_base_unit()

        # Parse target unit
        target_capacitance_unit, target_length_unit = self._parse_unit(
            target_unit
        )

        # Capacitance unit factors
        capacitance_factor = CAPACITANCE_FACTORS[target_capacitance_unit]
        # From base F to target capacitance unit
        capacitance_converted = base.value / capacitance_factor

        # Length conversion factor
        length_factor = ALL_LENGTH_FACTORS[target_length_unit]
        # Larger length unit => smaller per-length density
        length_converted = capacitance_converted * length_factor

        return FloatCapacitancePerLengthDto(
            value=length_converted, unit=target_unit
        )
