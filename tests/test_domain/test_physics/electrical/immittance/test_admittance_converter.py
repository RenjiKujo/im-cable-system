"""``physics.electrical.immittance.admittance_converter`` の単体テスト。

アドミタンス生成 4 関数を検証する:
    - admittance_from_impedance: Y = 1/Z
    - admittance_from_conductance_and_frequency: Y = G (実数)
    - admittance_from_inductance_and_frequency: Y = -j/(ωL)
    - admittance_from_capacitance_and_frequency: Y = jωC
"""

from __future__ import annotations

import numpy as np
import pytest

from im_cable_system.engine.domain.physics.electrical import (
    admittance_from_capacitance_and_frequency,
    admittance_from_conductance_and_frequency,
    admittance_from_impedance,
    admittance_from_inductance_and_frequency,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexImpedanceDto,
    ArrayFrequencyDto,
    FloatCapacitanceDto,
    FloatConductanceDto,
    FloatInductanceDto,
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


class TestAdmittanceFromImpedance:
    """Y = 1/Z。"""

    def test_returns_reciprocal_for_real_impedance(self) -> None:
        z = ArrayComplexImpedanceDto(value=np.array([2.0 + 0j]), unit="Ω")
        y = admittance_from_impedance(
            eps=TEST_EPS, max_mag=TEST_MAX_MAG, impedance=z
        )
        np.testing.assert_allclose(y.value, [0.5 + 0j])
        assert y.get_unit() == "S"

    def test_small_impedance_clamps_to_max_admittance(self) -> None:
        with numerical_stability_scope() as acc:
            y = admittance_from_impedance(
                eps=TEST_EPS,
                max_mag=TEST_MAX_MAG,
                impedance=ArrayComplexImpedanceDto(
                    value=np.array([0.0 + 0j]), unit="Ω"
                ),
            )
        assert np.abs(y.value[0]) == pytest.approx(_MAX_MAG)
        assert_event_counts(
            acc, (event_codes.IMPEDANCE_TOO_SMALL_FOR_ADMITTANCE, 1)
        )

    def test_no_event_with_normal_impedance(self) -> None:
        with numerical_stability_scope() as acc:
            admittance_from_impedance(
                eps=TEST_EPS,
                max_mag=TEST_MAX_MAG,
                impedance=ArrayComplexImpedanceDto(
                    value=np.array([1.0 + 0j]), unit="Ω"
                ),
            )
        assert_no_events(acc)


class TestAdmittanceFromConductanceAndFrequency:
    """純コンダクタンスは周波数によらず一定。"""

    def test_broadcasts_to_frequency_shape(self) -> None:
        y = admittance_from_conductance_and_frequency(
            eps=TEST_EPS,
            max_mag=TEST_MAX_MAG,
            conductance=FloatConductanceDto(value=0.1, unit="S"),
            frequency=_freq(np.array([50.0, 60.0])),
        )
        np.testing.assert_allclose(y.value, [0.1 + 0j, 0.1 + 0j])

    def test_too_small_conductance_clamps_to_eps(self) -> None:
        with numerical_stability_scope() as acc:
            y = admittance_from_conductance_and_frequency(
                eps=TEST_EPS,
                max_mag=TEST_MAX_MAG,
                conductance=FloatConductanceDto(value=0.0, unit="S"),
                frequency=_freq(np.array([50.0])),
            )
        assert np.abs(y.value[0]) == pytest.approx(_EPS)
        assert_event_counts(acc, (event_codes.CONDUCTANCE_TOO_SMALL, 1))


class TestAdmittanceFromInductanceAndFrequency:
    """Y = -j / (ωL)。"""

    def test_returns_negative_imaginary_inverse_wl(self) -> None:
        f = 50.0
        l_val = 0.01
        y = admittance_from_inductance_and_frequency(
            eps=TEST_EPS,
            max_mag=TEST_MAX_MAG,
            inductance=FloatInductanceDto(value=l_val, unit="H"),
            frequency=_freq(np.array([f])),
        )
        expected = -1j / (2.0 * np.pi * f * l_val)
        np.testing.assert_allclose(y.value, [expected])

    def test_too_small_inductance_clamps_to_max(self) -> None:
        with numerical_stability_scope() as acc:
            y = admittance_from_inductance_and_frequency(
                eps=TEST_EPS,
                max_mag=TEST_MAX_MAG,
                inductance=FloatInductanceDto(value=0.0, unit="H"),
                frequency=_freq(np.array([50.0])),
            )
        assert np.abs(y.value[0]) == pytest.approx(_MAX_MAG)
        assert_event_counts(acc, (event_codes.INDUCTANCE_TOO_SMALL, 1))


class TestAdmittanceFromCapacitanceAndFrequency:
    """Y = jωC。"""

    def test_returns_positive_imaginary_wc(self) -> None:
        f = 50.0
        c_val = 1e-6
        y = admittance_from_capacitance_and_frequency(
            eps=TEST_EPS,
            max_mag=TEST_MAX_MAG,
            capacitance=FloatCapacitanceDto(value=c_val, unit="F"),
            frequency=_freq(np.array([f])),
        )
        expected = 1j * 2.0 * np.pi * f * c_val
        np.testing.assert_allclose(y.value, [expected])

    def test_too_small_capacitance_clamps_to_eps(self) -> None:
        with numerical_stability_scope() as acc:
            y = admittance_from_capacitance_and_frequency(
                eps=TEST_EPS,
                max_mag=TEST_MAX_MAG,
                capacitance=FloatCapacitanceDto(value=0.0, unit="F"),
                frequency=_freq(np.array([50.0])),
            )
        assert np.abs(y.value[0]) == pytest.approx(_EPS)
        assert_event_counts(acc, (event_codes.CAPACITANCE_TOO_SMALL, 1))
