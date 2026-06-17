"""``physics.characteristic`` の単体テスト。

機器特性計算 4 関数を検証する:
    - ``calculate_efficiency``: η = P_out / P_in（範囲外で ``ValueError``）
    - ``calculate_power_factor``: pf = Re(S) / |S|（|S|≈0 でクランプ・イベント記録）
    - ``calculate_torque``: τ = P / ω（ω≈0 で要素 NaN、イベント記録）
    - ``calculate_rotational_speed``: n = (1-s) · 120·f/poles（rpm → rad/s）
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from im_cable_system.engine.domain.physics import (
    calculate_efficiency,
    calculate_power_factor,
    calculate_rotational_speed,
    calculate_torque,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayActivePowerDto,
    ArrayComplexPowerDto,
    ArrayFrequencyDto,
    ArrayRotationalSpeedDto,
    ArraySlipDto,
)
from im_cable_system.engine.shared.numerical_stability import (
    event_codes,
    numerical_stability_scope,
)
from tests.test_domain._domain_helpers import (
    TEST_EPS,
    assert_event_counts,
    assert_no_events,
)


class TestCalculateEfficiencyBasic:
    """効率計算の基本動作。"""

    def test_returns_ratio_of_output_to_input(self) -> None:
        eta = calculate_efficiency(
            input_active_power=ArrayActivePowerDto(
                value=np.array([100.0, 200.0]), unit="W"
            ),
            output_active_power=ArrayActivePowerDto(
                value=np.array([90.0, 180.0]), unit="W"
            ),
            eps=TEST_EPS,
        )
        np.testing.assert_allclose(eta.get_value(), [0.9, 0.9])
        assert eta.get_unit() == "-"

    def test_returns_zero_when_input_is_zero(self) -> None:
        """入力 0 のとき 0/0 ではなく 0 を返す（``np.where`` の分岐）。"""
        eta = calculate_efficiency(
            input_active_power=ArrayActivePowerDto(
                value=np.array([0.0, 100.0]), unit="W"
            ),
            output_active_power=ArrayActivePowerDto(
                value=np.array([0.0, 80.0]), unit="W"
            ),
            eps=TEST_EPS,
        )
        np.testing.assert_allclose(eta.get_value(), [0.0, 0.8])

    def test_returns_zero_when_input_is_near_zero(self) -> None:
        """入力が eps 以下（近接ゼロ）のとき効率 0 を返す。"""
        eps = 1e-9
        eta = calculate_efficiency(
            input_active_power=ArrayActivePowerDto(
                value=np.array([eps / 2.0, 100.0]), unit="W"
            ),
            output_active_power=ArrayActivePowerDto(
                value=np.array([0.0, 80.0]), unit="W"
            ),
            eps=eps,
        )
        np.testing.assert_allclose(eta.get_value(), [0.0, 0.8])


class TestCalculateEfficiencyRangeErrors:
    """効率が物理的に成立しない場合 ``ValueError``。"""

    def test_raises_when_efficiency_exceeds_one(self) -> None:
        with pytest.raises(ValueError, match="1.0を超える"):
            calculate_efficiency(
                input_active_power=ArrayActivePowerDto(
                    value=np.array([100.0]), unit="W"
                ),
                output_active_power=ArrayActivePowerDto(
                    value=np.array([150.0]), unit="W"
                ),
                eps=TEST_EPS,
            )

    def test_raises_when_efficiency_is_negative(self) -> None:
        with pytest.raises(ValueError, match="負の値"):
            calculate_efficiency(
                input_active_power=ArrayActivePowerDto(
                    value=np.array([100.0]), unit="W"
                ),
                output_active_power=ArrayActivePowerDto(
                    value=np.array([-10.0]), unit="W"
                ),
                eps=TEST_EPS,
            )

    def test_raises_when_shapes_mismatch(self) -> None:
        with pytest.raises(ValueError, match="配列形状が一致しません"):
            calculate_efficiency(
                input_active_power=ArrayActivePowerDto(
                    value=np.array([100.0, 200.0]), unit="W"
                ),
                output_active_power=ArrayActivePowerDto(
                    value=np.array([90.0]), unit="W"
                ),
                eps=TEST_EPS,
            )


class TestCalculatePowerFactorBasic:
    """力率計算の基本動作。"""

    def test_returns_one_for_pure_active_power(self) -> None:
        """P=100, |S|=100 → pf=1。"""
        pf = calculate_power_factor(
            ArrayComplexPowerDto(
                value=np.array([100.0 + 0j], dtype=np.complex128), unit="VA"
            ),
            eps=TEST_EPS,
        )
        assert pf.get_value()[0] == pytest.approx(1.0)
        assert pf.get_unit() == "-"

    def test_returns_general_power_factor(self) -> None:
        """P=80, Q=60, |S|=100 → pf=0.8。"""
        pf = calculate_power_factor(
            ArrayComplexPowerDto(
                value=np.array([80.0 + 60.0j], dtype=np.complex128), unit="VA"
            ),
            eps=TEST_EPS,
        )
        assert pf.get_value()[0] == pytest.approx(0.8)


class TestCalculatePowerFactorNearZeroApparent:
    """皮相電力が極小の要素はクランプされ、イベントが記録される。"""

    def test_clamps_and_records_event(self) -> None:
        eps = 1e-9
        with numerical_stability_scope() as acc:
            pf = calculate_power_factor(
                ArrayComplexPowerDto(
                    value=np.array(
                        [eps / 2.0 + 0j, 80.0 + 60.0j], dtype=np.complex128
                    ),
                    unit="VA",
                ),
                eps=eps,
            )
        # |S|<=eps の要素は分母を eps にクランプ: Re=eps/2 → pf=0.5。
        assert pf.get_value()[0] == pytest.approx(0.5)
        assert pf.get_value()[1] == pytest.approx(0.8)
        assert_event_counts(
            acc,
            (event_codes.APPARENT_POWER_NEAR_ZERO_POWER_FACTOR, 1),
        )

    def test_no_event_when_all_apparent_finite(self) -> None:
        with numerical_stability_scope() as acc:
            calculate_power_factor(
                ArrayComplexPowerDto(
                    value=np.array([100.0 + 0j], dtype=np.complex128),
                    unit="VA",
                ),
                eps=TEST_EPS,
            )
        assert_no_events(acc)


class TestCalculateTorqueBasic:
    """トルク計算の基本動作。"""

    def test_returns_power_divided_by_angular_velocity(self) -> None:
        """P=200 [W], ω=100 [rad/s] → τ=2 [Nm]。"""
        torque = calculate_torque(
            eps=TEST_EPS,
            output_power=ArrayActivePowerDto(value=np.array([200.0]), unit="W"),
            rotational_speed=ArrayRotationalSpeedDto(
                value=np.array([100.0]), unit="rad/s"
            ),
        )
        np.testing.assert_allclose(torque.get_value(), [2.0])
        assert torque.get_unit() == "Nm"

    def test_raises_when_shapes_mismatch(self) -> None:
        with pytest.raises(ValueError, match="配列形状が一致しません"):
            calculate_torque(
                eps=TEST_EPS,
                output_power=ArrayActivePowerDto(
                    value=np.array([100.0, 200.0]), unit="W"
                ),
                rotational_speed=ArrayRotationalSpeedDto(
                    value=np.array([10.0]), unit="rad/s"
                ),
            )


class TestCalculateTorqueZeroOmega:
    """角速度が極小の要素は NaN になり、イベントが記録される。"""

    def test_nan_at_zero_omega_and_records_event(self) -> None:
        with numerical_stability_scope() as acc:
            torque = calculate_torque(
                eps=TEST_EPS,
                output_power=ArrayActivePowerDto(
                    value=np.array([100.0, 200.0]), unit="W"
                ),
                rotational_speed=ArrayRotationalSpeedDto(
                    value=np.array([0.0, 100.0]), unit="rad/s"
                ),
            )
        values = torque.get_value()
        assert math.isnan(values[0])
        assert values[1] == pytest.approx(2.0)
        assert_event_counts(acc, (event_codes.OMEGA_NEAR_ZERO_TORQUE, 1))

    def test_no_event_when_all_omega_finite(self) -> None:
        with numerical_stability_scope() as acc:
            calculate_torque(
                eps=TEST_EPS,
                output_power=ArrayActivePowerDto(
                    value=np.array([100.0]), unit="W"
                ),
                rotational_speed=ArrayRotationalSpeedDto(
                    value=np.array([50.0]), unit="rad/s"
                ),
            )
        assert_no_events(acc)


class TestCalculateRotationalSpeedBasic:
    """誘導電動機回転速度の基本動作。"""

    def test_synchronous_speed_at_zero_slip(self) -> None:
        """s=0、f=50 Hz、poles=4 → n_s = 1500 rpm = 50π rad/s。"""
        omega = calculate_rotational_speed(
            slip_array=ArraySlipDto(value=np.array([0.0]), unit="-"),
            frequency_array=ArrayFrequencyDto(
                value=np.array([50.0]), unit="Hz"
            ),
            poles=4,
        )
        expected_rpm = 1500.0
        expected_rad_per_s = expected_rpm * 2.0 * math.pi / 60.0
        np.testing.assert_allclose(omega.get_value(), [expected_rad_per_s])

    @pytest.mark.parametrize(
        "slip, frequency, poles, expected_rpm",
        [
            (0.05, 50.0, 4, (1.0 - 0.05) * 1500.0),
            (0.10, 60.0, 4, (1.0 - 0.10) * 1800.0),
            (0.00, 50.0, 2, 3000.0),
        ],
    )
    def test_uses_slip_frequency_and_poles(
        self,
        slip: float,
        frequency: float,
        poles: int,
        expected_rpm: float,
    ) -> None:
        omega = calculate_rotational_speed(
            slip_array=ArraySlipDto(value=np.array([slip]), unit="-"),
            frequency_array=ArrayFrequencyDto(
                value=np.array([frequency]), unit="Hz"
            ),
            poles=poles,
        )
        expected_rad_per_s = expected_rpm * 2.0 * math.pi / 60.0
        np.testing.assert_allclose(omega.get_value(), [expected_rad_per_s])

    def test_raises_when_shapes_mismatch(self) -> None:
        with pytest.raises(ValueError, match="配列形状が一致しません"):
            calculate_rotational_speed(
                slip_array=ArraySlipDto(value=np.array([0.0, 0.05]), unit="-"),
                frequency_array=ArrayFrequencyDto(
                    value=np.array([50.0]), unit="Hz"
                ),
                poles=4,
            )

    @pytest.mark.parametrize("poles", [0, -2, 3])
    def test_raises_when_poles_not_positive_even(self, poles: int) -> None:
        """poles が正の偶数でない（0・負数・奇数）場合は ValueError。"""
        with pytest.raises(ValueError, match="正の偶数"):
            calculate_rotational_speed(
                slip_array=ArraySlipDto(value=np.array([0.0]), unit="-"),
                frequency_array=ArrayFrequencyDto(
                    value=np.array([50.0]), unit="Hz"
                ),
                poles=poles,
            )
