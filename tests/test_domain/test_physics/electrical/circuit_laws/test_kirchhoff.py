"""``physics.electrical.circuit_laws.kirchhoff`` の単体テスト。

``solve_kirchhoff_voltage`` (KVL) と ``solve_kirchhoff_current`` (KCL) の
基本動作・solve_for 分岐・形状検証・引数チェックを検証する。
"""

from __future__ import annotations

import numpy as np
import pytest

from im_cable_system.engine.domain.physics.electrical import (
    solve_kirchhoff_current,
    solve_kirchhoff_voltage,
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


def _voltage(value: np.ndarray) -> ArrayComplexVoltageDto:
    return ArrayComplexVoltageDto(value=value, unit="V")


def _current(value: np.ndarray) -> ArrayComplexCurrentDto:
    return ArrayComplexCurrentDto(value=value, unit="A")


class TestSolveKirchhoffVoltageRemaining:
    """``solve_for='remaining'``: V_unknown = V_total - Σ V_known。"""

    def test_returns_total_minus_remaining_sum(self) -> None:
        v_total = _voltage(np.array([10.0 + 0j]))
        v1 = _voltage(np.array([3.0 + 0j]))
        v2 = _voltage(np.array([4.0 + 0j]))
        result = solve_kirchhoff_voltage(
            eps=TEST_EPS,
            max_mag=TEST_MAX_MAG,
            solve_for="remaining",
            total_voltage=v_total,
            remaining_voltages=[v1, v2],
        )
        np.testing.assert_allclose(result.value, [3.0 + 0j])
        assert result.get_unit() == "V"

    def test_raises_when_total_is_missing(self) -> None:
        with pytest.raises(
            ValueError, match='solve_for="remaining" では total_voltage'
        ):
            solve_kirchhoff_voltage(
                eps=TEST_EPS,
                max_mag=TEST_MAX_MAG,
                solve_for="remaining",
                remaining_voltages=[_voltage(np.array([1.0 + 0j]))],
            )


class TestSolveKirchhoffVoltageTotal:
    """``solve_for='total'``: V_total = Σ V。"""

    def test_returns_sum_of_remaining(self) -> None:
        result = solve_kirchhoff_voltage(
            eps=TEST_EPS,
            max_mag=TEST_MAX_MAG,
            solve_for="total",
            remaining_voltages=[
                _voltage(np.array([2.0 + 0j])),
                _voltage(np.array([3.0 + 0j])),
                _voltage(np.array([5.0 + 0j])),
            ],
        )
        np.testing.assert_allclose(result.value, [10.0 + 0j])

    def test_raises_when_no_remaining_provided(self) -> None:
        with pytest.raises(ValueError, match="少なくとも1つの電圧"):
            solve_kirchhoff_voltage(
                eps=TEST_EPS,
                max_mag=TEST_MAX_MAG,
                solve_for="total",
                remaining_voltages=[],
            )


class TestSolveKirchhoffVoltageValidation:
    """形状検証・無効な ``solve_for`` の検証。"""

    def test_raises_on_invalid_solve_for(self) -> None:
        with pytest.raises(ValueError, match="無効なsolve_for"):
            solve_kirchhoff_voltage(
                eps=TEST_EPS,
                max_mag=TEST_MAX_MAG,
                solve_for="unknown",  # type: ignore[arg-type]
                remaining_voltages=[_voltage(np.array([1.0 + 0j]))],
            )

    def test_raises_on_shape_mismatch(self) -> None:
        with pytest.raises(ValueError, match="電圧配列の形状が一致しません"):
            solve_kirchhoff_voltage(
                eps=TEST_EPS,
                max_mag=TEST_MAX_MAG,
                solve_for="total",
                remaining_voltages=[
                    _voltage(np.array([1.0 + 0j])),
                    _voltage(np.array([1.0 + 0j, 2.0 + 0j])),
                ],
            )


class TestSolveKirchhoffCurrentBranches:
    """KCL の 4 つの ``solve_for`` 分岐。"""

    def test_remaining_downstream_returns_upstream_minus_downstream(
        self,
    ) -> None:
        result = solve_kirchhoff_current(
            eps=TEST_EPS,
            max_mag=TEST_MAX_MAG,
            solve_for="remaining_downstream",
            upstream_currents=[_current(np.array([10.0 + 0j]))],
            downstream_currents=[_current(np.array([3.0 + 0j]))],
        )
        np.testing.assert_allclose(result.value, [7.0 + 0j])

    def test_remaining_upstream_returns_downstream_minus_upstream(
        self,
    ) -> None:
        result = solve_kirchhoff_current(
            eps=TEST_EPS,
            max_mag=TEST_MAX_MAG,
            solve_for="remaining_upstream",
            upstream_currents=[_current(np.array([3.0 + 0j]))],
            downstream_currents=[_current(np.array([10.0 + 0j]))],
        )
        np.testing.assert_allclose(result.value, [7.0 + 0j])

    def test_total_downstream_sums_upstream(self) -> None:
        result = solve_kirchhoff_current(
            eps=TEST_EPS,
            max_mag=TEST_MAX_MAG,
            solve_for="total_downstream",
            upstream_currents=[
                _current(np.array([1.0 + 0j])),
                _current(np.array([2.0 + 0j])),
            ],
        )
        np.testing.assert_allclose(result.value, [3.0 + 0j])

    def test_total_upstream_sums_downstream(self) -> None:
        result = solve_kirchhoff_current(
            eps=TEST_EPS,
            max_mag=TEST_MAX_MAG,
            solve_for="total_upstream",
            downstream_currents=[
                _current(np.array([1.0 + 0j])),
                _current(np.array([2.0 + 0j])),
            ],
        )
        np.testing.assert_allclose(result.value, [3.0 + 0j])


class TestSolveKirchhoffCurrentValidation:
    """KCL の引数検証・形状検証。"""

    def test_raises_on_invalid_solve_for(self) -> None:
        with pytest.raises(ValueError, match="無効なsolve_for"):
            solve_kirchhoff_current(
                eps=TEST_EPS,
                max_mag=TEST_MAX_MAG,
                solve_for="unknown",  # type: ignore[arg-type]
                upstream_currents=[_current(np.array([1.0 + 0j]))],
            )

    def test_raises_on_shape_mismatch(self) -> None:
        with pytest.raises(ValueError, match="電流配列の形状が一致しません"):
            solve_kirchhoff_current(
                eps=TEST_EPS,
                max_mag=TEST_MAX_MAG,
                solve_for="total_downstream",
                upstream_currents=[
                    _current(np.array([1.0 + 0j])),
                    _current(np.array([1.0 + 0j, 2.0 + 0j])),
                ],
            )

    def test_raises_when_required_branch_input_missing(self) -> None:
        with pytest.raises(
            ValueError, match="少なくとも1つの上流電流または下流電流"
        ):
            solve_kirchhoff_current(
                eps=TEST_EPS, max_mag=TEST_MAX_MAG, solve_for="total_downstream"
            )


class TestKirchhoffNumericalStability:
    """極端値で対応イベントが記録される。"""

    def test_voltage_extreme_event_recorded(self) -> None:
        with numerical_stability_scope() as acc:
            solve_kirchhoff_voltage(
                eps=TEST_EPS,
                max_mag=TEST_MAX_MAG,
                solve_for="total",
                remaining_voltages=[_voltage(np.array([0.0 + 0j]))],
            )
        assert_event_counts(
            acc, (event_codes.KIRCHHOFF_VOLTAGE_EXTREME_INPUT, 1)
        )

    def test_current_extreme_event_recorded(self) -> None:
        with numerical_stability_scope() as acc:
            solve_kirchhoff_current(
                eps=TEST_EPS,
                max_mag=TEST_MAX_MAG,
                solve_for="total_downstream",
                upstream_currents=[_current(np.array([0.0 + 0j]))],
            )
        assert_event_counts(
            acc, (event_codes.KIRCHHOFF_CURRENT_EXTREME_INPUT, 1)
        )

    def test_no_event_with_normal_input(self) -> None:
        with numerical_stability_scope() as acc:
            solve_kirchhoff_voltage(
                eps=TEST_EPS,
                max_mag=TEST_MAX_MAG,
                solve_for="total",
                remaining_voltages=[_voltage(np.array([100.0 + 0j]))],
            )
        assert_no_events(acc)
