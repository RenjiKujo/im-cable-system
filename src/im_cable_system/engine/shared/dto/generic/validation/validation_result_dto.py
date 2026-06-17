"""Validation result DTO (generic DTO).

Provides a DTO that represents the outcome of validation functions, shared across
engine layers (simulation, machine learning, optimization) and domain types
(electrical, mechanical, thermal, etc.).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ValidationResultDto:
    """DTO representing a validation outcome.

    Used for results of validation functions based on physical laws and
    constraints. Shared across domain types (electrical, mechanical, thermal,
    etc.).

    Attributes:
        is_valid: True when validation succeeded, False when it failed.
        message: Failure message (empty string on success).
    """

    is_valid: bool
    message: str

    def __post_init__(self) -> None:
        """Validate field consistency."""
        if not self.is_valid and not self.message:
            raise ValueError("When validation failed, message is required")
