"""``convert_ratio_columns_to_absolute`` の単体テスト。

EstimateParams 経路の比率→絶対単位変換ヘルパが、

- ``power[-]`` × 名盤値（``W`` 換算）→ ``power[W]``
- ``current[%]`` × 名盤値（``A`` 換算） / 100 → ``current[A]``
- 既に絶対単位（``W`` / ``A`` / ``kW`` / ``kA`` 等）なら素通し
- 名盤の単位がサポート外なら ``ValueError``

を満たすことを、Assembler を介さず直接固定する。
"""

from __future__ import annotations

from typing import Any, cast

import numpy as np
import pytest

from im_cable_system.engine.algorithm.input_algorithm.assemble_input_dto.estimate_params.perf_curve_unit_converter import (  # noqa: E501
    convert_ratio_columns_to_absolute,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data.data_class.im_loaded_data import (  # noqa: E501
    ImNameplateLoadedData,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data.data_class.im_performance_curve_loaded_data import (  # noqa: E501
    ImPerformanceCurveLoadedData,
)


def _make_nameplate(
    *,
    voltage: float = 200.0,
    voltage_unit: str = "V",
    current: float = 25.0,
    current_unit: str = "A",
    power: float = 3711.0,
    power_unit: str = "W",
    frequency: float = 50.0,
    frequency_unit: str = "Hz",
) -> ImNameplateLoadedData:
    return ImNameplateLoadedData(
        voltage=voltage,
        voltage_unit=voltage_unit,
        current=current,
        current_unit=current_unit,
        power=power,
        power_unit=power_unit,
        frequency=frequency,
        frequency_unit=frequency_unit,
    )


def _make_curve_loaded(
    *,
    power: np.ndarray | None = None,
    power_unit: str | None = None,
    current: np.ndarray | None = None,
    current_unit: str | None = None,
    torque: np.ndarray | None = None,
    torque_unit: str | None = None,
) -> ImPerformanceCurveLoadedData:
    return ImPerformanceCurveLoadedData(
        name="EstimateParamsConverterTest",
        poles=4.0,
        supply_frequency=50.0,
        supply_frequency_unit="Hz",
        supply_voltage=200.0,
        supply_voltage_unit="V",
        rotational_speed=np.array([1500.0, 1490.0, 1480.0], dtype=np.float64),
        rotational_speed_unit="rpm",
        power=power,
        power_unit=power_unit,
        current=current,
        current_unit=current_unit,
        power_factor=None,
        power_factor_unit=None,
        efficiency=None,
        efficiency_unit=None,
        torque=torque,
        torque_unit=torque_unit,
    )


def _assert_optional_array_allclose(
    actual: np.ndarray | None,
    expected: np.ndarray,
    *,
    rtol: float,
) -> None:
    """optional 系列が存在することを確認してから近似一致を検証する。"""
    if actual is None:
        raise AssertionError("actual array must not be None")
    np.testing.assert_allclose(
        cast(Any, actual), cast(Any, expected), rtol=rtol
    )


class TestConvertRatioPowerToAbsolute:
    """``power[-]`` × 名盤W → ``power[W]`` の固定。"""

    def test_dash_unit_scales_by_nameplate_power_w(self) -> None:
        """``power_unit='-'`` のときは ``ratio × nameplate.power[W]``。"""
        nameplate = _make_nameplate(power=3711.0, power_unit="W")
        pc = _make_curve_loaded(
            power=np.array([0.0, 0.5, 1.0], dtype=np.float64),
            power_unit="-",
        )
        converted = convert_ratio_columns_to_absolute(pc, nameplate)
        assert converted.power_unit == "W"
        _assert_optional_array_allclose(
            converted.power,
            np.array([0.0, 1855.5, 3711.0], dtype=np.float64),
            rtol=1e-12,
        )

    def test_bracket_dash_unit_also_scales(self) -> None:
        """``power_unit='[-]'`` （角括弧付き）でも変換される。"""
        nameplate = _make_nameplate(power=3711.0, power_unit="W")
        pc = _make_curve_loaded(
            power=np.array([0.1, 0.2], dtype=np.float64),
            power_unit="[-]",
        )
        converted = convert_ratio_columns_to_absolute(pc, nameplate)
        assert converted.power_unit == "W"
        _assert_optional_array_allclose(
            converted.power,
            np.array([371.1, 742.2], dtype=np.float64),
            rtol=1e-12,
        )

    def test_nameplate_in_kw_is_normalized_to_w_before_scaling(self) -> None:
        """名盤が ``kW`` でも、SI (``W``) に揃えてから掛ける。"""
        nameplate = _make_nameplate(power=3.711, power_unit="kW")
        pc = _make_curve_loaded(
            power=np.array([0.5, 1.0], dtype=np.float64),
            power_unit="-",
        )
        converted = convert_ratio_columns_to_absolute(pc, nameplate)
        assert converted.power_unit == "W"
        _assert_optional_array_allclose(
            converted.power,
            np.array([1855.5, 3711.0], dtype=np.float64),
            rtol=1e-12,
        )


class TestConvertRatioCurrentToAbsolute:
    """``current[%]`` × 名盤A / 100 → ``current[A]`` の固定。"""

    def test_percent_unit_scales_by_nameplate_current_a_over_100(self) -> None:
        nameplate = _make_nameplate(current=25.0, current_unit="A")
        pc = _make_curve_loaded(
            current=np.array([0.0, 50.0, 100.0], dtype=np.float64),
            current_unit="%",
        )
        converted = convert_ratio_columns_to_absolute(pc, nameplate)
        assert converted.current_unit == "A"
        _assert_optional_array_allclose(
            converted.current,
            np.array([0.0, 12.5, 25.0], dtype=np.float64),
            rtol=1e-12,
        )

    def test_bracket_percent_unit_also_scales(self) -> None:
        nameplate = _make_nameplate(current=25.0, current_unit="A")
        pc = _make_curve_loaded(
            current=np.array([12.0, 24.0], dtype=np.float64),
            current_unit="[%]",
        )
        converted = convert_ratio_columns_to_absolute(pc, nameplate)
        assert converted.current_unit == "A"
        _assert_optional_array_allclose(
            converted.current,
            np.array([3.0, 6.0], dtype=np.float64),
            rtol=1e-12,
        )

    def test_nameplate_in_ka_is_normalized_to_a_before_scaling(self) -> None:
        """名盤が ``kA`` でも、SI (``A``) に揃えてから掛ける。"""
        nameplate = _make_nameplate(current=0.025, current_unit="kA")
        pc = _make_curve_loaded(
            current=np.array([50.0, 100.0], dtype=np.float64),
            current_unit="%",
        )
        converted = convert_ratio_columns_to_absolute(pc, nameplate)
        assert converted.current_unit == "A"
        _assert_optional_array_allclose(
            converted.current,
            np.array([12.5, 25.0], dtype=np.float64),
            rtol=1e-12,
        )


class TestConvertAbsoluteUnitsArePassThrough:
    """既に絶対単位の列はスケーリングされず、単位文字列も保たれる。"""

    def test_power_w_pass_through(self) -> None:
        nameplate = _make_nameplate(power=3711.0, power_unit="W")
        original_power = np.array([100.0, 200.0, 300.0], dtype=np.float64)
        pc = _make_curve_loaded(power=original_power, power_unit="W")
        converted = convert_ratio_columns_to_absolute(pc, nameplate)
        assert converted.power_unit == "W"
        _assert_optional_array_allclose(
            converted.power,
            original_power,
            rtol=0.0,
        )

    def test_power_kw_pass_through_unit_preserved(self) -> None:
        """``kW`` も比率ではないので変換しない（単位文字列を保つ）。"""
        nameplate = _make_nameplate(power=3711.0, power_unit="W")
        pc = _make_curve_loaded(
            power=np.array([0.1, 0.2, 0.3], dtype=np.float64),
            power_unit="kW",
        )
        converted = convert_ratio_columns_to_absolute(pc, nameplate)
        assert converted.power_unit == "kW"
        _assert_optional_array_allclose(
            converted.power,
            np.array([0.1, 0.2, 0.3], dtype=np.float64),
            rtol=0.0,
        )

    def test_current_a_pass_through(self) -> None:
        nameplate = _make_nameplate(current=25.0, current_unit="A")
        original_current = np.array([1.0, 2.0, 3.0], dtype=np.float64)
        pc = _make_curve_loaded(current=original_current, current_unit="A")
        converted = convert_ratio_columns_to_absolute(pc, nameplate)
        assert converted.current_unit == "A"
        _assert_optional_array_allclose(
            converted.current,
            original_current,
            rtol=0.0,
        )

    def test_current_ka_pass_through_unit_preserved(self) -> None:
        nameplate = _make_nameplate(current=25.0, current_unit="A")
        pc = _make_curve_loaded(
            current=np.array([0.001, 0.002], dtype=np.float64),
            current_unit="kA",
        )
        converted = convert_ratio_columns_to_absolute(pc, nameplate)
        assert converted.current_unit == "kA"
        _assert_optional_array_allclose(
            converted.current,
            np.array([0.001, 0.002], dtype=np.float64),
            rtol=0.0,
        )


class TestConvertNoneColumnsArePassThrough:
    """``power`` / ``current`` 列が ``None`` の場合は何もしない。"""

    def test_power_none_pass_through(self) -> None:
        nameplate = _make_nameplate()
        pc = _make_curve_loaded(power=None, power_unit=None)
        converted = convert_ratio_columns_to_absolute(pc, nameplate)
        assert converted.power is None
        assert converted.power_unit is None

    def test_current_none_pass_through(self) -> None:
        nameplate = _make_nameplate()
        pc = _make_curve_loaded(current=None, current_unit=None)
        converted = convert_ratio_columns_to_absolute(pc, nameplate)
        assert converted.current is None
        assert converted.current_unit is None


class TestConvertOtherColumnsAreNotTouched:
    """``torque`` / ``power_factor`` / ``efficiency`` 列は触らない。"""

    def test_torque_is_pass_through(self) -> None:
        nameplate = _make_nameplate()
        original_torque = np.array([1.0, 2.0, 3.0], dtype=np.float64)
        pc = _make_curve_loaded(torque=original_torque, torque_unit="Nm")
        converted = convert_ratio_columns_to_absolute(pc, nameplate)
        assert converted.torque_unit == "Nm"
        _assert_optional_array_allclose(
            converted.torque,
            original_torque,
            rtol=0.0,
        )


class TestConvertRaisesOnUnsupportedNameplateUnit:
    """名盤の単位がサポート外なら ``ValueError`` で弾く。"""

    def test_unsupported_power_unit_raises(self) -> None:
        nameplate = _make_nameplate(power=3711.0, power_unit="foo")
        pc = _make_curve_loaded(
            power=np.array([0.1, 0.2], dtype=np.float64),
            power_unit="-",
        )
        with pytest.raises(
            ValueError,
            match=r"EstimateParams 名盤 output_power の単位",
        ):
            convert_ratio_columns_to_absolute(pc, nameplate)

    def test_unsupported_current_unit_raises(self) -> None:
        nameplate = _make_nameplate(current=25.0, current_unit="foo")
        pc = _make_curve_loaded(
            current=np.array([10.0, 20.0], dtype=np.float64),
            current_unit="%",
        )
        with pytest.raises(
            ValueError,
            match=r"EstimateParams 名盤 input_line_current の単位",
        ):
            convert_ratio_columns_to_absolute(pc, nameplate)

    def test_unsupported_unit_only_checked_when_ratio_input(self) -> None:
        """絶対単位入力なら、名盤の単位がサポート外でも raise しない。

        変換が要らない経路では名盤値を読まない、という挙動を固定する。
        """
        nameplate = _make_nameplate(power=3711.0, power_unit="foo")
        pc = _make_curve_loaded(
            power=np.array([100.0, 200.0], dtype=np.float64),
            power_unit="W",
        )
        converted = convert_ratio_columns_to_absolute(pc, nameplate)
        assert converted.power_unit == "W"
