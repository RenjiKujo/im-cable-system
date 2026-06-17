"""Validation result DTOs (public export).

Responsibilities:
  - Return value of validation functions based on physical laws and constraints
    (``ValidationResultDto``).

Implementation lives in ``validation_result_dto``. For cross-layer use,
import from this package's ``__all__``.
"""

from im_cable_system.engine.shared.dto.generic.validation.validation_result_dto import (
    ValidationResultDto,
)

__all__ = [
    "ValidationResultDto",
]
