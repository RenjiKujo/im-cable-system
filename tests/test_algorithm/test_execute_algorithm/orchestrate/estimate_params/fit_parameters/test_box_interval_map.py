"""``fit_parameters.box_interval_map`` の単体テスト。

``BoxIntervalMap`` および薄いラッパ関数
``physical_to_unit_interval`` / ``unit_interval_to_physical`` を検証する。

検証観点:
    - 物理座標と単位区間座標の往復が一致する。
    - 固定次元（``lb_i == ub_i``）は ``z_i = 0.5`` で扱われ、
      物理側は ``lb_i`` を返す。
    - 不正な入力（形状不一致・非有限・``ub < lb``・可動次元の極小幅）で
      ``ValueError`` を発生させる。
    - ``unit_lower_bounds`` / ``unit_upper_bounds`` は可動次元 [0, 1]、
      固定次元 0.5 を返す。
"""

from __future__ import annotations

import numpy as np
import pytest

from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.fit_parameters.box_interval_map import (  # noqa: E501
    BoxIntervalMap,
    physical_to_unit_interval,
    unit_interval_to_physical,
)


class TestBoxIntervalMapRoundTrip:
    """物理座標と単位区間座標の往復一貫性を確認する。"""

    @pytest.mark.parametrize(
        "lb, ub, x",
        [
            (
                np.array([0.0, -1.0, 100.0]),
                np.array([1.0, 1.0, 200.0]),
                np.array([0.5, 0.25, 150.0]),
            ),
            (
                np.array([-5.0, 0.0]),
                np.array([5.0, 10.0]),
                np.array([2.5, 7.5]),
            ),
        ],
    )
    def test_to_unit_then_to_physical_returns_original(
        self, lb: np.ndarray, ub: np.ndarray, x: np.ndarray
    ) -> None:
        mapping = BoxIntervalMap.create(lb, ub)
        z = mapping.to_unit(x)
        x_back = mapping.to_physical(z)
        np.testing.assert_allclose(x_back, x)

    def test_to_physical_then_to_unit_returns_original(self) -> None:
        lb = np.array([0.0, 0.0])
        ub = np.array([2.0, 4.0])
        z = np.array([0.25, 0.75])
        mapping = BoxIntervalMap.create(lb, ub)
        x = mapping.to_physical(z)
        z_back = mapping.to_unit(x)
        np.testing.assert_allclose(z_back, z)


class TestBoxIntervalMapFixedDimensions:
    """固定次元（lb_i == ub_i）の扱いを確認する。"""

    def test_to_unit_returns_0_5_at_fixed_dimension(self) -> None:
        lb = np.array([0.0, 1.0])
        ub = np.array([2.0, 1.0])
        mapping = BoxIntervalMap.create(lb, ub)
        z = mapping.to_unit(np.array([1.5, 1.0]))
        np.testing.assert_allclose(z, [0.75, 0.5])

    def test_to_physical_returns_lb_at_fixed_dimension(self) -> None:
        """``z`` の値に関係なく、固定次元は ``lb_i`` を返す。"""
        lb = np.array([0.0, 1.0])
        ub = np.array([2.0, 1.0])
        mapping = BoxIntervalMap.create(lb, ub)
        x = mapping.to_physical(np.array([0.25, 0.99]))
        np.testing.assert_allclose(x, [0.5, 1.0])

    def test_unit_bounds_at_fixed_dimension(self) -> None:
        """固定次元は ``unit_lower_bounds = unit_upper_bounds = 0.5``。"""
        lb = np.array([0.0, 1.0])
        ub = np.array([2.0, 1.0])
        mapping = BoxIntervalMap.create(lb, ub)
        np.testing.assert_allclose(mapping.unit_lower_bounds(), [0.0, 0.5])
        np.testing.assert_allclose(mapping.unit_upper_bounds(), [1.0, 0.5])


class TestBoxIntervalMapValidation:
    """不正入力の検証。"""

    def test_shape_mismatch_raises(self) -> None:
        with pytest.raises(ValueError, match="長さが一致しません"):
            BoxIntervalMap.create(np.array([0.0, 1.0]), np.array([1.0]))

    def test_non_finite_raises(self) -> None:
        with pytest.raises(ValueError, match="有限値"):
            BoxIntervalMap.create(np.array([np.nan]), np.array([1.0]))

    def test_ub_less_than_lb_raises(self) -> None:
        with pytest.raises(ValueError, match="以上"):
            BoxIntervalMap.create(np.array([1.0]), np.array([0.0]))

    def test_movable_span_too_small_raises(self) -> None:
        """可動次元の幅が極小（``< _MIN_FINITE_SPAN``）だと拒否される。"""
        with pytest.raises(ValueError, match="小さすぎます"):
            BoxIntervalMap.create(np.array([0.0]), np.array([1e-20]))

    def test_to_unit_rejects_shape_mismatch(self) -> None:
        mapping = BoxIntervalMap.create(np.array([0.0]), np.array([1.0]))
        with pytest.raises(ValueError):
            mapping.to_unit(np.array([0.5, 0.5]))

    def test_to_unit_rejects_non_finite(self) -> None:
        mapping = BoxIntervalMap.create(np.array([0.0]), np.array([1.0]))
        with pytest.raises(ValueError, match="有限値"):
            mapping.to_unit(np.array([np.nan]))

    def test_to_physical_rejects_non_finite(self) -> None:
        mapping = BoxIntervalMap.create(np.array([0.0]), np.array([1.0]))
        with pytest.raises(ValueError, match="有限値"):
            mapping.to_physical(np.array([np.inf]))


class TestThinWrappers:
    """``physical_to_unit_interval`` / ``unit_interval_to_physical`` の動作。"""

    def test_thin_wrapper_to_unit_matches_class_method(self) -> None:
        lb = np.array([0.0])
        ub = np.array([1.0])
        x = np.array([0.7])
        z_wrapper = physical_to_unit_interval(x, lb, ub)
        z_class = BoxIntervalMap.create(lb, ub).to_unit(x)
        np.testing.assert_allclose(z_wrapper, z_class)

    def test_thin_wrapper_to_physical_matches_class_method(self) -> None:
        lb = np.array([0.0])
        ub = np.array([1.0])
        z = np.array([0.7])
        x_wrapper = unit_interval_to_physical(z, lb, ub)
        x_class = BoxIntervalMap.create(lb, ub).to_physical(z)
        np.testing.assert_allclose(x_wrapper, x_class)
