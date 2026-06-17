"""Generic DTO package.

Provides value objects (DTOs) used across the engine layer, organized into
subpackages by responsibility.

Note:
    Do not import directly from this package root
    (``im_cable_system.engine.shared.dto.generic``).
    Import required types from the corresponding subpackage public API
    (``entity``, ``validation``, ``physical_quantity``, ``im_cable_system``,
    ``interfaces``).

    Examples:
        - OK: ``from im_cable_system.engine.shared.dto.generic.im_cable_system import ArrayLayoutDto, ArrayKey``
        - OK: ``from im_cable_system.engine.shared.dto.generic.physical_quantity import ArrayComplexVoltageDto``
        - OK: ``from im_cable_system.engine.shared.dto.generic.entity import BaseEntityDto``
        - OK: ``from im_cable_system.engine.shared.dto.generic.interfaces import IArrayWithUnitDto``
        - NG: ``from im_cable_system.engine.shared.dto.generic import ArrayLayoutDto``
        - NG: ``from im_cable_system.engine.shared.dto.generic.im_cable_system.array import ArrayKey``
"""
