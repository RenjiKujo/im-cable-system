"""Tests for :class:`ParameterFitSpec` and :class:`InitMethod`.

``resolve_initial`` の 4 method 分岐とコンストラクタのバリデーション
（範囲不整合、``method='value'`` 時の必須/範囲外、それ以外 method での
``init_value`` 余分指定）を担保する。
"""

from __future__ import annotations

import math

import pytest

from im_cable_system.engine.shared.estimate_params_fit_spec import (  # noqa: E501
    InitMethod,
    ParameterFitSpec,
)


class TestResolveInitial:
    """``resolve_initial`` が method ごとに正しい値を返す。"""

    def test_midpoint_returns_average(self) -> None:
        spec = ParameterFitSpec(
            lb=1.0,
            ub=3.0,
            init_method=InitMethod.MIDPOINT,
        )
        assert spec.resolve_initial() == 2.0

    def test_lb_returns_lower_bound(self) -> None:
        spec = ParameterFitSpec(
            lb=0.1,
            ub=10.0,
            init_method=InitMethod.LB,
        )
        assert spec.resolve_initial() == 0.1

    def test_ub_returns_upper_bound(self) -> None:
        spec = ParameterFitSpec(
            lb=0.1,
            ub=10.0,
            init_method=InitMethod.UB,
        )
        assert spec.resolve_initial() == 10.0

    def test_value_returns_explicit_value(self) -> None:
        spec = ParameterFitSpec(
            lb=0.0,
            ub=2.0,
            init_method=InitMethod.VALUE,
            init_value=0.7,
        )
        assert spec.resolve_initial() == 0.7


class TestPostInitValidation:
    """コンストラクタの不変条件。"""

    def test_lb_greater_than_ub_raises(self) -> None:
        with pytest.raises(ValueError, match="lb=.*must not exceed ub="):
            ParameterFitSpec(
                lb=2.0,
                ub=1.0,
                init_method=InitMethod.MIDPOINT,
            )

    def test_value_method_requires_value(self) -> None:
        with pytest.raises(ValueError, match="requires 'init.value'"):
            ParameterFitSpec(
                lb=0.0,
                ub=1.0,
                init_method=InitMethod.VALUE,
                init_value=None,
            )

    def test_value_outside_bounds_raises(self) -> None:
        with pytest.raises(ValueError, match="outside bounds"):
            ParameterFitSpec(
                lb=0.0,
                ub=1.0,
                init_method=InitMethod.VALUE,
                init_value=2.5,
            )

    def test_non_value_method_must_not_have_init_value(self) -> None:
        with pytest.raises(ValueError, match="must not provide 'init.value'"):
            ParameterFitSpec(
                lb=0.0,
                ub=1.0,
                init_method=InitMethod.MIDPOINT,
                init_value=0.5,
            )

    def test_lb_equal_to_ub_is_valid(self) -> None:
        spec = ParameterFitSpec(
            lb=1.0,
            ub=1.0,
            init_method=InitMethod.MIDPOINT,
        )
        assert spec.resolve_initial() == 1.0

    def test_nan_lb_raises(self) -> None:
        with pytest.raises(ValueError, match="must be finite"):
            ParameterFitSpec(
                lb=math.nan,
                ub=1.0,
                init_method=InitMethod.MIDPOINT,
            )

    def test_inf_ub_raises(self) -> None:
        with pytest.raises(ValueError, match="must be finite"):
            ParameterFitSpec(
                lb=0.0,
                ub=math.inf,
                init_method=InitMethod.MIDPOINT,
            )

    def test_nan_init_value_raises(self) -> None:
        with pytest.raises(ValueError, match="must be finite"):
            ParameterFitSpec(
                lb=0.0,
                ub=1.0,
                init_method=InitMethod.VALUE,
                init_value=math.nan,
            )
