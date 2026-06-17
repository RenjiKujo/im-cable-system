"""Cable input DTO classes.

This module defines input DTOs for cable data in the IM cable system.
"""

from __future__ import annotations

from dataclasses import dataclass

from im_cable_system.engine.shared.dto.generic.entity import (
    BaseEntityDto,
)
from im_cable_system.engine.shared.dto.generic.im_cable_system.cable.cable_model_dto import (  # noqa: E501
    CableConductorModelDto,
)
from im_cable_system.engine.shared.dto.generic.im_cable_system.cable.cable_name import (
    CableName,
)
from im_cable_system.engine.shared.dto.generic.im_cable_system.cable.cable_section_name import (  # noqa: E501
    CableSectionName,
)
from im_cable_system.engine.shared.dto.generic.im_cable_system.cable.cable_series_name import (  # noqa: E501
    CableSeriesName,
)
from im_cable_system.engine.shared.dto.generic.im_cable_system.cable.cable_types_dto import (  # noqa: E501
    CableShapeTypeDto,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    FloatCapacitancePerLengthDto,
    FloatInductancePerLengthDto,
    FloatLengthDto,
    FloatResistanceLengthDto,
    FloatResistancePerLengthDto,
)


@dataclass(frozen=True)
class CableSeriesDto:
    """Cable series input DTO.

    Holds shared data for a cable series. Multiple instances of the same series
    can share this DTO to reduce memory use.

    Attributes:
        name: Cable series name (unique identifier). Use a field-specific
            implementation (e.g. MubarrazCableSeriesNameV1) when required.

        shape_type: Cable shape type.

        conductor_resistance_per_length: Conductor resistance per unit length.
        conductor_inductance_per_length: Conductor inductance per unit length.

        ground_resistance_length: Ground connection resistance-length product
            (resistance × length, Ω·m). May be infinite.
        ground_capacitance_per_length: Ground connection capacitance per unit
            length. May be infinite.
    """

    name: CableSeriesName

    # Basic cable information
    shape_type: CableShapeTypeDto

    # Conductor parameters (per-length)
    conductor_resistance_per_length: FloatResistancePerLengthDto
    conductor_inductance_per_length: FloatInductancePerLengthDto

    # Ground connection parameters (per-length)
    ground_resistance_length: FloatResistanceLengthDto
    ground_capacitance_per_length: FloatCapacitancePerLengthDto


class CableSeriesDtos(BaseEntityDto[CableSeriesDto]):
    """Collection DTO for cable series.

    Manages multiple cable series entries. Each series is uniquely identified
    by its ``name`` attribute.
    """

    def __init__(self, objects: list[CableSeriesDto]) -> None:
        """Initialize the collection.

        Args:
            objects: Initial list of CableSeriesDto instances.
        """
        super().__init__(objects=objects, attribute_name="name")


@dataclass(frozen=True)
class CableSectionDto:
    """Cable section input DTO.

    Holds input data for an individual section (segment) within a cable.
    Section name and series have a one-to-one relationship.

    Attributes:
        name: Cable section name (segment name). Use a field-specific
            implementation (e.g. MubarrazCableSegmentNameV1) when required.
        length: Section length. Supports SI (m, km, cm, mm) and field units
            (ft, in, yd, mi).
        series: Series details (required).
    """

    name: CableSectionName
    length: FloatLengthDto
    series: CableSeriesDto

    def __post_init__(self) -> None:
        """Validate section and series consistency."""
        if self.series is None:
            raise ValueError("series is required.")
        # When the section name provides get_allowed_series_names(), validate
        # the section/series combination via duck typing for any field impl.
        get_allowed_series_names = getattr(
            self.name, "get_allowed_series_names", None
        )
        if get_allowed_series_names is not None:
            allowed_series = get_allowed_series_names()  # type: ignore[attr-defined]
            if allowed_series:  # check only when non-empty
                series_value = self.series.name.get_value()
                if series_value not in allowed_series:
                    raise ValueError(
                        f"For section name '{self.name.get_value()}', "
                        f"cable series name '{series_value}' is not allowed. "
                        f"Allowed series names: {allowed_series}"
                    )


class CableSectionDtos(BaseEntityDto[CableSectionDto]):
    """Collection DTO for cable section input.

    Manages multiple cable sections. Each section is uniquely identified by
    its ``name`` attribute.
    """

    def __init__(self, objects: list[CableSectionDto]) -> None:
        """Initialize the collection.

        Args:
            objects: Initial list of CableSectionDto instances.
        """
        super().__init__(objects=objects, attribute_name="name")


@dataclass(frozen=True)
class CableDto:
    """Cable input DTO.

    Holds input data for an individual cable instance. A cable consists of
    multiple sections (segments). Each section has a series; section name and
    series have a one-to-one relationship.

    Attributes:
        name: Unique cable identifier (e.g. "SINGLE", "TOP", "BOTTOM"). Use a
            field-specific implementation (e.g. MubarrazCableNameV1) when
            required.
        sections: Collection of cable sections forming this cable.
        conductor_model: Conductor circuit model type and parameters.
    """

    name: CableName
    sections: CableSectionDtos
    conductor_model: CableConductorModelDto

    def calculate_total_length(self) -> FloatLengthDto:
        """Compute total cable length.

        Sums all section lengths converted to the base unit (m) and returns a
        FloatLengthDto in base units (m).

        Returns:
            Total cable length in base units (m). Returns 0.0 m when there are
            no sections.
        """
        total_length_m = 0.0
        for section in self.sections.get_all():
            base_length = section.length.to_base_unit()
            total_length_m += base_length.value
        return FloatLengthDto(value=total_length_m, unit="m")


class CableDtos(BaseEntityDto[CableDto]):
    """Collection DTO for cable input.

    Manages multiple cables. Each cable is uniquely identified by its ``name``
    attribute.
    """

    def __init__(self, objects: list[CableDto]) -> None:
        """Initialize the collection.

        Args:
            objects: Initial list of CableDto instances.
        """
        super().__init__(objects=objects, attribute_name="name")
