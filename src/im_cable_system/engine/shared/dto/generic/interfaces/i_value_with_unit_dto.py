"""Interfaces for DTOs that carry a value and a unit.

Defines a shared contract for physical quantities (voltage, current, power,
frequency, and so on): each DTO holds a value and a unit and supports
unit conversion.

- ``IFloatWithUnitDto``: scalar (``float``)
- ``IArrayWithUnitDto``: array (``np.ndarray``)

## Rationale

1. **Explicit contract**: Centralizes behavior required of physical-quantity DTOs
   (get value/unit, convert to base unit, convert to a target unit).
2. **Unified unit conversion**: Callers use the same methods (``get_value``,
   ``to_base_unit``, and so on) even when implementations differ by quantity
   (voltage, current, power, etc.).
3. **Extensibility**: New physical-quantity DTOs can be added without changing
   existing call sites.
4. **Static checking**: Ensures implementors define required methods.

## Why interfaces do not use ``@dataclass``

Only the contract (abstract methods) lives here; each concrete class defines its
data layout with ``@dataclass(frozen=True)``.

- Applying ``@dataclass`` on the interface tends to force attribute redefinition
  and field-order mismatches on concrete classes.
- Scalar and array variants use different types for ``value``, so the
  interface does not fix that type.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    import numpy as np  # noqa: F401

TArray = TypeVar("TArray", bound="IArrayWithUnitDto")
TFloat = TypeVar("TFloat", bound="IFloatWithUnitDto")


class IFloatWithUnitDto(ABC):
    """Interface for a DTO with a floating-point value and a unit.

    Defines access to a scalar value, its unit, and conversion to base or target
    units.

    Notes:
        Implementations must:

        - expose ``value: float`` and ``unit: str``
        - return their own type from ``to_base_unit()`` and ``convert_to_unit()``

    Validation:
        ``__post_init__`` on implementations must validate:

        **value**
            - numeric (``int`` or ``float``)
            - ``NaN`` is always rejected
            - finite by default. Passive immittance DTOs (R/L/C and their
              per-length variants) are the documented exception: they allow
              ``inf`` to express open/short/insulation/fault extremes, which
              downstream conversion clamps via eps/max_mag.
            - within a physically valid range for that quantity

        **unit**
            - listed among units allowed by that implementation class
    """

    @abstractmethod
    def get_value(self) -> float:
        """Return the floating-point value.

        Returns:
            float: Scalar value.
        """
        pass

    @abstractmethod
    def get_unit(self) -> str:
        """Return the unit string.

        Returns:
            str: Unit.
        """
        pass

    @abstractmethod
    def to_base_unit(self: TFloat) -> TFloat:
        """Convert to the base unit.

        Returns:
            TFloat: DTO expressed in the base unit (same concrete type).
        """
        pass

    @abstractmethod
    def convert_to_unit(self: TFloat, target_unit: str) -> TFloat:
        """Return a DTO converted to the given unit.

        Args:
            target_unit: Target unit.

        Returns:
            TFloat: DTO in ``target_unit`` (same concrete type).

        Raises:
            ValueError: If ``target_unit`` is not supported.
        """
        pass


class IArrayWithUnitDto(ABC):
    """Interface for a DTO with an array value and a unit.

    Defines access to array data, shape, dimensionality, and unit conversion.

    Notes:
        Implementations must:

        - expose ``value: np.ndarray`` and ``unit: str``
        - implement ``get_shape()`` and ``get_ndim()``
        - return their own type from ``to_base_unit()`` and ``convert_to_unit()``

    Validation:
        ``__post_init__`` on implementations must validate:

        **value**
            - an ``np.ndarray`` (or convertible via ``np.asarray``)
            - non-empty (``arr.size > 0``)
            - all elements finite (``np.all(np.isfinite(arr))``) by default
            - ``dtype`` normalized when required
            - within a physically valid range per element for that quantity

        **unit**
            - listed among units allowed by that implementation class

    Notes:
        ``inf`` is always rejected (project-wide rule). The "all elements
        finite" requirement above is the default contract; a few
        characteristic-value DTOs relax it to allow ``NaN`` as an
        "undefined-sample" marker (never ``inf``):

        - ``ArrayTorqueDto`` allows ``NaN`` so that a domain computation can
          mark samples where torque is undefined (e.g. ``omega ≈ 0`` →
          ``P / omega``) without rebuilding the array. Container DTOs that
          bundle observed curves (e.g. ``ImPerformanceCurveCatalogDto``)
          impose a stricter contract on top and reject ``NaN`` in their
          series values, expressing unobserved points via a mask instead.

        Implementations that allow ``NaN`` must document the reason on their
        own class docstring and still reject ``inf``.
    """

    @abstractmethod
    def get_value(self) -> np.ndarray:
        """Return the array value.

        Returns:
            np.ndarray: Array value.
        """
        pass

    @abstractmethod
    def get_unit(self) -> str:
        """Return the unit string.

        Returns:
            str: Unit.
        """
        pass

    @abstractmethod
    def get_shape(self) -> tuple[int, ...]:
        """Return the array shape.

        Returns:
            tuple[int, ...]: Shape (size per dimension).
        """
        pass

    @abstractmethod
    def get_ndim(self) -> int:
        """Return the number of dimensions.

        Returns:
            int: Number of dimensions.
        """
        pass

    @abstractmethod
    def to_base_unit(self: TArray) -> TArray:
        """Convert to the base unit.

        Returns:
            TArray: DTO expressed in the base unit (same concrete type).
        """
        pass

    @abstractmethod
    def convert_to_unit(self: TArray, target_unit: str) -> TArray:
        """Return a DTO converted to the given unit.

        Args:
            target_unit: Target unit.

        Returns:
            TArray: DTO in ``target_unit`` (same concrete type).

        Raises:
            ValueError: If ``target_unit`` is not supported.
        """
        pass
