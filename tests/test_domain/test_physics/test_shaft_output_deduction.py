"""``physics.shaft_output_deduction`` の単体テスト。

``calculate_constant_friction_windage_loss`` /
``calculate_quadratic_stray_load_loss`` の式・shape・
``I_N <= eps`` フォールバックを検証する。
"""

from __future__ import annotations

import numpy as np
import pytest

from im_cable_system.engine.domain.physics import (
    calculate_constant_friction_windage_loss,
    calculate_quadratic_stray_load_loss,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexCurrentDto,
    FloatActivePowerDto,
    FloatCurrentDto,
)


class TestCalculateConstantFrictionWindageLoss:
    """P_FW = k_fw * P_N を reference_shape へブロードキャストする。"""

    def test_returns_constant_value_broadcast_to_shape(self) -> None:
        loss = calculate_constant_friction_windage_loss(
            nameplate_power=FloatActivePowerDto(value=1000.0, unit="W"),
            k_friction_windage=0.02,
            reference_shape=(3, 2),
        )
        assert loss.get_shape() == (3, 2)
        np.testing.assert_allclose(loss.get_value(), np.full((3, 2), 20.0))
        assert loss.get_unit() == "W"

    def test_zero_coefficient_gives_zero_loss(self) -> None:
        loss = calculate_constant_friction_windage_loss(
            nameplate_power=FloatActivePowerDto(value=500.0, unit="W"),
            k_friction_windage=0.0,
            reference_shape=(2,),
        )
        np.testing.assert_allclose(loss.get_value(), [0.0, 0.0])

    def test_converts_nameplate_power_unit_to_base(self) -> None:
        loss = calculate_constant_friction_windage_loss(
            nameplate_power=FloatActivePowerDto(value=1.0, unit="kW"),
            k_friction_windage=0.01,
            reference_shape=(1,),
        )
        # 1 kW = 1000 W, P_FW = 0.01 * 1000 = 10 W
        np.testing.assert_allclose(loss.get_value(), [10.0])


class TestCalculateQuadraticStrayLoadLoss:
    """P_stray = k_str * P_N * (|I2|/I_N)^2。"""

    def test_returns_expected_value(self) -> None:
        loss = calculate_quadratic_stray_load_loss(
            nameplate_power=FloatActivePowerDto(value=1000.0, unit="W"),
            nameplate_current=FloatCurrentDto(value=10.0, unit="A"),
            secondary_current=ArrayComplexCurrentDto(
                value=np.array([5.0 + 0j]), unit="A"
            ),
            k_stray_load=0.01,
            eps=1.0e-9,
        )
        # r_I2 = 5/10 = 0.5, P_stray = 0.01 * 1000 * 0.25 = 2.5
        np.testing.assert_allclose(loss.get_value(), [2.5])
        assert loss.get_unit() == "W"

    def test_no_load_current_gives_zero_loss(self) -> None:
        loss = calculate_quadratic_stray_load_loss(
            nameplate_power=FloatActivePowerDto(value=1000.0, unit="W"),
            nameplate_current=FloatCurrentDto(value=10.0, unit="A"),
            secondary_current=ArrayComplexCurrentDto(
                value=np.array([0.0 + 0j]), unit="A"
            ),
            k_stray_load=0.01,
            eps=1.0e-9,
        )
        np.testing.assert_allclose(loss.get_value(), [0.0])

    def test_matches_shape_of_secondary_current(self) -> None:
        loss = calculate_quadratic_stray_load_loss(
            nameplate_power=FloatActivePowerDto(value=1000.0, unit="W"),
            nameplate_current=FloatCurrentDto(value=10.0, unit="A"),
            secondary_current=ArrayComplexCurrentDto(
                value=np.zeros((2, 3), dtype=np.complex128), unit="A"
            ),
            k_stray_load=0.01,
            eps=1.0e-9,
        )
        assert loss.get_shape() == (2, 3)

    def test_nameplate_current_near_zero_falls_back_to_raw_magnitude(
        self,
    ) -> None:
        # I_N <= eps のとき r_I2 = |I2|（正規化しない）
        loss = calculate_quadratic_stray_load_loss(
            nameplate_power=FloatActivePowerDto(value=1000.0, unit="W"),
            nameplate_current=FloatCurrentDto(value=0.0, unit="A"),
            secondary_current=ArrayComplexCurrentDto(
                value=np.array([2.0 + 0j]), unit="A"
            ),
            k_stray_load=0.5,
            eps=1.0e-9,
        )
        # r_I2 = |I2| = 2, P_stray = 0.5 * 1000 * 4 = 2000
        np.testing.assert_allclose(loss.get_value(), [2000.0])

    @pytest.mark.parametrize("nameplate_current_value", [0.0, 1.0e-12])
    def test_nameplate_current_within_eps_uses_fallback(
        self, nameplate_current_value: float
    ) -> None:
        eps = 1.0e-6
        loss = calculate_quadratic_stray_load_loss(
            nameplate_power=FloatActivePowerDto(value=100.0, unit="W"),
            nameplate_current=FloatCurrentDto(
                value=nameplate_current_value, unit="A"
            ),
            secondary_current=ArrayComplexCurrentDto(
                value=np.array([3.0 + 4.0j]), unit="A"
            ),
            k_stray_load=1.0,
            eps=eps,
        )
        # |I2| = 5, fallback: r_I2 = 5, P_stray = 1 * 100 * 25 = 2500
        np.testing.assert_allclose(loss.get_value(), [2500.0])
