"""``physics.electrical.voltage_current.delta_line_phase_converter`` の単体テスト。

デルタ結線の線間↔相変換 4 関数を検証する:
    - line_to_phase_voltage_delta: V_phase = V_line（等しい）
    - phase_to_line_voltage_delta: V_line = V_phase（等しい）
    - line_to_phase_current_delta: I_phase = I_line / √3 · e^(jπ/6)
    - phase_to_line_current_delta: I_line = √3 · I_phase · e^(-jπ/6)
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from im_cable_system.engine.domain.physics.electrical import (
    line_to_phase_current_delta,
    line_to_phase_current_delta_balanced,
    line_to_phase_voltage_delta,
    phase_to_line_current_delta,
    phase_to_line_current_delta_balanced,
    phase_to_line_voltage_delta,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexCurrentDto,
    ArrayComplexVoltageDto,
)
from im_cable_system.engine.shared.numerical_stability import (
    event_codes,
    numerical_stability_scope,
)
from tests.test_domain._domain_helpers import (
    TEST_EPS,
    TEST_MAX_MAG,
    assert_event_counts,
    assert_no_events,
)

_SQRT_3 = math.sqrt(3.0)


class TestVoltageIdentityDelta:
    """デルタ結線では線間電圧 = 相電圧。"""

    def test_line_to_phase_returns_same_value(self) -> None:
        v_line = ArrayComplexVoltageDto(
            value=np.array([100.0 + 50.0j]), unit="V"
        )
        v_phase = line_to_phase_voltage_delta(
            eps=TEST_EPS, max_mag=TEST_MAX_MAG, line_voltage_dto=v_line
        )
        np.testing.assert_allclose(v_phase.value, v_line.value)

    def test_phase_to_line_returns_same_value(self) -> None:
        v_phase = ArrayComplexVoltageDto(
            value=np.array([100.0 + 50.0j]), unit="V"
        )
        v_line = phase_to_line_voltage_delta(
            eps=TEST_EPS, max_mag=TEST_MAX_MAG, phase_voltage_dto=v_phase
        )
        np.testing.assert_allclose(v_line.value, v_phase.value)


class TestCurrentRoundTripDelta:
    """``line_to_phase`` と ``phase_to_line`` の往復一致。"""

    def test_round_trip_returns_original_current(self) -> None:
        original = ArrayComplexCurrentDto(
            value=np.array([10.0 + 5.0j, 3.0 + 0j]), unit="A"
        )
        phase = line_to_phase_current_delta(
            eps=TEST_EPS, max_mag=TEST_MAX_MAG, line_current_dto=original
        )
        recovered = phase_to_line_current_delta(
            eps=TEST_EPS, max_mag=TEST_MAX_MAG, phase_current_dto=phase
        )
        np.testing.assert_allclose(recovered.value, original.value, atol=1e-9)


class TestPhaseToLineCurrentDelta:
    """``I_line = √3 · I_phase · e^(-jπ/6)``。"""

    def test_magnitude_multiplied_by_sqrt_three(self) -> None:
        i_phase = ArrayComplexCurrentDto(value=np.array([10.0 + 0j]), unit="A")
        i_line = phase_to_line_current_delta(
            eps=TEST_EPS, max_mag=TEST_MAX_MAG, phase_current_dto=i_phase
        )
        np.testing.assert_allclose(np.abs(i_line.value), [_SQRT_3 * 10.0])


class TestLineToPhaseCurrentDelta:
    """``I_phase = I_line / √3 · e^(jπ/6)``。"""

    def test_magnitude_divided_by_sqrt_three(self) -> None:
        i_line = ArrayComplexCurrentDto(
            value=np.array([_SQRT_3 * 10.0 + 0j]), unit="A"
        )
        i_phase = line_to_phase_current_delta(
            eps=TEST_EPS, max_mag=TEST_MAX_MAG, line_current_dto=i_line
        )
        np.testing.assert_allclose(np.abs(i_phase.value), [10.0])


class TestLineToPhaseCurrentDeltaBalanced:
    """balanced 規約: ``I_phase = I_line / √3``（30° 回転を付与しない）。"""

    def test_magnitude_divided_by_sqrt_three(self) -> None:
        i_line = ArrayComplexCurrentDto(
            value=np.array([_SQRT_3 * 10.0 + 0j]), unit="A"
        )
        i_phase = line_to_phase_current_delta_balanced(
            eps=TEST_EPS, max_mag=TEST_MAX_MAG, line_current_dto=i_line
        )
        np.testing.assert_allclose(np.abs(i_phase.value), [10.0])

    def test_phase_is_preserved(self) -> None:
        # 任意位相の線電流でも相電流の位相は変わらない（大きさのみ 1/√3）。
        i_line = ArrayComplexCurrentDto(
            value=np.array([10.0 + 0j, 6.0 + 8.0j]), unit="A"
        )
        i_phase = line_to_phase_current_delta_balanced(
            eps=TEST_EPS, max_mag=TEST_MAX_MAG, line_current_dto=i_line
        )
        np.testing.assert_allclose(
            i_phase.value, i_line.value / _SQRT_3, atol=1e-9
        )

    def test_records_current_extreme_small_event(self) -> None:
        i = ArrayComplexCurrentDto(value=np.array([0.0 + 0j]), unit="A")
        with numerical_stability_scope() as acc:
            line_to_phase_current_delta_balanced(
                eps=TEST_EPS, max_mag=TEST_MAX_MAG, line_current_dto=i
            )
        assert_event_counts(acc, (event_codes.CURRENT_EXTREME_SMALL, 1))


class TestPhaseToLineCurrentDeltaBalanced:
    """balanced 規約: ``I_line = √3 · I_phase``（30° 回転を付与しない）。"""

    def test_magnitude_multiplied_by_sqrt_three(self) -> None:
        i_phase = ArrayComplexCurrentDto(value=np.array([10.0 + 0j]), unit="A")
        i_line = phase_to_line_current_delta_balanced(
            eps=TEST_EPS, max_mag=TEST_MAX_MAG, phase_current_dto=i_phase
        )
        np.testing.assert_allclose(np.abs(i_line.value), [_SQRT_3 * 10.0])

    def test_round_trip_returns_original_current(self) -> None:
        original = ArrayComplexCurrentDto(
            value=np.array([10.0 + 5.0j, 3.0 + 0j]), unit="A"
        )
        phase = line_to_phase_current_delta_balanced(
            eps=TEST_EPS, max_mag=TEST_MAX_MAG, line_current_dto=original
        )
        recovered = phase_to_line_current_delta_balanced(
            eps=TEST_EPS, max_mag=TEST_MAX_MAG, phase_current_dto=phase
        )
        np.testing.assert_allclose(recovered.value, original.value, atol=1e-9)


class TestNumericalStabilityEvents:
    """極小・極大入力でイベント記録されること。"""

    @pytest.mark.parametrize(
        "value, expected_code",
        [
            (np.array([0.0 + 0j]), event_codes.VOLTAGE_EXTREME_SMALL),
            (np.array([2e12 + 0j]), event_codes.VOLTAGE_EXTREME_LARGE),
        ],
    )
    def test_voltage_records_event(
        self, value: np.ndarray, expected_code: str
    ) -> None:
        v = ArrayComplexVoltageDto(value=value, unit="V")
        with numerical_stability_scope() as acc:
            line_to_phase_voltage_delta(
                eps=TEST_EPS, max_mag=TEST_MAX_MAG, line_voltage_dto=v
            )
        assert_event_counts(acc, (expected_code, 1))

    @pytest.mark.parametrize(
        "value, expected_code",
        [
            (np.array([0.0 + 0j]), event_codes.CURRENT_EXTREME_SMALL),
            (np.array([2e12 + 0j]), event_codes.CURRENT_EXTREME_LARGE),
        ],
    )
    def test_current_records_event(
        self, value: np.ndarray, expected_code: str
    ) -> None:
        i = ArrayComplexCurrentDto(value=value, unit="A")
        with numerical_stability_scope() as acc:
            phase_to_line_current_delta(
                eps=TEST_EPS, max_mag=TEST_MAX_MAG, phase_current_dto=i
            )
        assert_event_counts(acc, (expected_code, 1))

    def test_no_event_with_normal_input(self) -> None:
        i = ArrayComplexCurrentDto(value=np.array([5.0 + 0j]), unit="A")
        with numerical_stability_scope() as acc:
            line_to_phase_current_delta(
                eps=TEST_EPS, max_mag=TEST_MAX_MAG, line_current_dto=i
            )
        assert_no_events(acc)
