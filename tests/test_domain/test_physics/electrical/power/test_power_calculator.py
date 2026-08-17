"""``physics.electrical.power.power_calculator`` の単体テスト。

``power_from_voltage_and_current`` / ``power_from_voltage_and_admittance`` /
``power_from_current_and_impedance`` / ``add_power`` / ``subtract_power`` の
基本動作と整合性、形状不一致の例外を検証する。
"""

from __future__ import annotations

import numpy as np
import pytest

from im_cable_system.engine.domain.physics.electrical import (
    add_power,
    power_from_current_and_impedance,
    power_from_voltage_and_admittance,
    power_from_voltage_and_current,
    subtract_power,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexAdmittanceDto,
    ArrayComplexCurrentDto,
    ArrayComplexImpedanceDto,
    ArrayComplexPowerDto,
    ArrayComplexVoltageDto,
)


class TestPowerFromVoltageAndCurrent:
    """S = V · conj(I)。"""

    def test_returns_complex_power_va(self) -> None:
        # V = 10, I = 2 - 1j → conj(I) = 2 + 1j → S = 20 + 10j
        v = ArrayComplexVoltageDto(value=np.array([10.0 + 0j]), unit="V")
        i = ArrayComplexCurrentDto(value=np.array([2.0 - 1.0j]), unit="A")
        power = power_from_voltage_and_current(voltage=v, current=i)
        np.testing.assert_allclose(power.value, [20.0 + 10.0j])
        assert power.get_unit() == "VA"

    def test_active_part_equals_re_v_re_i_plus_im_v_im_i(self) -> None:
        v = ArrayComplexVoltageDto(value=np.array([3.0 + 4.0j]), unit="V")
        i = ArrayComplexCurrentDto(value=np.array([1.0 + 2.0j]), unit="A")
        power = power_from_voltage_and_current(voltage=v, current=i)
        # S = (3 + 4j) * (1 - 2j) = 3 - 6j + 4j + 8 = 11 - 2j
        np.testing.assert_allclose(power.value, [11.0 - 2.0j])

    def test_raises_on_shape_mismatch(self) -> None:
        v = ArrayComplexVoltageDto(value=np.array([1.0, 2.0]), unit="V")
        i = ArrayComplexCurrentDto(value=np.array([1.0 + 0j]), unit="A")
        with pytest.raises(ValueError, match="配列形状が一致しません"):
            power_from_voltage_and_current(voltage=v, current=i)


class TestPowerFromVoltageAndAdmittance:
    """S = V · conj(V·Y)。実数 Y なら ``|V|^2 · Y``。"""

    def test_returns_v_squared_times_y_for_real_admittance(self) -> None:
        v = ArrayComplexVoltageDto(value=np.array([10.0 + 0j]), unit="V")
        y = ArrayComplexAdmittanceDto(value=np.array([0.5 + 0j]), unit="S")
        power = power_from_voltage_and_admittance(voltage=v, admittance=y)
        np.testing.assert_allclose(power.value, [50.0 + 0j])
        assert power.get_unit() == "VA"

    def test_matches_v_times_conj_i_definition(self) -> None:
        """直接計算した ``V · conj(I)`` と一致する。"""
        v = np.array([10.0 + 5.0j])
        y = np.array([0.2 + 0.1j])
        i = v * y
        expected = v * np.conjugate(i)
        power = power_from_voltage_and_admittance(
            voltage=ArrayComplexVoltageDto(value=v, unit="V"),
            admittance=ArrayComplexAdmittanceDto(value=y, unit="S"),
        )
        np.testing.assert_allclose(power.value, expected)

    def test_raises_on_shape_mismatch(self) -> None:
        with pytest.raises(ValueError, match="配列形状が一致しません"):
            power_from_voltage_and_admittance(
                voltage=ArrayComplexVoltageDto(
                    value=np.array([1.0, 2.0]), unit="V"
                ),
                admittance=ArrayComplexAdmittanceDto(
                    value=np.array([1.0 + 0j]), unit="S"
                ),
            )


