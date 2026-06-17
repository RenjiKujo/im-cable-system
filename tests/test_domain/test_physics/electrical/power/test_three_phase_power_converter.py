"""``physics.electrical.power.three_phase_power_converter`` の単体テスト。

``to_three_phase_power_from_phase`` / ``to_three_phase_power_from_line`` を検証する。
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from im_cable_system.engine.domain.physics.electrical import (
    to_three_phase_power_from_line,
    to_three_phase_power_from_phase,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexCurrentDto,
    ArrayComplexPowerDto,
    ArrayComplexVoltageDto,
)


class TestToThreePhasePowerFromPhase:
    """``S_3phase = 3 · S_1phase``。"""

    @pytest.mark.parametrize(
        "value",
        [
            np.array([10.0 + 0j]),
            np.array([5.0 + 3.0j, -1.0 - 2.0j]),
        ],
    )
    def test_returns_three_times_single_phase(self, value: np.ndarray) -> None:
        single = ArrayComplexPowerDto(value=value, unit="VA")
        total = to_three_phase_power_from_phase(single_phase_power_dto=single)
        np.testing.assert_allclose(total.value, 3.0 * value)
        assert total.get_unit() == "VA"

    def test_preserves_multi_dimensional_shape(self) -> None:
        single = ArrayComplexPowerDto(
            value=np.ones((2, 3), dtype=np.complex128), unit="VA"
        )
        total = to_three_phase_power_from_phase(single_phase_power_dto=single)
        assert total.value.shape == (2, 3)
        np.testing.assert_allclose(total.value, 3.0 * np.ones((2, 3)))


class TestToThreePhasePowerFromLine:
    """``S_3phase = √3 · V_line · conj(I_line)``。"""

    def test_returns_sqrt3_times_v_conj_i(self) -> None:
        # 単純な実数: V_line = √3 · 100, I_line = 1 → S = √3 · √3 · 100 = 300
        v = ArrayComplexVoltageDto(
            value=np.array([math.sqrt(3.0) * 100.0 + 0j]), unit="V"
        )
        i = ArrayComplexCurrentDto(value=np.array([1.0 + 0j]), unit="A")
        total = to_three_phase_power_from_line(line_voltage=v, line_current=i)
        np.testing.assert_allclose(total.value, [300.0 + 0j])
        assert total.get_unit() == "VA"

    def test_takes_conjugate_of_current(self) -> None:
        v = ArrayComplexVoltageDto(value=np.array([1.0 + 0j]), unit="V")
        i = ArrayComplexCurrentDto(value=np.array([2.0 + 3.0j]), unit="A")
        total = to_three_phase_power_from_line(line_voltage=v, line_current=i)
        expected = math.sqrt(3.0) * (1.0 + 0j) * (2.0 - 3.0j)
        np.testing.assert_allclose(total.value, [expected])

    def test_raises_on_shape_mismatch(self) -> None:
        with pytest.raises(ValueError, match="配列形状が一致しません"):
            to_three_phase_power_from_line(
                line_voltage=ArrayComplexVoltageDto(
                    value=np.array([1.0, 2.0]), unit="V"
                ),
                line_current=ArrayComplexCurrentDto(
                    value=np.array([1.0 + 0j]), unit="A"
                ),
            )
