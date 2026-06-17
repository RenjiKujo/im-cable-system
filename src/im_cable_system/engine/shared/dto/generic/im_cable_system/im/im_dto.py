"""Induction motor (IM) input DTO classes.

Defines input DTOs for individual IM instances and IM series shared data.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from im_cable_system.engine.shared.dto.generic.im_cable_system.im.im_excitation_model_dto import (  # noqa: E501
    ImExcitationModelDto,
)
from im_cable_system.engine.shared.dto.generic.im_cable_system.im.im_name import (
    ImName,
)
from im_cable_system.engine.shared.dto.generic.im_cable_system.im.im_primary_model_dto import (  # noqa: E501
    ImPrimaryModelDto,
)
from im_cable_system.engine.shared.dto.generic.im_cable_system.im.im_secondary_model_dto import (  # noqa: E501
    ImCageMultiplicityType,
    ImSecondaryCageBranchType,
    ImSecondaryModelDto,
    expected_branch_keys_for_cage_multiplicity,
)
from im_cable_system.engine.shared.dto.generic.im_cable_system.im.im_series_name import (
    ImSeriesName,
)
from im_cable_system.engine.shared.dto.generic.im_cable_system.im.im_type import (  # noqa: E501
    ImCircuitType,
    ImConnectionType,
    ImPoles,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    FloatActivePowerDto,
    FloatCurrentDto,
    FloatFrequencyDto,
    FloatInductanceDto,
    FloatResistanceDto,
    FloatVoltageDto,
)


@dataclass(frozen=True)
class ImSeriesDto:
    """Motor series input DTO.

    Holds shared data for a motor series. Multiple instances of the same series
    can share this DTO to reduce memory use.

    Attributes:
        name: Motor series name (unique identifier).

        poles: Number of poles.
        nameplate_voltage: Rated voltage.
        nameplate_current: Rated current.
        nameplate_power: Rated power.
        nameplate_frequency: Rated frequency.

        connection_type: Winding connection type.
        circuit_type: Circuit type.

        primary_model: Primary circuit model.
        primary_resistance: Primary resistance.
        primary_inductance: Primary inductance.

        excitation_model: Excitation circuit model.
        excitation_resistance: Excitation resistance.
        excitation_inductance: Excitation inductance.

        cage_multiplicity: Cage multiplicity (single or double).
        secondary_models: Secondary circuit models keyed by branch.
        secondary_resistances: Secondary resistances keyed by branch.
        secondary_inductances: Secondary inductances keyed by branch.

    Note:
        Secondary R/L and models are always stored in dicts keyed by
        :class:`ImSecondaryCageBranchType`. For a single cage only ``SINGLE``
        is used; for a double cage only ``INNER`` and ``OUTER`` (validated in
        ``__post_init__`` against ``cage_multiplicity``).
    """

    name: ImSeriesName

    # Basic motor information
    poles: ImPoles
    nameplate_voltage: FloatVoltageDto
    nameplate_current: FloatCurrentDto
    nameplate_power: FloatActivePowerDto
    nameplate_frequency: FloatFrequencyDto

    # Motor circuit information
    connection_type: ImConnectionType
    circuit_type: ImCircuitType

    # Primary circuit parameters
    primary_model: ImPrimaryModelDto
    primary_resistance: FloatResistanceDto
    primary_inductance: FloatInductanceDto

    # Excitation circuit parameters
    excitation_model: ImExcitationModelDto
    excitation_resistance: FloatResistanceDto
    excitation_inductance: FloatInductanceDto

    # Secondary circuit parameters
    cage_multiplicity: ImCageMultiplicityType
    secondary_models: dict[ImSecondaryCageBranchType, ImSecondaryModelDto]
    secondary_resistances: dict[ImSecondaryCageBranchType, FloatResistanceDto]
    secondary_inductances: dict[ImSecondaryCageBranchType, FloatInductanceDto]

    def __post_init__(self) -> None:
        """Verify secondary dict keys match cage_multiplicity.

        Raises:
            ValueError: When keys do not match the expected branch set.
        """
        expected = expected_branch_keys_for_cage_multiplicity(
            self.cage_multiplicity
        )
        for label, branch_map in (
            ("secondary_models", self.secondary_models),
            ("secondary_resistances", self.secondary_resistances),
            ("secondary_inductances", self.secondary_inductances),
        ):
            keys = frozenset(branch_map.keys())
            if keys != expected:
                raise ValueError(
                    f"{label} keys are invalid for "
                    f"cage_multiplicity={self.cage_multiplicity!s}. "
                    f"Expected: {sorted(b.value for b in expected)}, "
                    f"actual: {sorted(b.value for b in keys)}"
                )


@dataclass(frozen=True)
class ImDto:
    """Induction motor (IM) input DTO.

    Holds input data for an individual IM instance. Shared series data is
    referenced via ImSeriesDto.

    Attributes:
        name: Unique IM identifier (position type). Use UPPER or LOWER in
            tandem arrangements, or SINGLE for a standalone motor.
        im_series: Series details (required).
    """

    im_series: ImSeriesDto
    name: ImName = field(default_factory=lambda: ImName(value="SINGLE"))

    def __post_init__(self) -> None:
        """Validate required fields."""
        if self.im_series is None:
            raise ValueError("im_series is required.")