class TestPowerFromCurrentAndImpedance:
    """S = Z · I · conj(I) = Z · |I|^2。"""

    def test_returns_z_times_i_squared(self) -> None:
        z = ArrayComplexImpedanceDto(value=np.array([2.0 + 1.0j]), unit="Ω")
        i = ArrayComplexCurrentDto(value=np.array([3.0 + 0j]), unit="A")
        power = power_from_current_and_impedance(current=i, impedance=z)
        # S = (2 + 1j) * 3 * 3 = 18 + 9j
        np.testing.assert_allclose(power.value, [18.0 + 9.0j])

    def test_active_power_equals_resistance_times_i_squared(self) -> None:
        """純抵抗 R, |I|=2 → P = 4R, Q = 0。"""
        z = ArrayComplexImpedanceDto(value=np.array([5.0 + 0j]), unit="Ω")
        i = ArrayComplexCurrentDto(value=np.array([2.0 + 0j]), unit="A")
        power = power_from_current_and_impedance(current=i, impedance=z)
        np.testing.assert_allclose(power.value, [20.0 + 0j])

    def test_raises_on_shape_mismatch(self) -> None:
        with pytest.raises(ValueError, match="配列形状が一致しません"):
            power_from_current_and_impedance(
                current=ArrayComplexCurrentDto(
                    value=np.array([1.0 + 0j]), unit="A"
                ),
                impedance=ArrayComplexImpedanceDto(
                    value=np.array([1.0, 2.0]), unit="Ω"
                ),
            )


class TestAddPower:
    """``add_power`` は基本単位 VA で合算する。"""

    def test_sums_two_powers_element_wise(self) -> None:
        s1 = ArrayComplexPowerDto(value=np.array([10.0 + 0j, 5.0]), unit="VA")
        s2 = ArrayComplexPowerDto(value=np.array([1.0 + 2.0j, 3.0]), unit="VA")
        total = add_power(power1=s1, power2=s2)
        np.testing.assert_allclose(total.value, [11.0 + 2.0j, 8.0])
        assert total.get_unit() == "VA"

    def test_raises_on_shape_mismatch(self) -> None:
        with pytest.raises(ValueError, match="電力配列の形状が一致しません"):
            add_power(
                power1=ArrayComplexPowerDto(value=np.array([1.0]), unit="VA"),
                power2=ArrayComplexPowerDto(
                    value=np.array([1.0, 2.0]), unit="VA"
                ),
            )


class TestSubtractPower:
    """``subtract_power`` は基本単位 VA で power1 - power2 を計算する。"""

    def test_subtracts_two_powers_element_wise(self) -> None:
        s1 = ArrayComplexPowerDto(value=np.array([10.0 + 0j, 5.0]), unit="VA")
        s2 = ArrayComplexPowerDto(value=np.array([1.0 + 2.0j, 3.0]), unit="VA")
        result = subtract_power(power1=s1, power2=s2)
        np.testing.assert_allclose(result.value, [9.0 - 2.0j, 2.0])
        assert result.get_unit() == "VA"

    def test_is_inverse_of_add_power(self) -> None:
        s1 = ArrayComplexPowerDto(value=np.array([7.0 + 3.0j]), unit="VA")
        s2 = ArrayComplexPowerDto(value=np.array([2.0 - 1.0j]), unit="VA")
        total = add_power(power1=s1, power2=s2)
        back = subtract_power(power1=total, power2=s2)
        np.testing.assert_allclose(back.value, s1.value)

    def test_raises_on_shape_mismatch(self) -> None:
        with pytest.raises(ValueError, match="電力配列の形状が一致しません"):
            subtract_power(
                power1=ArrayComplexPowerDto(value=np.array([1.0]), unit="VA"),
                power2=ArrayComplexPowerDto(
                    value=np.array([1.0, 2.0]), unit="VA"
                ),
            )
