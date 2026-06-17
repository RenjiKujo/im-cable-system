"""``physics.electrical.power.three_phase_power_builder`` の単体テスト。

``three_phase_power_from_voltage_and_current_phase`` 等の dict 操作を含む
ビルダー群を検証する。
"""

from __future__ import annotations

import numpy as np
import pytest

from im_cable_system.engine.domain.physics.electrical import (
    sum_power_dict_values,
    three_phase_power_dict_from_voltage_and_current_phase_dict,
    three_phase_power_from_voltage_and_current_phase,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexCurrentDto,
    ArrayComplexPowerDto,
    ArrayComplexVoltageDto,
)


class TestThreePhasePowerFromVoltageAndCurrentPhase:
    """``3 · V · conj(I)``。"""

    def test_returns_three_times_v_conj_i(self) -> None:
        v = ArrayComplexVoltageDto(value=np.array([10.0 + 0j]), unit="V")
        i = ArrayComplexCurrentDto(value=np.array([2.0 - 1.0j]), unit="A")
        # S_1phase = 10 * (2 + 1j) = 20 + 10j
        # S_3phase = 3 * S_1phase = 60 + 30j
        total = three_phase_power_from_voltage_and_current_phase(
            voltage=v, current=i
        )
        np.testing.assert_allclose(total.value, [60.0 + 30.0j])
        assert total.get_unit() == "VA"


class TestThreePhasePowerDictBuilder:
    """key ごとに ``3 · V · conj(I)`` を計算した dict を返す。"""

    def test_builds_dict_with_same_keys(self) -> None:
        voltage_dict = {
            "primary": ArrayComplexVoltageDto(
                value=np.array([10.0 + 0j]), unit="V"
            ),
            "secondary": ArrayComplexVoltageDto(
                value=np.array([5.0 + 0j]), unit="V"
            ),
        }
        current_dict = {
            "primary": ArrayComplexCurrentDto(
                value=np.array([2.0 + 0j]), unit="A"
            ),
            "secondary": ArrayComplexCurrentDto(
                value=np.array([1.0 + 0j]), unit="A"
            ),
        }
        power_dict = three_phase_power_dict_from_voltage_and_current_phase_dict(
            voltage_dict=voltage_dict, current_dict=current_dict
        )
        assert set(power_dict.keys()) == {"primary", "secondary"}
        np.testing.assert_allclose(power_dict["primary"].value, [60.0 + 0j])
        np.testing.assert_allclose(power_dict["secondary"].value, [15.0 + 0j])

    def test_raises_when_keys_mismatch(self) -> None:
        with pytest.raises(ValueError, match="キーが一致しません"):
            three_phase_power_dict_from_voltage_and_current_phase_dict(
                voltage_dict={
                    "a": ArrayComplexVoltageDto(
                        value=np.array([1.0 + 0j]), unit="V"
                    )
                },
                current_dict={
                    "b": ArrayComplexCurrentDto(
                        value=np.array([1.0 + 0j]), unit="A"
                    )
                },
            )


class TestSumPowerDictValues:
    """複数 dict の全 value を合算する。"""

    def test_sums_all_values_across_dicts(self) -> None:
        d1 = {
            "x": ArrayComplexPowerDto(value=np.array([1.0 + 0j]), unit="VA"),
            "y": ArrayComplexPowerDto(value=np.array([2.0 + 0j]), unit="VA"),
        }
        d2 = {
            "z": ArrayComplexPowerDto(value=np.array([3.0 + 0j]), unit="VA"),
        }
        total = sum_power_dict_values(power_dicts=[d1, d2])
        np.testing.assert_allclose(total.value, [6.0 + 0j])
        assert total.get_unit() == "VA"

    def test_raises_when_all_dicts_are_empty(self) -> None:
        with pytest.raises(ValueError, match="損失電力の合計対象が空"):
            sum_power_dict_values(power_dicts=[{}, {}])
