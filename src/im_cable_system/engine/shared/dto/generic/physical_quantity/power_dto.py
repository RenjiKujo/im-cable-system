from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from im_cable_system.engine.shared.dto.generic.interfaces.i_value_with_unit_dto import (
    IArrayWithUnitDto,
    IFloatWithUnitDto,
)

# Active power unit factors (base unit: W)
ACTIVE_POWER_FACTORS: dict[str, float] = {
    "MW": 1_000_000.0,
    "kW": 1_000.0,
    "W": 1.0,
    "HP": 745.699872,  # Imperial horsepower: 1 HP = 745.699872 W
}

# Reactive power unit factors (base unit: var)
REACTIVE_POWER_FACTORS: dict[str, float] = {
    "Mvar": 1_000_000.0,
    "kvar": 1_000.0,
    "var": 1.0,
}

# Apparent power unit factors (base unit: VA)
APPARENT_POWER_FACTORS: dict[str, float] = {
    "MVA": 1_000_000.0,
    "kVA": 1_000.0,
    "VA": 1.0,
}


@dataclass(frozen=True)
class FloatActivePowerDto(IFloatWithUnitDto):
    """DTO for scalar active power (P).

    Attributes:
        value: Active power value.
        unit: Power unit (W, kW, MW, HP).
    """

    value: float
    unit: str

    def __post_init__(self) -> None:
        """Validate the instance."""
        if not isinstance(self.value, (int, float)):
            raise ValueError("active power value must be numeric")
        if not np.isfinite(self.value):
            raise ValueError("active power value must not contain NaN/inf")
        if self.value < 0:
            raise ValueError("active power value must be non-negative")

        if self.unit not in ACTIVE_POWER_FACTORS:
            raise ValueError(f"invalid active power unit: {self.unit}")

    def get_value(self) -> float:
        """Return the active power value."""
        return self.value

    def get_unit(self) -> str:
        """Return the active power unit."""
        return self.unit

    def to_base_unit(self) -> FloatActivePowerDto:
        """Convert to the base-unit (W) DTO."""
        if self.unit == "W":
            return self
        base_value = self.value * ACTIVE_POWER_FACTORS[self.unit]
        return FloatActivePowerDto(base_value, "W")

    def convert_to_unit(self, target_unit: str) -> FloatActivePowerDto:
        """Convert to the specified unit."""
        if target_unit not in ACTIVE_POWER_FACTORS:
            raise ValueError(f"invalid active power unit: {target_unit}")
        if target_unit == self.unit:
            return self

        base_value = self.to_base_unit().value
        reverse = {
            unit: (1.0 / factor)
            for unit, factor in ACTIVE_POWER_FACTORS.items()
        }
        converted_value = base_value * reverse[target_unit]
        return FloatActivePowerDto(converted_value, target_unit)


@dataclass(frozen=True)
class FloatReactivePowerDto(IFloatWithUnitDto):
    """DTO for scalar reactive power (Q).

    Attributes:
        value: Reactive power value.
        unit: Power unit (var, kvar, Mvar).
    """

    value: float
    unit: str

    def __post_init__(self) -> None:
        """Validate the instance."""
        if not isinstance(self.value, (int, float)):
            raise ValueError("reactive power value must be numeric")
        if not np.isfinite(self.value):
            raise ValueError("reactive power value must not contain NaN/inf")
        if self.value < 0:
            raise ValueError("reactive power value must be non-negative")

        if self.unit not in REACTIVE_POWER_FACTORS:
            raise ValueError(f"invalid reactive power unit: {self.unit}")

    def get_value(self) -> float:
        """Return the reactive power value."""
        return self.value

    def get_unit(self) -> str:
        """Return the reactive power unit."""
        return self.unit

    def to_base_unit(self) -> FloatReactivePowerDto:
        """Convert to the base-unit (var) DTO."""
        if self.unit == "var":
            return self
        base_value = self.value * REACTIVE_POWER_FACTORS[self.unit]
        return FloatReactivePowerDto(base_value, "var")

    def convert_to_unit(self, target_unit: str) -> FloatReactivePowerDto:
        """Convert to the specified unit."""
        if target_unit not in REACTIVE_POWER_FACTORS:
            raise ValueError(f"invalid reactive power unit: {target_unit}")
        if target_unit == self.unit:
            return self

        base_value = self.to_base_unit().value
        reverse = {
            unit: (1.0 / factor)
            for unit, factor in REACTIVE_POWER_FACTORS.items()
        }
        converted_value = base_value * reverse[target_unit]
        return FloatReactivePowerDto(converted_value, target_unit)


