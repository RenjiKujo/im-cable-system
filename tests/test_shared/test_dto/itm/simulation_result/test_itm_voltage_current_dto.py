"""``ItmImVoltageCurrentDto`` / ``ItmCableVoltageCurrentDto`` テスト。

``__post_init__`` の dict キー検証および補助メソッド
（``get_secondary_branch_voltage`` / ``get_secondary_voltage`` /
``get_secondary_total_current`` /
``get_currents_for_array_layout``）の振る舞いを検証する。
"""

from __future__ import annotations

import numpy as np
import pytest

from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ArrayKey,
    ImCageMultiplicityType,
    ImSecondaryCageBranchType,
    PieCableConductorKey,
    PieCableGroundKey,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexCurrentDto,
    ArrayComplexVoltageDto,
)
from im_cable_system.engine.shared.dto.itm import (
    ItmCableVoltageCurrentDto,
    ItmImVoltageCurrentDto,
)
from tests.test_shared.test_dto.itm._itm_builders import (
    make_complex_current,
    make_complex_voltage,
)


def _v(arr_value: complex) -> ArrayComplexVoltageDto:
    return ArrayComplexVoltageDto(
        value=np.array([arr_value], dtype=np.complex128), unit="V"
    )


def _i(arr_value: complex) -> ArrayComplexCurrentDto:
    return ArrayComplexCurrentDto(
        value=np.array([arr_value], dtype=np.complex128), unit="A"
    )


class TestItmImVoltageCurrentDtoSingleCage:
    def _make(self) -> ItmImVoltageCurrentDto:
        single = ImSecondaryCageBranchType.SINGLE
        return ItmImVoltageCurrentDto(
            im_input_voltage=make_complex_voltage(),
            im_input_current=make_complex_current(),
            im_primary_voltage=make_complex_voltage(),
            im_primary_current=make_complex_current(),
            im_excitation_voltage=make_complex_voltage(),
            im_excitation_current=make_complex_current(),
            cage_multiplicity=ImCageMultiplicityType.SINGLE_CAGE,
            secondary_base_voltage={single: _v(10.0)},
            secondary_load_voltage={single: _v(20.0)},
            secondary_branch_current={single: _i(2.0)},
        )

    def test_construction_ok(self) -> None:
        dto = self._make()
        assert dto.cage_multiplicity == ImCageMultiplicityType.SINGLE_CAGE

    def test_branch_voltage_sum(self) -> None:
        dto = self._make()
        sec_v = dto.get_secondary_branch_voltage()
        assert sec_v[ImSecondaryCageBranchType.SINGLE].get_value()[0] == (
            pytest.approx(30.0 + 0j)
        )

    def test_secondary_voltage_returns_branch_voltage(self) -> None:
        dto = self._make()
        v = dto.get_secondary_voltage()
        assert v.get_value()[0] == pytest.approx(30.0 + 0j)

    def test_secondary_total_current_single(self) -> None:
        dto = self._make()
        total = dto.get_secondary_total_current()
        assert total.get_value()[0] == pytest.approx(2.0 + 0j)

    def test_currents_for_array_layout_single(self) -> None:
        dto = self._make()
        d = dto.get_currents_for_array_layout()
        assert ArrayKey.IM_INPUT_CURRENT in d
        assert ArrayKey.IM_PRIMARY_CURRENT in d
        assert ArrayKey.IM_EXCITATION_CURRENT in d
        assert ArrayKey.SINGLE_CAGE_IM_SECONDARY_CURRENT in d
        assert ArrayKey.DOUBLE_CAGE_IM_SECONDARY_INNER_CURRENT not in d

    def test_wrong_keys_for_single_cage_rejected(self) -> None:
        with pytest.raises(ValueError, match="secondary_base_voltage"):
            ItmImVoltageCurrentDto(
                im_input_voltage=make_complex_voltage(),
                im_input_current=make_complex_current(),
                im_primary_voltage=make_complex_voltage(),
                im_primary_current=make_complex_current(),
                im_excitation_voltage=make_complex_voltage(),
                im_excitation_current=make_complex_current(),
                cage_multiplicity=ImCageMultiplicityType.SINGLE_CAGE,
                secondary_base_voltage={
                    ImSecondaryCageBranchType.INNER: _v(10.0),
                    ImSecondaryCageBranchType.OUTER: _v(20.0),
                },
                secondary_load_voltage={
                    ImSecondaryCageBranchType.SINGLE: _v(20.0),
                },
                secondary_branch_current={
                    ImSecondaryCageBranchType.SINGLE: _i(2.0),
                },
            )


