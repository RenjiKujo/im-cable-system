"""Shared base (mixin) and validation helpers for name_id implementations.

NOTE:
    Despite the implementation-inheritance guideline in
    ``docs/conventions/2_design_principles.md``, this base
    is limited to ``generic/im_cable_system/im`` and ``cable`` name modules as
    shared boilerplate. String-backed name objects should at least provide
    ``get_value``, equality with ``str``, hashing, and string representation
    (**implementation contract**). Do not import from outside this package tree.
"""

from __future__ import annotations


class BaseNameId:
    """Equality, hashing, and display for frozen dataclasses with ``value: str``.

    When adding a name class under ``generic/im_cable_system/im`` or ``cable``,
    inherit this base and
    satisfy the behavior defined here (implementation contract).

    Each name class should define ``value`` and validation in
    ``__post_init__``, and multiply-inherit this base. ``value`` is usually a
    plain field, but a subclass may instead expose it as a read-only
    ``@property`` derived from other fields when the identifier itself is
    composed from more than one part (see ``ImCableSystemName``, whose
    ``value`` joins a display-only ``base`` with an optional
    ``discriminator``). Either way ``value`` must stay non-blank, immutable
    once constructed, and hashable.
    Use ``@dataclass(frozen=True, eq=False)`` so dataclass-generated ``__eq__``
    does not override the base ``__eq__``.
    """

    value: str

    def get_value(self) -> str:
        """Return the identifier string."""
        return self.value

    def __eq__(self, other: object) -> bool:
        """Compare with same type or ``str`` by value."""
        if type(other) is type(self):
            return self.value == other.value
        if isinstance(other, str):
            return self.value == other
        return False

    def __hash__(self) -> int:
        """Return hash of ``value``."""
        return hash(self.value)

    def __str__(self) -> str:
        """Return the identifier string (``value``).

        Some subclasses (e.g. ``ImCableSystemName``) additionally expose a
        display-only accessor such as ``get_base()``; prefer that over
        ``str()``/``value`` for human-facing display.
        """
        return self.value


def validate_non_blank_after_strip(value: str, field_label: str) -> None:
    """Reject empty or whitespace-only values (production names).

    Args:
        value: Value to validate.
        field_label: Field name for error messages.

    Raises:
        ValueError: If empty or whitespace-only after strip.
    """
    if not isinstance(value, str) or value.strip() == "":
        raise ValueError(f"{field_label} must be a non-empty string: {value!r}")


def validate_non_empty_string(value: str, field_label: str) -> None:
    """Reject empty strings only (whitespace-only is allowed).

    Args:
        value: Value to validate.
        field_label: Field name for error messages.

    Raises:
        ValueError: If the string is empty.
    """
    if not isinstance(value, str) or len(value) == 0:
        raise ValueError(f"{field_label} must be a non-empty string: {value}")