@dataclass(frozen=True)
class FloatApparentPowerDto(IFloatWithUnitDto):
    """DTO for scalar apparent power (S).

    Attributes:
        value: Apparent power value.
        unit: Power unit (VA, kVA, MVA).
    """

    value: float
    unit: str

    def __post_init__(self) -> None:
        """Validate the instance."""
        if not isinstance(self.value, (int, float)):
            raise ValueError("apparent power value must be numeric")
        if not np.isfinite(self.value):
            raise ValueError("apparent power value must not contain NaN/inf")
        if self.value < 0:
            raise ValueError("apparent power value must be non-negative")

        if self.unit not in APPARENT_POWER_FACTORS:
            raise ValueError(f"invalid apparent power unit: {self.unit}")

    def get_value(self) -> float:
        """Return the apparent power value."""
        return self.value

    def get_unit(self) -> str:
        """Return the apparent power unit."""
        return self.unit

    def to_base_unit(self) -> FloatApparentPowerDto:
        """Convert to the base-unit (VA) DTO."""
        if self.unit == "VA":
            return self
        base_value = self.value * APPARENT_POWER_FACTORS[self.unit]
        return FloatApparentPowerDto(base_value, "VA")

    def convert_to_unit(self, target_unit: str) -> FloatApparentPowerDto:
        """Convert to the specified unit."""
        if target_unit not in APPARENT_POWER_FACTORS:
            raise ValueError(f"invalid apparent power unit: {target_unit}")
        if target_unit == self.unit:
            return self

        base_value = self.to_base_unit().value
        reverse = {
            unit: (1.0 / factor)
            for unit, factor in APPARENT_POWER_FACTORS.items()
        }
        converted_value = base_value * reverse[target_unit]
        return FloatApparentPowerDto(converted_value, target_unit)


