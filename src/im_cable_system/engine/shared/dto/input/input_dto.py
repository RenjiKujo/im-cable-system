"""Top-level input DTOs for IM cable system simulation.

This module defines the top-level DTOs for input data to the IM cable system
simulation engine.

Independent inputs and reference axes:
    Independent variables for the circuit model (slip, frequency, voltage)
    are specified as reference axes on :class:`ArrayLayoutDto`
    (``reference_axes`` in CARTESIAN layout). Currents are simulation
    results and are never allowed as reference axes.
    Pipeline entry points use slip, frequency, and input_line_voltage as
    reference axes.
    Supported axes:
        - Current: slip, frequency, input_line_voltage
        - Future: temperature, time (degradation / elapsed time)
    Only steady-state operation is modeled; no other independent axes are
    planned.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from im_cable_system.engine.shared.dto.generic.entity import (
    BaseEntityDto,
)
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ArrayKey,
    ArrayLayoutDto,
    CableDto,
    ImCableSystemName,
    ImDto,
    ImPerformanceCurveCatalogDtos,
)

# Axes allowed as reference axes (same as :class:`ArrayKey.reference_axes_members`).
REFERENCE_AXIS_ALLOWED: tuple[ArrayKey, ...] = ArrayKey.reference_axes_members()

# Axes always required in ``arrays`` (pipeline entry: forward, estimate_params, etc.).
REQUIRED_AXES: tuple[ArrayKey, ...] = (
    ArrayKey.FREQUENCY,
    ArrayKey.INPUT_LINE_VOLTAGE,
    ArrayKey.SLIP,
)


def _default_im_pc_catalogs() -> ImPerformanceCurveCatalogDtos:
    """Return an empty performance-curve catalog (default for Input)."""
    return ImPerformanceCurveCatalogDtos(objects=[])


@dataclass(frozen=True)
class InputDto:
    """Top-level input DTO for an induction motor (IM) and cable system.

    Holds surface-measurable attributes for one IM connected to one cable.

    Attributes:
        name: Unique identifier for the IM–cable system.
        im: Induction motor (IM) DTO.
        cable: Cable DTO, or None if no cable is present. When None, model
            build creates a perfect conductor with perfect insulation as a
            pseudo cable; system immittance is the IM immittance alone.
        im_pc_catalogs: Reference IM performance-curve catalogs (1D slip curves
            per supply condition). Missing conditions have no record. Used for
            parameter estimation targets and plotting.
        array_layout: Array layout DTO. ``arrays`` keys must be
            :class:`ArrayKey` values (``array`` public API). ``reference_axes``
            must be subsets of REFERENCE_AXIS_ALLOWED (independent inputs on
            the Enum). Required keys in ``arrays``: frequency,
            input_line_voltage, slip.

    Note:
        Immittance design assumption:
        - Immittances built from this DTO are per-phase star-equivalent values.
          IM connection (star/delta) is handled as single-phase equivalent.
    """

    name: ImCableSystemName
    array_layout: ArrayLayoutDto
    im: ImDto
    cable: CableDto | None = None
    im_pc_catalogs: ImPerformanceCurveCatalogDtos = field(
        default_factory=_default_im_pc_catalogs,
    )

    def __post_init__(self) -> None:
        """Validate layout contract.

        - ``array_layout`` is not None (layout rules are enforced in
          :class:`ArrayLayoutDto` ``__post_init__``).
        - At least one REFERENCE_AXIS_ALLOWED member appears in reference axes.
        - Required axes (frequency, input_line_voltage, slip) exist in
          ``arrays``.
        """
        if self.array_layout is None:
            raise ValueError("array_layout is required.")

        layout = self.array_layout
        effective_axes = layout.reference_axes

        used_allowed = [
            a for a in REFERENCE_AXIS_ALLOWED if a in effective_axes
        ]
        if not used_allowed:
            raise ValueError(
                "Specify at least one REFERENCE_AXIS_ALLOWED axis as a "
                "reference axis. "
                f"Allowed: {list(REFERENCE_AXIS_ALLOWED)}. "
                f"Current reference axes: {effective_axes}"
            )

        missing_axes = [a for a in REQUIRED_AXES if a not in layout.arrays]
        if missing_axes:
            raise ValueError(
                f"array_layout is missing required axes: {missing_axes}. "
                f"Current axis keys: {list(layout.arrays.keys())}"
            )


class InputDtos(BaseEntityDto[InputDto]):
    """Collection DTO for :class:`InputDto` instances.

    Note:
        IM/cable series data are embedded on each ``InputDto``.
        Performance-curve catalogs live on ``InputDto.im_pc_catalogs``; this
        collection does not hold a separate catalog list.
    """

    def __init__(self, objects: list[InputDto]) -> None:
        """Initialize the collection.

        Args:
            objects: Initial list of ``InputDto`` instances.
        """
        super().__init__(objects=objects, attribute_name="name")
