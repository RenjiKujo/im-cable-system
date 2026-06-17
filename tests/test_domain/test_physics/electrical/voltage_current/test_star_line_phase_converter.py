"""``physics.electrical.voltage_current.star_line_phase_converter`` の単体テスト。

スター結線の線間↔相変換 4 関数を検証する:
    - line_to_phase_voltage_star: V_phase = V_line / √3 · e^(-jπ/6)
    - phase_to_line_voltage_star: V_line = √3 · V_phase · e^(jπ/6)
    - line_to_phase_current_star: I_phase = I_line（スター結線では等しい）
    - phase_to_line_current_star: I_line = I_phase（同上）
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from im_cable_system.engine.domain.physics.electrical import (
    line_to_phase_current_star,
    line_to_phase_voltage_star,
    line_to_phase_voltage_star_balanced,
    phase_to_line_current_star,
    phase_to_line_voltage_star,
    phase_to_line_voltage_star_balanced,
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
_PHASE_30 = np.exp(1j * np.pi / 6.0)


class TestVoltageRoundTripStar:
    """``line_to_phase`` と ``phase_to_line`` の往復一致。"""

    def test_round_trip_returns_original_voltage(self) -> None:
        original = ArrayComplexVoltageDto(
            value=np.array([100.0 + 50.0j, 460.0 + 0j]), unit="V"
        )
        phase = line_to_phase_voltage_star(
            eps=TEST_EPS, max_mag=TEST_MAX_MAG, line_voltage_dto=original
        )
        recovered = phase_to_line_voltage_star(
            eps=TEST_EPS, max_mag=TEST_MAX_MAG, phase_voltage_dto=phase
        )
        np.testing.assert_allclose(recovered.value, original.value, atol=1e-9)


class TestPhaseToLineVoltageStar:
    """``V_line = √3 · V_phase · e^(jπ/6)``。"""

    def test_magnitude_multiplied_by_sqrt_three(self) -> None:
        v_phase = ArrayComplexVoltageDto(value=np.array([100.0 + 0j]), unit="V")
        v_line = phase_to_line_voltage_star(
            eps=TEST_EPS, max_mag=TEST_MAX_MAG, phase_voltage_dto=v_phase
        )
        np.testing.assert_allclose(np.abs(v_line.value), [_SQRT_3 * 100.0])

    def test_phase_advanced_by_30_degrees(self) -> None:
        v_phase = ArrayComplexVoltageDto(value=np.array([1.0 + 0j]), unit="V")
        v_line = phase_to_line_voltage_star(
            eps=TEST_EPS, max_mag=TEST_MAX_MAG, phase_voltage_dto=v_phase
        )
        np.testing.assert_allclose(v_line.value, [_SQRT_3 * _PHASE_30])


class TestLineToPhaseVoltageStar:
    """``V_phase = V_line / √3 · e^(-jπ/6)``。"""

    def test_magnitude_divided_by_sqrt_three(self) -> None:
        v_line = ArrayComplexVoltageDto(
            value=np.array([_SQRT_3 * 100.0 + 0j]), unit="V"
        )
        v_phase = line_to_phase_voltage_star(
            eps=TEST_EPS, max_mag=TEST_MAX_MAG, line_voltage_dto=v_line
        )
        np.testing.assert_allclose(np.abs(v_phase.value), [100.0])


class TestLineToPhaseVoltageStarBalanced:
    """balanced 規約: ``V_phase = V_line / √3``（30° 回転を付与しない）。"""

    def test_magnitude_divided_by_sqrt_three(self) -> None:
        v_line = ArrayComplexVoltageDto(
            value=np.array([_SQRT_3 * 100.0 + 0j]), unit="V"
        )
        v_phase = line_to_phase_voltage_star_balanced(
            eps=TEST_EPS, max_mag=TEST_MAX_MAG, line_voltage_dto=v_line
        )
        np.testing.assert_allclose(np.abs(v_phase.value), [100.0])

    def test_phase_is_preserved(self) -> None:
        # 任意位相の線間電圧でも相電圧の位相は変わらない（大きさのみ 1/√3）。
        v_line = ArrayComplexVoltageDto(
            value=np.array([200.0 * _PHASE_30, 100.0 + 50.0j]), unit="V"
        )
        v_phase = line_to_phase_voltage_star_balanced(
            eps=TEST_EPS, max_mag=TEST_MAX_MAG, line_voltage_dto=v_line
        )
        np.testing.assert_allclose(
            v_phase.value, v_line.value / _SQRT_3, atol=1e-9
        )

    def test_records_voltage_extreme_small_event(self) -> None:
        v = ArrayComplexVoltageDto(value=np.array([0.0 + 0j]), unit="V")
        with numerical_stability_scope() as acc:
            line_to_phase_voltage_star_balanced(
                eps=TEST_EPS, max_mag=TEST_MAX_MAG, line_voltage_dto=v
            )
        assert_event_counts(acc, (event_codes.VOLTAGE_EXTREME_SMALL, 1))


class TestPhaseToLineVoltageStarBalanced:
    """balanced 規約: ``V_line = √3 · V_phase``（30° 回転を付与しない）。"""

    def test_magnitude_multiplied_by_sqrt_three(self) -> None:
        v_phase = ArrayComplexVoltageDto(value=np.array([100.0 + 0j]), unit="V")
        v_line = phase_to_line_voltage_star_balanced(
            eps=TEST_EPS, max_mag=TEST_MAX_MAG, phase_voltage_dto=v_phase
        )
        np.testing.assert_allclose(np.abs(v_line.value), [_SQRT_3 * 100.0])

    def test_phase_is_preserved(self) -> None:
        v_phase = ArrayComplexVoltageDto(
            value=np.array([100.0 * _PHASE_30, 60.0 + 80.0j]), unit="V"
        )
        v_line = phase_to_line_voltage_star_balanced(
            eps=TEST_EPS, max_mag=TEST_MAX_MAG, phase_voltage_dto=v_phase
        )
        np.testing.assert_allclose(
            v_line.value, v_phase.value * _SQRT_3, atol=1e-9
        )

    def test_round_trip_returns_original_voltage(self) -> None:
        original = ArrayComplexVoltageDto(
            value=np.array([100.0 + 50.0j, 460.0 + 0j]), unit="V"
        )
        phase = line_to_phase_voltage_star_balanced(
            eps=TEST_EPS, max_mag=TEST_MAX_MAG, line_voltage_dto=original
        )
        recovered = phase_to_line_voltage_star_balanced(
            eps=TEST_EPS, max_mag=TEST_MAX_MAG, phase_voltage_dto=phase
        )
        np.testing.assert_allclose(recovered.value, original.value, atol=1e-9)


class TestCurrentIdentityStar:
    """スター結線では線電流 = 相電流。"""

    def test_line_to_phase_returns_same_value(self) -> None:
        i_line = ArrayComplexCurrentDto(value=np.array([2.0 + 1.0j]), unit="A")
        i_phase = line_to_phase_current_star(
            eps=TEST_EPS, max_mag=TEST_MAX_MAG, line_current_dto=i_line
        )
        np.testing.assert_allclose(i_phase.value, i_line.value)

    def test_phase_to_line_returns_same_value(self) -> None:
        i_phase = ArrayComplexCurrentDto(value=np.array([2.0 + 1.0j]), unit="A")
        i_line = phase_to_line_current_star(
            eps=TEST_EPS, max_mag=TEST_MAX_MAG, phase_current_dto=i_phase
        )
        np.testing.assert_allclose(i_line.value, i_phase.value)


class TestNumericalStabilityVoltageEvents:
    """電圧の極小・極大入力で事件が記録されること。"""

    def test_records_voltage_extreme_small_event(self) -> None:
        v = ArrayComplexVoltageDto(value=np.array([0.0 + 0j]), unit="V")
        with numerical_stability_scope() as acc:
            line_to_phase_voltage_star(
                eps=TEST_EPS, max_mag=TEST_MAX_MAG, line_voltage_dto=v
            )
        assert_event_counts(acc, (event_codes.VOLTAGE_EXTREME_SMALL, 1))

    def test_records_voltage_extreme_large_event(self) -> None:
        # DTO は NaN/inf 禁止のため、|V| >= 1/eps = 1e12 となる有限値で発火させる
        v = ArrayComplexVoltageDto(value=np.array([2e12 + 0j]), unit="V")
        with numerical_stability_scope() as acc:
            phase_to_line_voltage_star(
                eps=TEST_EPS, max_mag=TEST_MAX_MAG, phase_voltage_dto=v
            )
        assert_event_counts(acc, (event_codes.VOLTAGE_EXTREME_LARGE, 1))

    def test_no_event_with_normal_voltage(self) -> None:
        v = ArrayComplexVoltageDto(value=np.array([100.0 + 0j]), unit="V")
        with numerical_stability_scope() as acc:
            line_to_phase_voltage_star(
                eps=TEST_EPS, max_mag=TEST_MAX_MAG, line_voltage_dto=v
            )
        assert_no_events(acc)


class TestNumericalStabilityCurrentEvents:
    """電流の極小・極大入力で事件が記録されること。"""

    @pytest.mark.parametrize(
        "value, expected_code",
        [
            (np.array([0.0 + 0j]), event_codes.CURRENT_EXTREME_SMALL),
            (np.array([2e12 + 0j]), event_codes.CURRENT_EXTREME_LARGE),
        ],
    )
    def test_records_current_extreme_event(
        self, value: np.ndarray, expected_code: str
    ) -> None:
        i = ArrayComplexCurrentDto(value=value, unit="A")
        with numerical_stability_scope() as acc:
            phase_to_line_current_star(
                eps=TEST_EPS, max_mag=TEST_MAX_MAG, phase_current_dto=i
            )
        assert_event_counts(acc, (expected_code, 1))
