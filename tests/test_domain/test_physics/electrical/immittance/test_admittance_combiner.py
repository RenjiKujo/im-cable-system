"""``physics.electrical.immittance.admittance_combiner`` の単体テスト。

並列 (Y1+Y2) と直列 (1/(1/Y1+1/Y2)) の 2 つの基本合成と、リスト版を検証する。
"""

from __future__ import annotations

import numpy as np
import pytest

from im_cable_system.engine.domain.physics.electrical import (
    combine_admittance_parallel,
    combine_admittance_series,
    combine_admittances_parallel,
    combine_admittances_series,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexAdmittanceDto,
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


def _y(value: np.ndarray) -> ArrayComplexAdmittanceDto:
    return ArrayComplexAdmittanceDto(value=value, unit="S")


class TestCombineAdmittanceParallel:
    """並列合成: Y_total = Y1 + Y2。"""

    def test_sum_of_two_real_admittances(self) -> None:
        y = combine_admittance_parallel(
            eps=TEST_EPS,
            max_mag=TEST_MAX_MAG,
            admittance1=_y(np.array([0.3 + 0j])),
            admittance2=_y(np.array([0.4 + 0j])),
        )
        np.testing.assert_allclose(y.value, [0.7 + 0j])
        assert y.get_unit() == "S"

    def test_raises_on_shape_mismatch(self) -> None:
        with pytest.raises(ValueError, match="形状が一致しません"):
            combine_admittance_parallel(
                eps=TEST_EPS,
                max_mag=TEST_MAX_MAG,
                admittance1=_y(np.array([0.1 + 0j])),
                admittance2=_y(np.array([0.1 + 0j, 0.2 + 0j])),
            )


class TestCombineAdmittanceSeries:
    """直列合成: Y_total = Y1·Y2 / (Y1 + Y2)。"""

    def test_two_equal_admittances_give_half(self) -> None:
        y = combine_admittance_series(
            eps=TEST_EPS,
            max_mag=TEST_MAX_MAG,
            admittance1=_y(np.array([0.1 + 0j])),
            admittance2=_y(np.array([0.1 + 0j])),
        )
        np.testing.assert_allclose(y.value, [0.05 + 0j])

    def test_raises_on_shape_mismatch(self) -> None:
        with pytest.raises(ValueError, match="形状が一致しません"):
            combine_admittance_series(
                eps=TEST_EPS,
                max_mag=TEST_MAX_MAG,
                admittance1=_y(np.array([0.1 + 0j])),
                admittance2=_y(np.array([0.1 + 0j, 0.2 + 0j])),
            )


class TestCombineAdmittancesSeriesList:
    """リスト版直列合成。"""

    def test_returns_single_element_unchanged(self) -> None:
        y0 = _y(np.array([0.5 + 0j]))
        y = combine_admittances_series(
            eps=TEST_EPS, max_mag=TEST_MAX_MAG, admittances=[y0]
        )
        np.testing.assert_allclose(y.value, y0.value)

    def test_three_equal_admittances_give_one_third(self) -> None:
        y = combine_admittances_series(
            eps=TEST_EPS,
            max_mag=TEST_MAX_MAG,
            admittances=[
                _y(np.array([0.3 + 0j])),
                _y(np.array([0.3 + 0j])),
                _y(np.array([0.3 + 0j])),
            ],
        )
        np.testing.assert_allclose(y.value, [0.1 + 0j])

    def test_raises_on_empty_list(self) -> None:
        with pytest.raises(ValueError, match="リストが空"):
            combine_admittances_series(
                eps=TEST_EPS, max_mag=TEST_MAX_MAG, admittances=[]
            )


class TestCombineAdmittancesParallelList:
    """リスト版並列合成。"""

    def test_returns_single_element_unchanged(self) -> None:
        y0 = _y(np.array([0.5 + 0j]))
        y = combine_admittances_parallel(
            eps=TEST_EPS, max_mag=TEST_MAX_MAG, admittances=[y0]
        )
        np.testing.assert_allclose(y.value, y0.value)

    def test_sum_of_three_admittances(self) -> None:
        y = combine_admittances_parallel(
            eps=TEST_EPS,
            max_mag=TEST_MAX_MAG,
            admittances=[
                _y(np.array([0.1 + 0j])),
                _y(np.array([0.2 + 0j])),
                _y(np.array([0.3 + 0j])),
            ],
        )
        np.testing.assert_allclose(y.value, [0.6 + 0j])

    def test_raises_on_empty_list(self) -> None:
        with pytest.raises(ValueError, match="リストが空"):
            combine_admittances_parallel(
                eps=TEST_EPS, max_mag=TEST_MAX_MAG, admittances=[]
            )


class TestAdmittanceCombinerNumericalStability:
    """極端値でクランプイベントが記録される。"""

    def test_records_event_on_both_small(self) -> None:
        with numerical_stability_scope() as acc:
            combine_admittance_parallel(
                eps=TEST_EPS,
                max_mag=TEST_MAX_MAG,
                admittance1=_y(np.array([0.0 + 0j])),
                admittance2=_y(np.array([0.0 + 0j])),
            )
        assert_event_counts(acc, (event_codes.ADMITTANCE_COMBINER_CLAMP, 1))

    def test_no_event_for_normal_input(self) -> None:
        with numerical_stability_scope() as acc:
            combine_admittance_series(
                eps=TEST_EPS,
                max_mag=TEST_MAX_MAG,
                admittance1=_y(np.array([0.1 + 0j])),
                admittance2=_y(np.array([0.1 + 0j])),
            )
        assert_no_events(acc)
