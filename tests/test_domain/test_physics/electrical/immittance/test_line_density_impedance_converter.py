"""``physics.electrical.immittance.line_density_impedance_converter`` の単体テスト。

線密度（単位長あたり）と長さからインピーダンスを計算する 2 関数を検証する:
    - impedance_from_conductor_line_density: R + jωL（直列）
    - impedance_from_ground_line_density: R ∥ (1/(jωC))（並列）
"""

from __future__ import annotations

import numpy as np
import pytest

from im_cable_system.engine.domain.physics.electrical import (
    impedance_from_conductor_line_density,
    impedance_from_ground_line_density,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayFrequencyDto,
    FloatCapacitancePerLengthDto,
    FloatInductancePerLengthDto,
    FloatLengthDto,
    FloatResistanceLengthDto,
    FloatResistancePerLengthDto,
)
from tests.test_domain._domain_helpers import (
    TEST_EPS,
    TEST_MAX_MAG,
)


def _freq(values: np.ndarray) -> ArrayFrequencyDto:
    return ArrayFrequencyDto(value=values, unit="Hz")


class TestImpedanceFromConductorLineDensity:
    """``R_total + jω L_total``（直列）。"""

    def test_real_part_equals_resistance_times_length(self) -> None:
        z = impedance_from_conductor_line_density(
            eps=TEST_EPS,
            max_mag=TEST_MAX_MAG,
            resistance_per_length=FloatResistancePerLengthDto(
                value=0.1, unit="Ω/m"
            ),
            inductance_per_length=FloatInductancePerLengthDto(
                value=1e-6, unit="H/m"
            ),
            length=FloatLengthDto(value=100.0, unit="m"),
            frequency=_freq(np.array([50.0])),
        )
        # R_total = 0.1 × 100 = 10.0
        # L_total = 1e-6 × 100 = 1e-4
        # Z = 10 + j · 2π · 50 · 1e-4
        expected_real = 10.0
        expected_imag = 2.0 * np.pi * 50.0 * 1e-4
        np.testing.assert_allclose(z.value.real, [expected_real])
        np.testing.assert_allclose(z.value.imag, [expected_imag])

    def test_broadcasts_to_frequency_shape(self) -> None:
        z = impedance_from_conductor_line_density(
            eps=TEST_EPS,
            max_mag=TEST_MAX_MAG,
            resistance_per_length=FloatResistancePerLengthDto(
                value=0.1, unit="Ω/m"
            ),
            inductance_per_length=FloatInductancePerLengthDto(
                value=1e-6, unit="H/m"
            ),
            length=FloatLengthDto(value=100.0, unit="m"),
            frequency=_freq(np.array([50.0, 60.0, 70.0])),
        )
        assert z.value.shape == (3,)

    def test_raises_on_zero_length(self) -> None:
        """長さ 0 は ``ValueError``（DTO 側は負値・線密度の負値を別途検出）。"""
        with pytest.raises(ValueError, match="長さが0以下"):
            impedance_from_conductor_line_density(
                eps=TEST_EPS,
                max_mag=TEST_MAX_MAG,
                resistance_per_length=FloatResistancePerLengthDto(
                    value=0.1, unit="Ω/m"
                ),
                inductance_per_length=FloatInductancePerLengthDto(
                    value=1e-6, unit="H/m"
                ),
                length=FloatLengthDto(value=0.0, unit="m"),
                frequency=_freq(np.array([50.0])),
            )


class TestImpedanceFromGroundLineDensity:
    """``R || (1/(jωC))``（並列）。"""

    def test_basic_combination_at_low_capacitance(self) -> None:
        """非常に小さい C → 並列インピーダンスは R 支配（≈ R）。"""
        r_length_value = 1e6  # Ω·m
        length = 10.0  # m
        # R_total = R·m / length = 1e6 / 10 = 1e5 Ω
        # C_total = 1e-15 × 10 = 1e-14 F → 1/(ωC) ≫ R → R || (1/(ωC)) ≈ R
        z = impedance_from_ground_line_density(
            eps=TEST_EPS,
            max_mag=TEST_MAX_MAG,
            resistance_length=FloatResistanceLengthDto(
                value=r_length_value, unit="Ω*m"
            ),
            capacitance_per_length=FloatCapacitancePerLengthDto(
                value=1e-15, unit="F/m"
            ),
            length=FloatLengthDto(value=length, unit="m"),
            frequency=_freq(np.array([50.0])),
        )
        # R_total = 1e5、ωC = 2π·50·1e-14 = 約3.14e-12 → 1/(ωC) ≈ 3.18e11
        # R || X_c ≈ R = 1e5
        assert np.abs(z.value[0]) == pytest.approx(1e5, rel=1e-3)

    def test_raises_on_zero_length(self) -> None:
        with pytest.raises(ValueError, match="長さが0以下"):
            impedance_from_ground_line_density(
                eps=TEST_EPS,
                max_mag=TEST_MAX_MAG,
                resistance_length=FloatResistanceLengthDto(
                    value=1.0, unit="Ω*m"
                ),
                capacitance_per_length=FloatCapacitancePerLengthDto(
                    value=1e-12, unit="F/m"
                ),
                length=FloatLengthDto(value=0.0, unit="m"),
                frequency=_freq(np.array([50.0])),
            )

    def test_custom_eps_is_propagated_to_clamp(self) -> None:
        """注入した eps が内部のクランプに伝播することを検証する。

        R_total（=1e-5 Ω）は既定 eps(1e-12) では極小扱いされないが、
        custom eps(1e-3) では極小としてクランプされ、容量側（極大）との
        並列合成は極小（eps）支配となる。
        """
        # R_total = 1e-4 / 10 = 1e-5 Ω、C_total = 1e-8 F
        custom_eps = 1e-3
        z = impedance_from_ground_line_density(
            resistance_length=FloatResistanceLengthDto(value=1e-4, unit="Ω*m"),
            capacitance_per_length=FloatCapacitancePerLengthDto(
                value=1e-9, unit="F/m"
            ),
            length=FloatLengthDto(value=10.0, unit="m"),
            frequency=_freq(np.array([50.0])),
            eps=custom_eps,
            max_mag=1.0 / custom_eps,
        )
        assert np.abs(z.value[0]) == pytest.approx(custom_eps, rel=1e-6)
