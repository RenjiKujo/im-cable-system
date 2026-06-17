"""``ItmCableImmittanceDto`` の dict キー検証テスト。"""

from __future__ import annotations

import pytest

from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    CableConductorModelDto,
    ConductorModelType,
    PieCableConductorKey,
    PieCableGroundKey,
)
from im_cable_system.engine.shared.dto.itm import ItmCableImmittanceDto
from tests.test_shared.test_dto.itm._itm_builders import (
    make_complex_admittance,
    make_complex_impedance,
)


def _make_basic_conductor() -> CableConductorModelDto:
    return CableConductorModelDto(name=ConductorModelType.BASIC)


class TestItmCableImmittanceDto:
    def test_valid_pi_keys_ok(self) -> None:
        ItmCableImmittanceDto(
            conductor_model=_make_basic_conductor(),
            conductor_impedance={
                PieCableConductorKey.SINGLE: make_complex_impedance(),
            },
            conductor_admittance={
                PieCableConductorKey.SINGLE: make_complex_admittance(),
            },
            ground_impedance={
                PieCableGroundKey.UPSTREAM: make_complex_impedance(),
                PieCableGroundKey.DOWNSTREAM: make_complex_impedance(),
            },
            ground_admittance={
                PieCableGroundKey.UPSTREAM: make_complex_admittance(),
                PieCableGroundKey.DOWNSTREAM: make_complex_admittance(),
            },
            is_ground_insulated=False,
            is_ground_shorted=False,
            is_conductor_ideal=False,
        )

    def test_missing_ground_downstream_rejected(self) -> None:
        with pytest.raises(ValueError, match="ground_impedance"):
            ItmCableImmittanceDto(
                conductor_model=_make_basic_conductor(),
                conductor_impedance={
                    PieCableConductorKey.SINGLE: make_complex_impedance(),
                },
                conductor_admittance={
                    PieCableConductorKey.SINGLE: make_complex_admittance(),
                },
                ground_impedance={
                    PieCableGroundKey.UPSTREAM: make_complex_impedance(),
                },
                ground_admittance={
                    PieCableGroundKey.UPSTREAM: make_complex_admittance(),
                    PieCableGroundKey.DOWNSTREAM: make_complex_admittance(),
                },
                is_ground_insulated=False,
                is_ground_shorted=False,
                is_conductor_ideal=False,
            )

    def test_extra_conductor_admittance_rejected(self) -> None:
        with pytest.raises(ValueError, match="conductor_admittance"):
            ItmCableImmittanceDto(
                conductor_model=_make_basic_conductor(),
                conductor_impedance={
                    PieCableConductorKey.SINGLE: make_complex_impedance(),
                },
                conductor_admittance={},
                ground_impedance={
                    PieCableGroundKey.UPSTREAM: make_complex_impedance(),
                    PieCableGroundKey.DOWNSTREAM: make_complex_impedance(),
                },
                ground_admittance={
                    PieCableGroundKey.UPSTREAM: make_complex_admittance(),
                    PieCableGroundKey.DOWNSTREAM: make_complex_admittance(),
                },
                is_ground_insulated=False,
                is_ground_shorted=False,
                is_conductor_ideal=False,
            )
