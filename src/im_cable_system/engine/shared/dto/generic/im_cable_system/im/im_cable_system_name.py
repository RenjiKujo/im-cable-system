"""IM cable system name identifier."""

from __future__ import annotations

from dataclasses import dataclass

from im_cable_system.engine.shared.dto.generic.im_cable_system.base.base_name_id import (  # noqa: E501
    BaseNameId,
    validate_non_blank_after_strip,
)


@dataclass(frozen=True, eq=False)
class ImCableSystemName(BaseNameId):
    """Unique identifier for an IM-and-cable system.

    Holds two distinct identities as one composite value instead of two
    sibling fields:

    - ``base``: the display name of the *measured object* (e.g. one
      performance curve). Human-facing; shared by every candidate derived
      from the same curve.
    - ``discriminator``: the suffix that distinguishes one *computational
      run* (e.g. one model-structure candidate) from another over the same
      ``base``. ``None`` when there is only ever one run per object (forward).

    ``value`` (the identifier used as file name / CSV row identifier /
    report key) is derived by joining the two. Use ``get_base()`` — never
    ``value`` — for display purposes such as figure titles, since ``value``
    is not unique-per-object when a ``discriminator`` is present.

    Note:
        Equality/hashing (``BaseNameId``) compare ``value`` only, not the
        ``base``/``discriminator`` split. Two instances whose joined strings
        coincide (e.g. ``base="A_1", discriminator=None`` vs.
        ``base="A", discriminator="1"``) compare equal even though
        ``get_base()`` differs. In practice this does not occur: within one
        run, every instance shares the same ``base`` (one measured object)
        and only ``discriminator`` varies across candidates.
    """

    base: str
    discriminator: str | None = None

    def __post_init__(self) -> None:
        """Validate the base name and, if present, the discriminator."""
        validate_non_blank_after_strip(self.base, "IM cable system base name")
        if self.discriminator is not None:
            validate_non_blank_after_strip(
                self.discriminator, "IM cable system name discriminator"
            )

    @property
    def value(self) -> str:
        """Return the identifier string (``base`` plus ``discriminator``)."""
        if self.discriminator is None:
            return self.base
        return f"{self.base}_{self.discriminator}"

    def get_base(self) -> str:
        """Return the display-only base name (discriminator stripped)."""
        return self.base
