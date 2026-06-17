from __future__ import annotations

from enum import Enum, IntEnum


class ImCircuitType(Enum):
    """Induction motor circuit topology.

    Attributes:
        value (str): Circuit type (T, L).
    """

    T = "T"
    L = "L"


class ImConnectionType(Enum):
    """Induction motor winding connection.

    Attributes:
        value (str): Connection type (DELTA, STAR).
    """

    DELTA = "DELTA"
    STAR = "STAR"


class ImPoles(IntEnum):
    """Induction motor pole count (even values from 2 through 12)."""

    P2 = 2
    P4 = 4
    P6 = 6
    P8 = 8
    P10 = 10
    P12 = 12
