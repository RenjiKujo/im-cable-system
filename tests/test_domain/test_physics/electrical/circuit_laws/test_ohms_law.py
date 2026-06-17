"""``physics.electrical.circuit_laws.ohms_law`` の単体テスト。

オームの法則の 4 関数を検証する:
    - V = I · Z (calculate_voltage_from_current_and_impedance)
    - V = I / Y (calculate_voltage_from_current_and_admittance)
    - I = V / Z (calculate_current_from_voltage_and_impedance)
    - I = V · Y (calculate_current_from_voltage_and_admittance)
"""

from __future__ import annotations

import numpy as np
import pytest

from im_cable_system.engine.domain.physics.electrical import (
    calculate_current_from_voltage_and_admittance,
    calculate_current_from_voltage_and_impedance,
    calculate_voltage_from_current_and_admittance,
    calculate_voltage_from_current_and_impedance,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexAdmittanceDto,
    ArrayComplexCurrentDto,
    ArrayComplexImpedanceDto,
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


class TestVoltageFromCurrentAndImpedance:
    """V = I · Z。"""

    def test_returns_product_of_current_and_impedance(self) -> None:
        i = ArrayComplexCurrentDto(value=np.array([2.0 + 0j]), unit="A")
        z = ArrayComplexImpedanceDto(value=np.array([3.0 + 4.0j]), unit="Ω")
        v = calculate_voltage_from_current_and_impedance(
            eps=TEST_EPS, max_mag=TEST_MAX_MAG, current=i, impedance=z
        )
        np.testing.assert_allclose(v.value, [6.0 + 8.0j])
        assert v.get_unit() == "V"

    @pytest.mark.parametrize(
        "i_val, z_val, v_val",
        [
            (1.0 + 0j, 5.0 + 0j, 5.0 + 0j),
            (0.0 + 1j, 0.0 + 1j, -1.0 + 0j),
        ],
    )
    def test_complex_multiplication(
        self,
        i_val: complex,
        z_val: complex,
        v_val: complex,
    ) -> None:
        v = calculate_voltage_from_current_and_impedance(
            eps=TEST_EPS,
            max_mag=TEST_MAX_MAG,
            current=ArrayComplexCurrentDto(value=np.array([i_val]), unit="A"),
            impedance=ArrayComplexImpedanceDto(
                value=np.array([z_val]), unit="Ω"
            ),
        )
        np.testing.assert_allclose(v.value, [v_val])

    def test_raises_on_shape_mismatch(self) -> None:
        with pytest.raises(ValueError, match="配列形状が一致しません"):
            calculate_voltage_from_current_and_impedance(
                eps=TEST_EPS,
                max_mag=TEST_MAX_MAG,
                current=ArrayComplexCurrentDto(
                    value=np.array([1.0, 2.0]), unit="A"
                ),
                impedance=ArrayComplexImpedanceDto(
                    value=np.array([1.0 + 0j]), unit="Ω"
                ),
            )


class TestVoltageFromCurrentAndAdmittance:
    """V = I / Y。"""

    def test_returns_quotient(self) -> None:
        i = ArrayComplexCurrentDto(value=np.array([10.0 + 0j]), unit="A")
        y = ArrayComplexAdmittanceDto(value=np.array([2.0 + 0j]), unit="S")
        v = calculate_voltage_from_current_and_admittance(
            eps=TEST_EPS, max_mag=TEST_MAX_MAG, current=i, admittance=y
        )
        np.testing.assert_allclose(v.value, [5.0 + 0j])

    def test_raises_on_shape_mismatch(self) -> None:
        with pytest.raises(ValueError, match="配列形状が一致しません"):
            calculate_voltage_from_current_and_admittance(
                eps=TEST_EPS,
                max_mag=TEST_MAX_MAG,
                current=ArrayComplexCurrentDto(
                    value=np.array([1.0 + 0j]), unit="A"
                ),
                admittance=ArrayComplexAdmittanceDto(
                    value=np.array([1.0, 2.0]), unit="S"
                ),
            )


class TestCurrentFromVoltageAndImpedance:
    """I = V / Z。"""

    def test_returns_quotient(self) -> None:
        v = ArrayComplexVoltageDto(value=np.array([10.0 + 0j]), unit="V")
        z = ArrayComplexImpedanceDto(value=np.array([2.0 + 0j]), unit="Ω")
        i = calculate_current_from_voltage_and_impedance(
            eps=TEST_EPS, max_mag=TEST_MAX_MAG, voltage=v, impedance=z
        )
        np.testing.assert_allclose(i.value, [5.0 + 0j])
        assert i.get_unit() == "A"

    def test_raises_on_shape_mismatch(self) -> None:
        with pytest.raises(ValueError, match="配列形状が一致しません"):
            calculate_current_from_voltage_and_impedance(
                eps=TEST_EPS,
                max_mag=TEST_MAX_MAG,
                voltage=ArrayComplexVoltageDto(
                    value=np.array([1.0, 2.0]), unit="V"
                ),
                impedance=ArrayComplexImpedanceDto(
                    value=np.array([1.0 + 0j]), unit="Ω"
                ),
            )


class TestCurrentFromVoltageAndAdmittance:
    """I = V · Y。"""

    def test_returns_product(self) -> None:
        v = ArrayComplexVoltageDto(value=np.array([10.0 + 0j]), unit="V")
        y = ArrayComplexAdmittanceDto(value=np.array([0.5 + 0j]), unit="S")
        i = calculate_current_from_voltage_and_admittance(
            eps=TEST_EPS, max_mag=TEST_MAX_MAG, voltage=v, admittance=y
        )
        np.testing.assert_allclose(i.value, [5.0 + 0j])

    def test_raises_on_shape_mismatch(self) -> None:
        with pytest.raises(ValueError, match="配列形状が一致しません"):
            calculate_current_from_voltage_and_admittance(
                eps=TEST_EPS,
                max_mag=TEST_MAX_MAG,
                voltage=ArrayComplexVoltageDto(
                    value=np.array([1.0 + 0j]), unit="V"
                ),
                admittance=ArrayComplexAdmittanceDto(
                    value=np.array([1.0, 2.0]), unit="S"
                ),
            )


class TestOhmsLawNumericalStability:
    """極小・極大入力でイベントが記録され、結果がクランプされること。"""

    def test_voltage_calc_records_extreme_event(self) -> None:
        """電流が極小 → ``OHMS_LAW_VOLTAGE_IMPEDANCE_INPUT_EXTREME``。"""
        with numerical_stability_scope() as acc:
            calculate_voltage_from_current_and_impedance(
                eps=TEST_EPS,
                max_mag=TEST_MAX_MAG,
                current=ArrayComplexCurrentDto(
                    value=np.array([0.0 + 0j]), unit="A"
                ),
                impedance=ArrayComplexImpedanceDto(
                    value=np.array([1.0 + 0j]), unit="Ω"
                ),
            )
        assert_event_counts(
            acc,
            (event_codes.OHMS_LAW_VOLTAGE_IMPEDANCE_INPUT_EXTREME, 1),
        )

    def test_current_calc_records_extreme_when_impedance_is_zero(
        self,
    ) -> None:
        """インピーダンスが極小 → I は max_mag にクランプ。"""
        with numerical_stability_scope() as acc:
            result = calculate_current_from_voltage_and_impedance(
                eps=TEST_EPS,
                max_mag=TEST_MAX_MAG,
                voltage=ArrayComplexVoltageDto(
                    value=np.array([10.0 + 0j]), unit="V"
                ),
                impedance=ArrayComplexImpedanceDto(
                    value=np.array([0.0 + 0j]), unit="Ω"
                ),
            )
        assert_event_counts(
            acc,
            (event_codes.OHMS_LAW_CURRENT_IMPEDANCE_INPUT_EXTREME, 1),
        )
        # 短絡近傍 → I = max_mag
        assert np.abs(result.value[0]) == pytest.approx(1e12)

    def test_no_event_when_inputs_are_normal(self) -> None:
        with numerical_stability_scope() as acc:
            calculate_voltage_from_current_and_impedance(
                eps=TEST_EPS,
                max_mag=TEST_MAX_MAG,
                current=ArrayComplexCurrentDto(
                    value=np.array([1.0 + 0j]), unit="A"
                ),
                impedance=ArrayComplexImpedanceDto(
                    value=np.array([1.0 + 0j]), unit="Ω"
                ),
            )
        assert_no_events(acc)
