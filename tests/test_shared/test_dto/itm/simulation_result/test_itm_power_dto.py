"""``ItmImPowerDto`` / ``ItmCablePowerDto`` の dict キー検証テスト。"""

from __future__ import annotations

import pytest

from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ImCageMultiplicityType,
    ImSecondaryCageBranchType,
    PieCableConductorKey,
    PieCableGroundKey,
)
from im_cable_system.engine.shared.dto.itm import (
    ItmCablePowerDto,
    ItmImPowerDto,
)
from tests.test_shared.test_dto.itm._itm_builders import make_complex_power


class TestItmImPowerDto:
    def test_single_cage_ok(self) -> None:
        single = ImSecondaryCageBranchType.SINGLE
        ItmImPowerDto(
            input_power=make_complex_power(),
            primary_loss_power=make_complex_power(),
            excitation_loss_power=make_complex_power(),
            cage_multiplicity=ImCageMultiplicityType.SINGLE_CAGE,
            secondary_base_loss_power={single: make_complex_power()},
            secondary_load_power={single: make_complex_power()},
            secondary_branch_total_power={single: make_complex_power()},
            secondary_total_power=make_complex_power(),
            output_power=make_complex_power(),
            total_loss_power=make_complex_power(),
            copper_loss_power=make_complex_power(),
            iron_loss_power=make_complex_power(),
        )

    def test_double_cage_ok(self) -> None:
        inner = ImSecondaryCageBranchType.INNER
        outer = ImSecondaryCageBranchType.OUTER
        ItmImPowerDto(
            input_power=make_complex_power(),
            primary_loss_power=make_complex_power(),
            excitation_loss_power=make_complex_power(),
            cage_multiplicity=ImCageMultiplicityType.DOUBLE_CAGE,
            secondary_base_loss_power={
                inner: make_complex_power(),
                outer: make_complex_power(),
            },
            secondary_load_power={
                inner: make_complex_power(),
                outer: make_complex_power(),
            },
            secondary_branch_total_power={
                inner: make_complex_power(),
                outer: make_complex_power(),
            },
            secondary_total_power=make_complex_power(),
            output_power=make_complex_power(),
            total_loss_power=make_complex_power(),
            copper_loss_power=make_complex_power(),
            iron_loss_power=make_complex_power(),
        )

    def test_single_cage_with_double_keys_rejected(self) -> None:
        inner = ImSecondaryCageBranchType.INNER
        outer = ImSecondaryCageBranchType.OUTER
        single = ImSecondaryCageBranchType.SINGLE
        with pytest.raises(ValueError, match="secondary_base_loss_power"):
            ItmImPowerDto(
                input_power=make_complex_power(),
                primary_loss_power=make_complex_power(),
                excitation_loss_power=make_complex_power(),
                cage_multiplicity=ImCageMultiplicityType.SINGLE_CAGE,
                secondary_base_loss_power={
                    inner: make_complex_power(),
                    outer: make_complex_power(),
                },
                secondary_load_power={single: make_complex_power()},
                secondary_branch_total_power={single: make_complex_power()},
                secondary_total_power=make_complex_power(),
                output_power=make_complex_power(),
                total_loss_power=make_complex_power(),
                copper_loss_power=make_complex_power(),
                iron_loss_power=make_complex_power(),
            )


class TestItmCablePowerDto:
    def test_valid_pi_keys_ok(self) -> None:
        ItmCablePowerDto(
            system_total_input_power=make_complex_power(),
            input_phase_power=make_complex_power(),
            conductor_loss_power={
                PieCableConductorKey.SINGLE: make_complex_power(),
            },
            ground_loss_power={
                PieCableGroundKey.UPSTREAM: make_complex_power(),
                PieCableGroundKey.DOWNSTREAM: make_complex_power(),
            },
            end_point_phase_power=make_complex_power(),
            total_loss_power=make_complex_power(),
        )

    def test_missing_ground_key_rejected(self) -> None:
        with pytest.raises(ValueError, match="ground_loss_power"):
            ItmCablePowerDto(
                system_total_input_power=make_complex_power(),
                input_phase_power=make_complex_power(),
                conductor_loss_power={
                    PieCableConductorKey.SINGLE: make_complex_power(),
                },
                ground_loss_power={
                    PieCableGroundKey.UPSTREAM: make_complex_power(),
                },
                end_point_phase_power=make_complex_power(),
                total_loss_power=make_complex_power(),
            )

    def test_extra_conductor_key_rejected(self) -> None:
        with pytest.raises(ValueError, match="conductor_loss_power"):
            ItmCablePowerDto(
                system_total_input_power=make_complex_power(),
                input_phase_power=make_complex_power(),
                conductor_loss_power={},
                ground_loss_power={
                    PieCableGroundKey.UPSTREAM: make_complex_power(),
                    PieCableGroundKey.DOWNSTREAM: make_complex_power(),
                },
                end_point_phase_power=make_complex_power(),
                total_loss_power=make_complex_power(),
            )