@dataclass(frozen=True)
class ArrayComplexPowerDto(IArrayWithUnitDto):
    """DTO for a complex power array (S).

    All methods accept only ``np.ndarray`` values for power calculations.

    Attributes:
        value: Complex power array.
        unit: Power unit (W, kW, MW).
    """

    value: np.ndarray
    unit: str = "VA"

    def __post_init__(self) -> None:
        """Validate and coerce the internal array type.

        - Coerces ``value`` to ``np.ndarray[np.complex128]``.
        - Rejects NaN/inf.
        - Rejects zero-length arrays.
        """
        arr = np.asarray(self.value, dtype=np.complex128)
        if arr.size == 0:
            raise ValueError("power array must not be empty")
        if not np.all(np.isfinite(arr)):
            raise ValueError("power array must not contain NaN/inf")
        object.__setattr__(self, "value", arr)

        if self.unit not in APPARENT_POWER_FACTORS:
            raise ValueError(
                f"invalid power unit: {self.unit}. "
                f"allowed: {list(APPARENT_POWER_FACTORS.keys())}"
            )

    def get_value(self) -> np.ndarray:
        """Return the power array."""
        return self.value

    def get_unit(self) -> str:
        """Return the power unit."""
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

    def to_base_unit(self) -> ArrayComplexPowerDto:
        """Convert to the base-unit (VA) DTO.

        Returns:
            DTO with the complex power array normalized to VA.
        """
        if self.unit == "VA":
            return self
        base_value = self.value * APPARENT_POWER_FACTORS[self.unit]
        return ArrayComplexPowerDto(value=base_value, unit="VA")

    def convert_to_unit(
        self,
        target_unit: str,
    ) -> ArrayComplexPowerDto:
        """Return a new DTO converted to the specified unit.

        Args:
            target_unit: Target unit (VA, kVA, MVA).

        Returns:
            Converted DTO.
        """
        if target_unit not in APPARENT_POWER_FACTORS:
            raise ValueError(f"invalid complex power unit: {target_unit}")
        if target_unit == self.unit:
            return self

        base = self.to_base_unit().value
        reverse = {
            unit: (1.0 / factor)
            for unit, factor in APPARENT_POWER_FACTORS.items()
        }
        converted = base * reverse[target_unit]
        return ArrayComplexPowerDto(value=converted, unit=target_unit)

    def get_magnitude(self) -> np.ndarray:
        """Return power magnitude."""
        return np.abs(self.value)

    def get_phase(self) -> np.ndarray:
        """Return power phase in radians."""
        return np.angle(self.value)

    def get_real_part(self) -> np.ndarray:
        """Return the real part (active power)."""
        return np.real(self.value)

    def get_imaginary_part(self) -> np.ndarray:
        """Return the imaginary part (reactive power)."""
        return np.imag(self.value)

    def to_active_power_array(
        self,
        unit: str = "W",
    ) -> ArrayActivePowerDto:
        """Convert to an active power array DTO.

        Args:
            unit: Output active power unit (W, kW, MW).

        Returns:
            Active power array DTO.
        """
        base_s = self.to_base_unit()
        active_base = np.real(base_s.value)
        return ArrayActivePowerDto.from_base_value(
            value=active_base,
            target_unit=unit,
        )

    def to_reactive_power_array(
        self,
        unit: str = "var",
    ) -> ArrayReactivePowerDto:
        """Convert to a reactive power array DTO.

        Args:
            unit: Output reactive power unit (var, kvar, Mvar).

        Returns:
            Reactive power array DTO.
        """
        base_s = self.to_base_unit()
        reactive_base = np.imag(base_s.value)
        return ArrayReactivePowerDto.from_base_value(
            value=reactive_base,
            target_unit=unit,
        )

    def to_apparent_power_array(
        self,
        unit: str = "VA",
    ) -> ArrayApparentPowerDto:
        """Convert to an apparent power array DTO.

        Args:
            unit: Output apparent power unit (VA, kVA, MVA).

        Returns:
            Apparent power array DTO.
        """
        base_s = self.to_base_unit()
        apparent_base = np.abs(base_s.value)
        return ArrayApparentPowerDto.from_base_value(
            value=apparent_base,
            target_unit=unit,
        )


@dataclass(frozen=True)
class ArrayActivePowerDto(IArrayWithUnitDto):
    """DTO for an active power array (P).

    Attributes:
        value: Active power array.
        unit: Power unit (W, kW, MW).
    """

    value: np.ndarray
    unit: str = "W"

    def __post_init__(self) -> None:
        """Validate the instance."""
        arr = np.asarray(self.value, dtype=np.float64)
        if arr.size == 0:
            raise ValueError("active power array must not be empty")
        if not np.all(np.isfinite(arr)):
            raise ValueError("active power array must not contain NaN/inf")
        object.__setattr__(self, "value", arr)

    def get_value(self) -> np.ndarray:
        """Return the active power array."""
        return self.value

    def get_unit(self) -> str:
        """Return the active power unit."""
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

    def to_base_unit(self) -> ArrayActivePowerDto:
        """Convert to the base-unit (W) DTO."""
        if self.unit == "W":
            return self
        base_value = self.value * ACTIVE_POWER_FACTORS[self.unit]
        return ArrayActivePowerDto(value=base_value, unit="W")

    def convert_to_unit(self, target_unit: str) -> ArrayActivePowerDto:
        """Return a new DTO converted to the specified unit."""
        if target_unit not in ACTIVE_POWER_FACTORS:
            raise ValueError(f"invalid active power unit: {target_unit}")
        if target_unit == self.unit:
            return self

        base = self.to_base_unit().value
        reverse = {
            unit: (1.0 / factor)
            for unit, factor in ACTIVE_POWER_FACTORS.items()
        }
        converted = base * reverse[target_unit]
        return ArrayActivePowerDto(value=converted, unit=target_unit)

    @classmethod
    def from_base_value(
        cls,
        value: np.ndarray,
        target_unit: str = "W",
    ) -> ArrayActivePowerDto:
        """Create a DTO from active power given in W (base unit)."""
        base_dto = cls(value=value, unit="W")
        return base_dto.convert_to_unit(target_unit)


