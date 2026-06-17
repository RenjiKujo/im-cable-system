"""``physics.electrical.immittance.impedance_combiner`` の単体テスト。

直列・並列のインピーダンス合成と、リスト版を検証する。
"""

from __future__ import annotations

import numpy as np
import pytest

from im_cable_system.engine.domain.physics.electrical import (
    combine_impedance_parallel,
    combine_impedance_series,
    combine_impedances_parallel,
    combine_impedances_series,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexImpedanceDto,
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


def _z(value: np.ndarray) -> ArrayComplexImpedanceDto:
    return ArrayComplexImpedanceDto(value=value, unit="Ω")


class TestCombineImpedanceSeries:
    """Z_total = Z1 + Z2。"""

    def test_sum_of_two_real_impedances(self) -> None:
        z = combine_impedance_series(
            eps=TEST_EPS,
            max_mag=TEST_MAX_MAG,
            impedance1=_z(np.array([3.0 + 0j])),
            impedance2=_z(np.array([4.0 + 0j])),
        )
        np.testing.assert_allclose(z.value, [7.0 + 0j])
        assert z.get_unit() == "Ω"

    def test_complex_addition(self) -> None:
        z = combine_impedance_series(
            eps=TEST_EPS,
            max_mag=TEST_MAX_MAG,
            impedance1=_z(np.array([3.0 + 4.0j])),
            impedance2=_z(np.array([1.0 + 2.0j])),
        )
        np.testing.assert_allclose(z.value, [4.0 + 6.0j])

    def test_raises_on_shape_mismatch(self) -> None:
        with pytest.raises(ValueError, match="形状が一致しません"):
            combine_impedance_series(
                eps=TEST_EPS,
                max_mag=TEST_MAX_MAG,
                impedance1=_z(np.array([1.0 + 0j])),
                impedance2=_z(np.array([1.0 + 0j, 2.0 + 0j])),
            )


class TestCombineImpedanceParallel:
    """Z_total = (Z1·Z2) / (Z1 + Z2)。"""

    def test_two_equal_resistors_give_half(self) -> None:
        """R ∥ R = R/2。"""
        z = combine_impedance_parallel(
            eps=TEST_EPS,
            max_mag=TEST_MAX_MAG,
            impedance1=_z(np.array([10.0 + 0j])),
            impedance2=_z(np.array([10.0 + 0j])),
        )
        np.testing.assert_allclose(z.value, [5.0 + 0j])

    def test_unequal_resistors(self) -> None:
        """6Ω ∥ 3Ω = 2Ω。"""
        z = combine_impedance_parallel(
            eps=TEST_EPS,
            max_mag=TEST_MAX_MAG,
            impedance1=_z(np.array([6.0 + 0j])),
            impedance2=_z(np.array([3.0 + 0j])),
        )
        np.testing.assert_allclose(z.value, [2.0 + 0j])

    def test_raises_on_shape_mismatch(self) -> None:
        with pytest.raises(ValueError, match="形状が一致しません"):
            combine_impedance_parallel(
                eps=TEST_EPS,
                max_mag=TEST_MAX_MAG,
                impedance1=_z(np.array([1.0 + 0j])),
                impedance2=_z(np.array([1.0 + 0j, 2.0 + 0j])),
            )


class TestCombineImpedancesSeriesList:
    """リスト版直列合成。"""

    def test_returns_single_element_unchanged(self) -> None:
        z0 = _z(np.array([5.0 + 0j]))
        z = combine_impedances_series(
            eps=TEST_EPS, max_mag=TEST_MAX_MAG, impedances=[z0]
        )
        np.testing.assert_allclose(z.value, z0.value)

    def test_sum_of_three_impedances(self) -> None:
        z = combine_impedances_series(
            eps=TEST_EPS,
            max_mag=TEST_MAX_MAG,
            impedances=[
                _z(np.array([1.0 + 0j])),
                _z(np.array([2.0 + 0j])),
                _z(np.array([3.0 + 0j])),
            ],
        )
        np.testing.assert_allclose(z.value, [6.0 + 0j])

    def test_raises_on_empty_list(self) -> None:
        with pytest.raises(ValueError, match="リストが空"):
            combine_impedances_series(
                eps=TEST_EPS, max_mag=TEST_MAX_MAG, impedances=[]
            )


class TestCombineImpedancesParallelList:
    """リスト版並列合成。"""

    def test_returns_single_element_unchanged(self) -> None:
        z0 = _z(np.array([5.0 + 0j]))
        z = combine_impedances_parallel(
            eps=TEST_EPS, max_mag=TEST_MAX_MAG, impedances=[z0]
        )
        np.testing.assert_allclose(z.value, z0.value)

    def test_three_equal_resistors_give_one_third(self) -> None:
        """R ∥ R ∥ R = R/3。"""
        z = combine_impedances_parallel(
            eps=TEST_EPS,
            max_mag=TEST_MAX_MAG,
            impedances=[
                _z(np.array([6.0 + 0j])),
                _z(np.array([6.0 + 0j])),
                _z(np.array([6.0 + 0j])),
            ],
        )
        np.testing.assert_allclose(z.value, [2.0 + 0j])

    def test_raises_on_empty_list(self) -> None:
        with pytest.raises(ValueError, match="リストが空"):
            combine_impedances_parallel(
                eps=TEST_EPS, max_mag=TEST_MAX_MAG, impedances=[]
            )


class TestImpedanceCombinerNumericalStability:
    """極端値でクランプイベントが記録されること。"""

    def test_series_records_event_on_both_small(self) -> None:
        with numerical_stability_scope() as acc:
            combine_impedance_series(
                eps=TEST_EPS,
                max_mag=TEST_MAX_MAG,
                impedance1=_z(np.array([0.0 + 0j])),
                impedance2=_z(np.array([0.0 + 0j])),
            )
        assert_event_counts(acc, (event_codes.IMPEDANCE_COMBINER_CLAMP, 1))

    def test_parallel_no_event_for_normal_input(self) -> None:
        with numerical_stability_scope() as acc:
            combine_impedance_parallel(
                eps=TEST_EPS,
                max_mag=TEST_MAX_MAG,
                impedance1=_z(np.array([1.0 + 0j])),
                impedance2=_z(np.array([1.0 + 0j])),
            )
        assert_no_events(acc)
