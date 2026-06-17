"""``physics.electrical.immittance.impedance_converter`` の単体テスト。

インピーダンス生成 4 関数を検証する:
    - impedance_from_admittance: Z = 1/Y
    - impedance_from_resistance_and_frequency: Z = R (実数)
    - impedance_from_inductance_and_frequency: Z = jωL
    - impedance_from_capacitance_and_frequency: Z = -j/(ωC)
"""

from __future__ import annotations

import numpy as np
import pytest

from im_cable_system.engine.domain.physics.electrical import (
    admittance_from_impedance,
    impedance_from_admittance,
    impedance_from_capacitance_and_frequency,
    impedance_from_inductance_and_frequency,
    impedance_from_resistance_and_frequency,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexAdmittanceDto,
    ArrayFrequencyDto,
    FloatCapacitanceDto,
    FloatInductanceDto,
    FloatResistanceDto,
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

_EPS = 1e-12
_MAX_MAG = 1.0 / _EPS


def _freq(values: np.ndarray) -> ArrayFrequencyDto:
    return ArrayFrequencyDto(value=values, unit="Hz")


class TestImpedanceFromAdmittance:
    """Z = 1/Y。"""

    def test_returns_reciprocal_for_real_admittance(self) -> None:
        y = ArrayComplexAdmittanceDto(value=np.array([0.5 + 0j]), unit="S")
        z = impedance_from_admittance(
            eps=TEST_EPS, max_mag=TEST_MAX_MAG, admittance=y
        )
        np.testing.assert_allclose(z.value, [2.0 + 0j])
        assert z.get_unit() == "Ω"

    def test_complex_admittance_round_trip(self) -> None:
        """``admittance_from_impedance`` との往復で値が戻る。"""
        y0 = ArrayComplexAdmittanceDto(value=np.array([2.0 + 1.0j]), unit="S")
        z = impedance_from_admittance(
            eps=TEST_EPS, max_mag=TEST_MAX_MAG, admittance=y0
        )
        y = admittance_from_impedance(
            eps=TEST_EPS, max_mag=TEST_MAX_MAG, impedance=z
        )
        np.testing.assert_allclose(y.value, y0.value)


class TestImpedanceFromAdmittanceClamp:
    """極小・極大アドミタンスのクランプ挙動。"""

    def test_small_admittance_clamps_to_max_impedance(self) -> None:
        with numerical_stability_scope() as acc:
            z = impedance_from_admittance(
                eps=TEST_EPS,
                max_mag=TEST_MAX_MAG,
                admittance=ArrayComplexAdmittanceDto(
                    value=np.array([0.0 + 0j]), unit="S"
                ),
            )
        assert np.abs(z.value[0]) == pytest.approx(_MAX_MAG)
        assert_event_counts(
            acc, (event_codes.ADMITTANCE_TOO_SMALL_FOR_IMPEDANCE, 1)
        )

    def test_no_event_with_normal_admittance(self) -> None:
        with numerical_stability_scope() as acc:
            impedance_from_admittance(
                eps=TEST_EPS,
                max_mag=TEST_MAX_MAG,
                admittance=ArrayComplexAdmittanceDto(
                    value=np.array([1.0 + 0j]), unit="S"
                ),
            )
        assert_no_events(acc)


class TestImpedanceFromResistanceAndFrequency:
    """純抵抗インピーダンスは周波数によらず一定。"""

    def test_broadcasts_resistance_to_frequency_shape(self) -> None:
        z = impedance_from_resistance_and_frequency(
            eps=TEST_EPS,
            max_mag=TEST_MAX_MAG,
            resistance=FloatResistanceDto(value=10.0, unit="Ω"),
            frequency=_freq(np.array([50.0, 60.0, 70.0])),
        )
        np.testing.assert_allclose(z.value, [10.0 + 0j, 10.0 + 0j, 10.0 + 0j])
        assert z.get_unit() == "Ω"

    def test_zero_resistance_clamps_and_records_event(self) -> None:
        with numerical_stability_scope() as acc:
            z = impedance_from_resistance_and_frequency(
                eps=TEST_EPS,
                max_mag=TEST_MAX_MAG,
                resistance=FloatResistanceDto(value=0.0, unit="Ω"),
                frequency=_freq(np.array([50.0])),
            )
        assert np.abs(z.value[0]) == pytest.approx(_EPS)
        assert_event_counts(acc, (event_codes.RESISTANCE_TOO_SMALL, 1))


class TestImpedanceFromInductanceAndFrequency:
    """Z = jωL = j · 2π · f · L。"""

    def test_returns_pure_imaginary_jwl(self) -> None:
        f = 50.0
        l_val = 0.01  # 10 mH
        z = impedance_from_inductance_and_frequency(
            eps=TEST_EPS,
            max_mag=TEST_MAX_MAG,
            inductance=FloatInductanceDto(value=l_val, unit="H"),
            frequency=_freq(np.array([f])),
        )
        expected = 1j * 2.0 * np.pi * f * l_val
        np.testing.assert_allclose(z.value, [expected])

    @pytest.mark.parametrize("unit, factor", [("H", 1.0), ("mH", 1e-3)])
    def test_unit_conversion(self, unit: str, factor: float) -> None:
        z = impedance_from_inductance_and_frequency(
            eps=TEST_EPS,
            max_mag=TEST_MAX_MAG,
            inductance=FloatInductanceDto(value=10.0, unit=unit),
            frequency=_freq(np.array([50.0])),
        )
        expected = 1j * 2.0 * np.pi * 50.0 * (10.0 * factor)
        np.testing.assert_allclose(z.value, [expected])

    def test_too_small_inductance_clamps_to_eps(self) -> None:
        with numerical_stability_scope() as acc:
            z = impedance_from_inductance_and_frequency(
                eps=TEST_EPS,
                max_mag=TEST_MAX_MAG,
                inductance=FloatInductanceDto(value=0.0, unit="H"),
                frequency=_freq(np.array([50.0, 60.0])),
            )
        np.testing.assert_allclose(np.abs(z.value), [_EPS, _EPS])
        assert_event_counts(acc, (event_codes.INDUCTANCE_TOO_SMALL, 1))


class TestImpedanceFromCapacitanceAndFrequency:
    """Z = -j / (ωC)。"""

    def test_returns_negative_imaginary_inverse_wc(self) -> None:
        f = 50.0
        c_val = 1e-6  # 1 µF
        z = impedance_from_capacitance_and_frequency(
            eps=TEST_EPS,
            max_mag=TEST_MAX_MAG,
            capacitance=FloatCapacitanceDto(value=c_val, unit="F"),
            frequency=_freq(np.array([f])),
        )
        expected = -1j / (2.0 * np.pi * f * c_val)
        np.testing.assert_allclose(z.value, [expected])

    def test_too_small_capacitance_clamps_to_max(self) -> None:
        with numerical_stability_scope() as acc:
            z = impedance_from_capacitance_and_frequency(
                eps=TEST_EPS,
                max_mag=TEST_MAX_MAG,
                capacitance=FloatCapacitanceDto(value=0.0, unit="F"),
                frequency=_freq(np.array([50.0])),
            )
        assert np.abs(z.value[0]) == pytest.approx(_MAX_MAG)
        assert_event_counts(acc, (event_codes.CAPACITANCE_TOO_SMALL, 1))