@dataclass(frozen=True)
class ArrayReactivePowerDto(IArrayWithUnitDto):
    """DTO for a reactive power array (Q).

    Attributes:
        value: Reactive power array.
        unit: Power unit (var, kvar, Mvar).
    """

    value: np.ndarray
    unit: str = "var"

    def __post_init__(self) -> None:
        """Validate the instance."""
        arr = np.asarray(self.value, dtype=np.float64)
        if arr.size == 0:
            raise ValueError("reactive power array must not be empty")
        if not np.all(np.isfinite(arr)):
            raise ValueError("reactive power array must not contain NaN/inf")
        object.__setattr__(self, "value", arr)

    def get_value(self) -> np.ndarray:
        """Return the reactive power array."""
        return self.value

    def get_unit(self) -> str:
        """Return the reactive power unit."""
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

    def to_base_unit(self) -> ArrayReactivePowerDto:
        """Convert to the base-unit (var) DTO."""
        if self.unit == "var":
            return self
        base_value = self.value * REACTIVE_POWER_FACTORS[self.unit]
        return ArrayReactivePowerDto(value=base_value, unit="var")

    def convert_to_unit(self, target_unit: str) -> ArrayReactivePowerDto:
        """Return a new DTO converted to the specified unit."""
        if target_unit not in REACTIVE_POWER_FACTORS:
            raise ValueError(f"invalid reactive power unit: {target_unit}")
        if target_unit == self.unit:
            return self

        base = self.to_base_unit().value
        reverse = {
            unit: (1.0 / factor)
            for unit, factor in REACTIVE_POWER_FACTORS.items()
        }
        converted = base * reverse[target_unit]
        return ArrayReactivePowerDto(value=converted, unit=target_unit)

    @classmethod
    def from_base_value(
        cls,
        value: np.ndarray,
        target_unit: str = "var",
    ) -> ArrayReactivePowerDto:
        """Create a DTO from reactive power given in var (base unit)."""
        base_dto = cls(value=value, unit="var")
        return base_dto.convert_to_unit(target_unit)


@dataclass(frozen=True)
class ArrayApparentPowerDto(IArrayWithUnitDto):
    """DTO for an apparent power array (S).

    Attributes:
        value: Apparent power array.
        unit: Power unit (VA, kVA, MVA).
    """

    value: np.ndarray
    unit: str = "VA"

    def __post_init__(self) -> None:
        """Validate the instance."""
        arr = np.asarray(self.value, dtype=np.float64)
        if arr.size == 0:
            raise ValueError("apparent power array must not be empty")
        if not np.all(np.isfinite(arr)):
            raise ValueError("apparent power array must not contain NaN/inf")
        object.__setattr__(self, "value", arr)

    def get_value(self) -> np.ndarray:
        """Return the apparent power array."""
        return self.value

    def get_unit(self) -> str:
        """Return the apparent power unit."""
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

    def to_base_unit(self) -> ArrayApparentPowerDto:
        """Convert to the base-unit (VA) DTO."""
        if self.unit == "VA":
            return self
        base_value = self.value * APPARENT_POWER_FACTORS[self.unit]
        return ArrayApparentPowerDto(value=base_value, unit="VA")

    def convert_to_unit(self, target_unit: str) -> ArrayApparentPowerDto:
        """Return a new DTO converted to the specified unit."""
        if target_unit not in APPARENT_POWER_FACTORS:
            raise ValueError(f"invalid apparent power unit: {target_unit}")
        if target_unit == self.unit:
            return self

        base = self.to_base_unit().value
        reverse = {
            unit: (1.0 / factor)
            for unit, factor in APPARENT_POWER_FACTORS.items()
        }
        converted = base * reverse[target_unit]
        return ArrayApparentPowerDto(value=converted, unit=target_unit)

    @classmethod
    def from_base_value(
        cls,
        value: np.ndarray,
        target_unit: str = "VA",
    ) -> ArrayApparentPowerDto:
        """Create a DTO from apparent power given in VA (base unit)."""
        base_dto = cls(value=value, unit="VA")
        return base_dto.convert_to_unit(target_unit)
