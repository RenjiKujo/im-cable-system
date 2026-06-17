"""``physics.electrical.voltage_current.connection_type_converter`` の単体テスト。

デルタ⇔スターの **相** 電圧・相電流の等価変換 4 関数を検証する:
    - V_star = V_delta / √3 · e^(-jπ/6)
    - I_star = I_delta · √3 · e^(-jπ/6)
    - V_delta = √3 · V_star · e^(+jπ/6)
    - I_delta = V_star / √3 · e^(+jπ/6)
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from im_cable_system.engine.domain.physics.electrical import (
    convert_current_delta_to_star,
    convert_current_delta_to_star_balanced,
    convert_current_star_to_delta,
    convert_current_star_to_delta_balanced,
    convert_voltage_delta_to_star,
    convert_voltage_delta_to_star_balanced,
    convert_voltage_star_to_delta,
    convert_voltage_star_to_delta_balanced,
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


class TestVoltageRoundTrip:
    """delta↔star の電圧変換が往復で一致すること。"""

    def test_delta_to_star_to_delta_returns_original(self) -> None:
        original = ArrayComplexVoltageDto(
            value=np.array([100.0 + 50.0j, 200.0 + 0j]), unit="V"
        )
        star = convert_voltage_delta_to_star(
            eps=TEST_EPS, max_mag=TEST_MAX_MAG, voltage_dto=original
        )
        recovered = convert_voltage_star_to_delta(
            eps=TEST_EPS, max_mag=TEST_MAX_MAG, voltage_dto=star
        )
        np.testing.assert_allclose(recovered.value, original.value, atol=1e-9)


class TestCurrentRoundTrip:
    """delta↔star の電流変換が往復で一致すること。"""

    def test_delta_to_star_to_delta_returns_original(self) -> None:
        original = ArrayComplexCurrentDto(
            value=np.array([10.0 + 5.0j, 3.0 + 0j]), unit="A"
        )
        star = convert_current_delta_to_star(
            eps=TEST_EPS, max_mag=TEST_MAX_MAG, current_dto=original
        )
        recovered = convert_current_star_to_delta(
            eps=TEST_EPS, max_mag=TEST_MAX_MAG, current_dto=star
        )
        np.testing.assert_allclose(recovered.value, original.value, atol=1e-9)


class TestMagnitudeRelations:
    """大きさの比が ``√3`` で結ばれること。"""

    def test_voltage_delta_to_star_divides_magnitude_by_sqrt3(self) -> None:
        v_delta = ArrayComplexVoltageDto(value=np.array([100.0 + 0j]), unit="V")
        v_star = convert_voltage_delta_to_star(
            eps=TEST_EPS, max_mag=TEST_MAX_MAG, voltage_dto=v_delta
        )
        np.testing.assert_allclose(np.abs(v_star.value), [100.0 / _SQRT_3])

    def test_voltage_star_to_delta_multiplies_magnitude_by_sqrt3(self) -> None:
        v_star = ArrayComplexVoltageDto(value=np.array([100.0 + 0j]), unit="V")
        v_delta = convert_voltage_star_to_delta(
            eps=TEST_EPS, max_mag=TEST_MAX_MAG, voltage_dto=v_star
        )
        np.testing.assert_allclose(np.abs(v_delta.value), [100.0 * _SQRT_3])

    def test_current_delta_to_star_multiplies_magnitude_by_sqrt3(self) -> None:
        i_delta = ArrayComplexCurrentDto(value=np.array([10.0 + 0j]), unit="A")
        i_star = convert_current_delta_to_star(
            eps=TEST_EPS, max_mag=TEST_MAX_MAG, current_dto=i_delta
        )
        np.testing.assert_allclose(np.abs(i_star.value), [10.0 * _SQRT_3])

    def test_current_star_to_delta_divides_magnitude_by_sqrt3(self) -> None:
        i_star = ArrayComplexCurrentDto(value=np.array([10.0 + 0j]), unit="A")
        i_delta = convert_current_star_to_delta(
            eps=TEST_EPS, max_mag=TEST_MAX_MAG, current_dto=i_star
        )
        np.testing.assert_allclose(np.abs(i_delta.value), [10.0 / _SQRT_3])


class TestStarToDeltaBalanced:
    """balanced 規約: 大きさのみ √3 倍／1/√3 倍し、30° 回転を付与しない。"""

    def test_voltage_scales_magnitude_and_preserves_phase(self) -> None:
        # 任意位相のスター相電圧でも、デルタ相電圧は同位相で大きさ √3 倍。
        v_star = ArrayComplexVoltageDto(
            value=np.array([100.0 + 0j, 60.0 + 80.0j]), unit="V"
        )
        v_delta = convert_voltage_star_to_delta_balanced(
            eps=TEST_EPS, max_mag=TEST_MAX_MAG, voltage_dto=v_star
        )
        np.testing.assert_allclose(
            v_delta.value, v_star.value * _SQRT_3, atol=1e-9
        )

    def test_current_scales_magnitude_and_preserves_phase(self) -> None:
        # 任意位相のスター相電流でも、デルタ相電流は同位相で大きさ 1/√3 倍。
        i_star = ArrayComplexCurrentDto(
            value=np.array([10.0 + 0j, 6.0 + 8.0j]), unit="A"
        )
        i_delta = convert_current_star_to_delta_balanced(
            eps=TEST_EPS, max_mag=TEST_MAX_MAG, current_dto=i_star
        )
        np.testing.assert_allclose(
            i_delta.value, i_star.value / _SQRT_3, atol=1e-9
        )

    def test_voltage_round_trip_balanced(self) -> None:
        # star→delta→star（balanced）で元に戻る。
        original = ArrayComplexVoltageDto(
            value=np.array([100.0 + 50.0j, 200.0 + 0j]), unit="V"
        )
        delta = convert_voltage_star_to_delta_balanced(
            eps=TEST_EPS, max_mag=TEST_MAX_MAG, voltage_dto=original
        )
        recovered = convert_voltage_delta_to_star_balanced(
            eps=TEST_EPS, max_mag=TEST_MAX_MAG, voltage_dto=delta
        )
        np.testing.assert_allclose(recovered.value, original.value, atol=1e-9)

    def test_current_round_trip_balanced(self) -> None:
        # star→delta→star（balanced）で元に戻る。
        original = ArrayComplexCurrentDto(
            value=np.array([10.0 + 5.0j, 3.0 + 0j]), unit="A"
        )
        delta = convert_current_star_to_delta_balanced(
            eps=TEST_EPS, max_mag=TEST_MAX_MAG, current_dto=original
        )
        recovered = convert_current_delta_to_star_balanced(
            eps=TEST_EPS, max_mag=TEST_MAX_MAG, current_dto=delta
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
        with numerical_stability_scope() as acc:
            convert_voltage_delta_to_star(
                eps=TEST_EPS,
                max_mag=TEST_MAX_MAG,
                voltage_dto=ArrayComplexVoltageDto(value=value, unit="V"),
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
        with numerical_stability_scope() as acc:
            convert_current_star_to_delta(
                eps=TEST_EPS,
                max_mag=TEST_MAX_MAG,
                current_dto=ArrayComplexCurrentDto(value=value, unit="A"),
            )
        assert_event_counts(acc, (expected_code, 1))

    def test_no_event_for_normal_input(self) -> None:
        with numerical_stability_scope() as acc:
            convert_voltage_star_to_delta(
                eps=TEST_EPS,
                max_mag=TEST_MAX_MAG,
                voltage_dto=ArrayComplexVoltageDto(
                    value=np.array([100.0 + 0j]), unit="V"
                ),
            )
        assert_no_events(acc)
