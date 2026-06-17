"""``validation.energy_conservation`` の単体テスト。

``validate_energy_conservation`` は ``input = output + loss`` を相対誤差で
検証する。完全一致・許容内・許容外・形状不一致・無効電力・配列の混在
など主要パターンを網羅する。
"""

from __future__ import annotations

import numpy as np
import pytest

from im_cable_system.engine.domain.validation import (
    validate_energy_conservation,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexPowerDto,
)
from tests.test_domain._domain_helpers import (
    TEST_EPS,
)


def _power(value: np.ndarray) -> ArrayComplexPowerDto:
    return ArrayComplexPowerDto(value=value, unit="VA")


class TestValidateEnergyConservationPasses:
    """エネルギー保存則を満たすケース。"""

    def test_passes_when_perfectly_balanced(self) -> None:
        """``input = output + loss`` 完全一致の場合。"""
        result = validate_energy_conservation(
            input_power=_power(np.array([20.0 + 0j])),
            output_power=_power(np.array([0.0 + 0j])),
            loss_power=_power(np.array([20.0 + 0j])),
            tolerance=1e-6,
            eps=TEST_EPS,
        )
        assert result.is_valid is True

    def test_passes_within_relative_tolerance(self) -> None:
        """相対誤差が ``tolerance`` 以下ならパス。"""
        result = validate_energy_conservation(
            input_power=_power(np.array([100.0 + 0j])),
            output_power=_power(np.array([0.0 + 0j])),
            loss_power=_power(np.array([100.0001 + 0j])),  # 相対誤差 1e-6
            tolerance=1e-5,
            eps=TEST_EPS,
        )
        assert result.is_valid is True

    def test_passes_with_reactive_power(self) -> None:
        """複素電力の有効・無効両成分が保存されることを検証。"""
        result = validate_energy_conservation(
            input_power=_power(np.array([20.0 + 10.0j])),
            output_power=_power(np.array([0.0 + 0j])),
            loss_power=_power(np.array([20.0 + 10.0j])),
            tolerance=1e-6,
            eps=TEST_EPS,
        )
        assert result.is_valid is True

    def test_passes_with_load_in_output(self) -> None:
        result = validate_energy_conservation(
            input_power=_power(np.array([30.0 + 0j])),
            output_power=_power(np.array([20.0 + 0j])),
            loss_power=_power(np.array([10.0 + 0j])),
            tolerance=1e-6,
            eps=TEST_EPS,
        )
        assert result.is_valid is True


class TestValidateEnergyConservationFails:
    """エネルギー保存則が破れているケース。"""

    def test_fails_when_relative_error_exceeds_tolerance(self) -> None:
        result = validate_energy_conservation(
            input_power=_power(np.array([20.0 + 0j])),
            output_power=_power(np.array([0.0 + 0j])),
            loss_power=_power(np.array([25.0 + 0j])),
            tolerance=1e-6,
            eps=TEST_EPS,
        )
        assert result.is_valid is False
        assert "エネルギー保存則の検証に失敗" in result.message

    def test_fails_when_partial_elements_violate(self) -> None:
        """配列の一部要素のみ違反する場合でも is_valid=False となる。"""
        result = validate_energy_conservation(
            input_power=_power(np.array([10.0, 10.0, 10.0]) + 0j),
            output_power=_power(np.array([0.0, 0.0, 0.0]) + 0j),
            loss_power=_power(np.array([10.0, 20.0, 10.0]) + 0j),
            tolerance=1e-6,
            eps=TEST_EPS,
        )
        assert result.is_valid is False
        assert "違反箇所数: 1/3" in result.message

    def test_fails_when_imaginary_component_differs(self) -> None:
        """実部は合っているが虚部だけ違う場合でも失敗（複素差分で比較）。"""
        result = validate_energy_conservation(
            input_power=_power(np.array([20.0 + 5.0j])),
            output_power=_power(np.array([0.0 + 0j])),
            loss_power=_power(np.array([20.0 + 0j])),  # 虚部 5 のずれ
            tolerance=1e-6,
            eps=TEST_EPS,
        )
        assert result.is_valid is False


class TestValidateEnergyConservationSmallInput:
    """入力電力が極小（``eps`` 未満）のときは絶対誤差で評価。"""

    def test_passes_when_diff_is_below_tolerance_in_absolute_terms(
        self,
    ) -> None:
        result = validate_energy_conservation(
            input_power=_power(np.array([0.0 + 0j])),
            output_power=_power(np.array([0.0 + 0j])),
            loss_power=_power(np.array([1e-9 + 0j])),
            tolerance=1e-6,
            eps=TEST_EPS,
        )
        assert result.is_valid is True

    def test_fails_when_absolute_diff_exceeds_tolerance(self) -> None:
        result = validate_energy_conservation(
            input_power=_power(np.array([0.0 + 0j])),
            output_power=_power(np.array([0.0 + 0j])),
            loss_power=_power(np.array([1e-3 + 0j])),
            tolerance=1e-6,
            eps=TEST_EPS,
        )
        assert result.is_valid is False


class TestValidateEnergyConservationShapeMismatch:
    """配列形状不一致を ``ValueError`` ではなく ``is_valid=False`` で返す。"""

    @pytest.mark.parametrize(
        "output_shape, loss_shape",
        [
            ((2,), (1,)),
            ((1,), (2,)),
        ],
    )
    def test_returns_invalid_result_on_shape_mismatch(
        self, output_shape: tuple[int, ...], loss_shape: tuple[int, ...]
    ) -> None:
        result = validate_energy_conservation(
            input_power=_power(np.zeros(1, dtype=np.complex128)),
            output_power=_power(np.zeros(output_shape, dtype=np.complex128)),
            loss_power=_power(np.zeros(loss_shape, dtype=np.complex128)),
            eps=TEST_EPS,
        )
        assert result.is_valid is False
        assert "電力配列の形状が一致しません" in result.message