class TestItmImVoltageCurrentDtoDoubleCage:
    def _make_consistent(self) -> ItmImVoltageCurrentDto:
        inner = ImSecondaryCageBranchType.INNER
        outer = ImSecondaryCageBranchType.OUTER
        # 内・外で同一の base+load 電圧（合計 30）
        return ItmImVoltageCurrentDto(
            im_input_voltage=make_complex_voltage(),
            im_input_current=make_complex_current(),
            im_primary_voltage=make_complex_voltage(),
            im_primary_current=make_complex_current(),
            im_excitation_voltage=make_complex_voltage(),
            im_excitation_current=make_complex_current(),
            cage_multiplicity=ImCageMultiplicityType.DOUBLE_CAGE,
            secondary_base_voltage={
                inner: _v(10.0),
                outer: _v(15.0),
            },
            secondary_load_voltage={
                inner: _v(20.0),
                outer: _v(15.0),
            },
            secondary_branch_current={
                inner: _i(1.0),
                outer: _i(2.0),
            },
        )

    def test_construction_ok(self) -> None:
        self._make_consistent()

    def test_secondary_voltage_consistent_branches(self) -> None:
        # INNER: 10+20=30, OUTER: 15+15=30 で一致 → エラーなし
        dto = self._make_consistent()
        v = dto.get_secondary_voltage()
        assert v.get_value()[0] == pytest.approx(30.0 + 0j)

    def test_secondary_voltage_inconsistent_raises(self) -> None:
        inner = ImSecondaryCageBranchType.INNER
        outer = ImSecondaryCageBranchType.OUTER
        dto = ItmImVoltageCurrentDto(
            im_input_voltage=make_complex_voltage(),
            im_input_current=make_complex_current(),
            im_primary_voltage=make_complex_voltage(),
            im_primary_current=make_complex_current(),
            im_excitation_voltage=make_complex_voltage(),
            im_excitation_current=make_complex_current(),
            cage_multiplicity=ImCageMultiplicityType.DOUBLE_CAGE,
            secondary_base_voltage={inner: _v(10.0), outer: _v(15.0)},
            secondary_load_voltage={inner: _v(50.0), outer: _v(15.0)},
            secondary_branch_current={inner: _i(1.0), outer: _i(2.0)},
        )
        with pytest.raises(ValueError, match="一致しません"):
            dto.get_secondary_voltage()

    def test_secondary_total_current_sum(self) -> None:
        dto = self._make_consistent()
        total = dto.get_secondary_total_current()
        assert total.get_value()[0] == pytest.approx(3.0 + 0j)

    def test_currents_for_array_layout_double(self) -> None:
        dto = self._make_consistent()
        d = dto.get_currents_for_array_layout()
        assert ArrayKey.DOUBLE_CAGE_IM_SECONDARY_INNER_CURRENT in d
        assert ArrayKey.DOUBLE_CAGE_IM_SECONDARY_OUTER_CURRENT in d
        assert ArrayKey.SINGLE_CAGE_IM_SECONDARY_CURRENT not in d


class TestItmCableVoltageCurrentDto:
    def _make(self) -> ItmCableVoltageCurrentDto:
        return ItmCableVoltageCurrentDto(
            input_line_voltage=make_complex_voltage(),
            input_line_current=make_complex_current(),
            input_phase_voltage=make_complex_voltage(),
            input_phase_current=make_complex_current(),
            conductor_voltage={
                PieCableConductorKey.SINGLE: make_complex_voltage(),
            },
            conductor_current={
                PieCableConductorKey.SINGLE: make_complex_current(),
            },
            ground_voltage={
                PieCableGroundKey.UPSTREAM: make_complex_voltage(),
                PieCableGroundKey.DOWNSTREAM: make_complex_voltage(),
            },
            ground_current={
                PieCableGroundKey.UPSTREAM: make_complex_current(),
                PieCableGroundKey.DOWNSTREAM: make_complex_current(),
            },
            end_point_phase_voltage=make_complex_voltage(),
            end_point_phase_current=make_complex_current(),
        )

    def test_construction_ok(self) -> None:
        self._make()

    def test_currents_for_array_layout_keys(self) -> None:
        dto = self._make()
        d = dto.get_currents_for_array_layout()
        for key in (
            ArrayKey.INPUT_LINE_CURRENT,
            ArrayKey.INPUT_PHASE_CURRENT,
            ArrayKey.END_POINT_PHASE_CURRENT,
            ArrayKey.CONDUCTOR_CURRENT_PIE_SINGLE,
            ArrayKey.GROUND_CURRENT_PIE_UPSTREAM,
            ArrayKey.GROUND_CURRENT_PIE_DOWNSTREAM,
        ):
            assert key in d

    def test_missing_ground_key_rejected(self) -> None:
        with pytest.raises(ValueError, match="ground_voltage"):
            ItmCableVoltageCurrentDto(
                input_line_voltage=make_complex_voltage(),
                input_line_current=make_complex_current(),
                input_phase_voltage=make_complex_voltage(),
                input_phase_current=make_complex_current(),
                conductor_voltage={
                    PieCableConductorKey.SINGLE: make_complex_voltage(),
                },
                conductor_current={
                    PieCableConductorKey.SINGLE: make_complex_current(),
                },
                ground_voltage={
                    PieCableGroundKey.UPSTREAM: make_complex_voltage(),
                },
                ground_current={
                    PieCableGroundKey.UPSTREAM: make_complex_current(),
                    PieCableGroundKey.DOWNSTREAM: make_complex_current(),
                },
                end_point_phase_voltage=make_complex_voltage(),
                end_point_phase_current=make_complex_current(),
            )

    def test_extra_conductor_key_rejected(self) -> None:
        # conductor 系には PieCableGroundKey は載せられない
        with pytest.raises(ValueError, match="conductor_voltage"):
            ItmCableVoltageCurrentDto(
                input_line_voltage=make_complex_voltage(),
                input_line_current=make_complex_current(),
                input_phase_voltage=make_complex_voltage(),
                input_phase_current=make_complex_current(),
                conductor_voltage={},
                conductor_current={
                    PieCableConductorKey.SINGLE: make_complex_current(),
                },
                ground_voltage={
                    PieCableGroundKey.UPSTREAM: make_complex_voltage(),
                    PieCableGroundKey.DOWNSTREAM: make_complex_voltage(),
                },
                ground_current={
                    PieCableGroundKey.UPSTREAM: make_complex_current(),
                    PieCableGroundKey.DOWNSTREAM: make_complex_current(),
                },
                end_point_phase_voltage=make_complex_voltage(),
                end_point_phase_current=make_complex_current(),
            )
