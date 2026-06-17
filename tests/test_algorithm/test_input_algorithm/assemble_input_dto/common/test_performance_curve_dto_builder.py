"""共通性能曲線 DTO ビルダーの組み立て契約テスト。

``performance_curve_dto_builder`` で、欠落列が
``ImPerformanceCurveCatalogDto`` 上で ``None`` のまま乗ること、
``torque`` 列だけがあるケースで ``power_w = T·ω`` の逆算により
``power_series`` が組み立つこと、NaN が mask として保持されることを
直接確認する。
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from im_cable_system.engine.algorithm.input_algorithm.assemble_input_dto.common.performance_curve_dto_builder import (  # noqa: E501
    build_im_performance_curve_catalogs,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data.data_class.im_performance_curve_loaded_data import (  # noqa: E501
    ImPerformanceCurveLoadedData,
)


def _make_curve_loaded(
    *,
    rotational_speed: np.ndarray | None = None,
    power: np.ndarray | None = None,
    power_unit: str | None = None,
    current: np.ndarray | None = None,
    current_unit: str | None = None,
    torque: np.ndarray | None = None,
    torque_unit: str | None = None,
) -> ImPerformanceCurveLoadedData:
    """テスト用に最小の ``ImPerformanceCurveLoadedData`` を組み立てる。"""
    if rotational_speed is None:
        rotational_speed = np.array([1500.0, 1490.0, 1480.0], dtype=np.float64)
    return ImPerformanceCurveLoadedData(
        name="PerformanceCurveBuilderTest",
        poles=4.0,
        supply_frequency=50.0,
        supply_frequency_unit="Hz",
        supply_voltage=200.0,
        supply_voltage_unit="V",
        rotational_speed=rotational_speed,
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


class TestPerformanceCurveBuilderPartialColumns:
    """欠落列が DTO 上で None のまま乗ることを確認する。"""

    def test_only_current_column_keeps_power_series_none(self) -> None:
        loaded = _make_curve_loaded(
            rotational_speed=np.array([1500.0, 1490.0], dtype=np.float64),
            current=np.array([12.0, 15.0], dtype=np.float64),
            current_unit="A",
        )
        cat = build_im_performance_curve_catalogs(loaded).get_all()[0]
        assert cat.current_series is not None
        assert cat.power_series is None
        assert cat.power_factor_series is None
        assert cat.efficiency_series is None
        assert cat.rotational_speed_series is not None


class TestPerformanceCurveBuilderTorqueToPower:
    """``torque`` 列だけがあるケースで ``power = T·ω`` 逆算が走る。"""

    def test_torque_only_backcalculates_power_series(self) -> None:
        rpm_arr = np.array([1500.0, 1450.0, 1400.0], dtype=np.float64)
        torque_arr = np.array([0.0, 5.0, 10.0], dtype=np.float64)
        loaded = _make_curve_loaded(
            rotational_speed=rpm_arr,
            torque=torque_arr,
            torque_unit="Nm",
        )
        cat = build_im_performance_curve_catalogs(loaded).get_all()[0]
        assert cat.power_series is not None
        expected_w = torque_arr * (2.0 * math.pi * rpm_arr / 60.0)
        got_w = np.asarray(
            cat.power_series.to_base_unit().get_value(), dtype=np.float64
        )
        assert np.allclose(got_w, expected_w, rtol=0.0, atol=1e-9)

    def test_power_and_torque_consistency_violation_raises(self) -> None:
        loaded = _make_curve_loaded(
            rotational_speed=np.array([1500.0], dtype=np.float64),
            power=np.array([100.0], dtype=np.float64),
            power_unit="W",
            torque=np.array([0.0], dtype=np.float64),
            torque_unit="Nm",
        )
        with pytest.raises(ValueError, match=r"P = T"):
            build_im_performance_curve_catalogs(loaded)


class TestPerformanceCurveBuilderMaskExtraction:
    """NaN が値 0 + mask=False として保持されることを確認する。"""

    def test_power_nan_yields_mask_and_zero_value(self) -> None:
        loaded = _make_curve_loaded(
            rotational_speed=np.array([1500.0, 1490.0, 1480.0]),
            power=np.array([10.0, np.nan, 30.0], dtype=np.float64),
            power_unit="W",
        )
        cat = build_im_performance_curve_catalogs(loaded).get_all()[0]
        assert cat.power_series is not None
        assert cat.power_series_mask is not None
        np.testing.assert_array_equal(
            cat.power_series_mask,
            np.array([True, False, True], dtype=bool),
        )
        power_w = cat.power_series.to_base_unit().get_value()
        assert power_w[1] == 0.0
        assert np.isfinite(power_w).all()

    def test_no_nan_yields_all_true_mask(self) -> None:
        loaded = _make_curve_loaded(
            rotational_speed=np.array([1500.0, 1490.0], dtype=np.float64),
            power=np.array([10.0, 20.0], dtype=np.float64),
            power_unit="W",
            current=np.array([12.0, 15.0], dtype=np.float64),
            current_unit="A",
        )
        cat = build_im_performance_curve_catalogs(loaded).get_all()[0]
        assert cat.power_series_mask is not None
        assert cat.current_series_mask is not None
        np.testing.assert_array_equal(
            cat.power_series_mask,
            np.array([True, True], dtype=bool),
        )
        np.testing.assert_array_equal(
            cat.current_series_mask,
            np.array([True, True], dtype=bool),
        )

    def test_torque_nan_propagates_to_power_mask(self) -> None:
        loaded = _make_curve_loaded(
            rotational_speed=np.array([1500.0, 1490.0, 1480.0]),
            torque=np.array([1.0, np.nan, 3.0], dtype=np.float64),
            torque_unit="Nm",
        )
        cat = build_im_performance_curve_catalogs(loaded).get_all()[0]
        assert cat.torque_series is not None
        assert cat.torque_series_mask is not None
        np.testing.assert_array_equal(
            cat.torque_series_mask,
            np.array([True, False, True], dtype=bool),
        )
        assert cat.power_series is not None
        assert cat.power_series_mask is not None
        np.testing.assert_array_equal(
            cat.power_series_mask,
            np.array([True, False, True], dtype=bool),
        )
        assert cat.torque_series.to_base_unit().get_value()[1] == 0.0
        assert cat.power_series.to_base_unit().get_value()[1] == 0.0

    def test_all_torque_masked_skips_consistency_check(self) -> None:
        loaded = _make_curve_loaded(
            rotational_speed=np.array([1500.0, 1490.0], dtype=np.float64),
            power=np.array([999.0, 500.0], dtype=np.float64),
            power_unit="W",
            torque=np.array([np.nan, np.nan], dtype=np.float64),
            torque_unit="Nm",
        )
        cat = build_im_performance_curve_catalogs(loaded).get_all()[0]
        assert cat.torque_series_mask is not None
        np.testing.assert_array_equal(
            cat.torque_series_mask,
            np.array([False, False], dtype=bool),
        )
