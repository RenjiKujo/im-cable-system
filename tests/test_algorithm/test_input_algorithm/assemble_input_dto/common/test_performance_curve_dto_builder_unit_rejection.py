"""共通性能曲線ビルダーの単位ガード単体テスト。

``performance_curve_dto_builder`` の共通契約
（モジュール docstring）を直接固定する：

- ``power`` / ``current`` / ``torque`` 列の **比率単位** ``-`` / ``%``
  は ``ValueError`` で拒否する。
- 観測列に ``inf`` が含まれていた場合は ``ValueError`` で拒否する
  （``inf`` は欠損ではなく異常値とみなす）。
- 絶対単位（``W`` / ``kW`` / ``A`` / ``kA`` / ``Nm`` 等）は素通しする。

``ImPerformanceCurveLoadedData`` を直接組み立てて
:func:`build_im_performance_curve_catalogs` に渡す形で、TSV を介さずに
ビルダー単体の挙動を確認する。
"""

from __future__ import annotations

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
    power: np.ndarray | None = None,
    power_unit: str | None = None,
    current: np.ndarray | None = None,
    current_unit: str | None = None,
    torque: np.ndarray | None = None,
    torque_unit: str | None = None,
    rotational_speed: np.ndarray | None = None,
) -> ImPerformanceCurveLoadedData:
    """テスト用に最小の ``ImPerformanceCurveLoadedData`` を組み立てる。"""
    if rotational_speed is None:
        rotational_speed = np.array([1500.0, 1490.0, 1480.0], dtype=np.float64)
    return ImPerformanceCurveLoadedData(
        name="UnitRejectionTest",
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


class TestPowerSeriesRejectsRatioUnits:
    """``power`` 列の比率単位を拒否する。"""

    def test_power_unit_dash_raises(self) -> None:
        """``power_unit='-'`` （ratio）は ``ValueError``。"""
        loaded = _make_curve_loaded(
            power=np.array([0.1, 0.2, 0.3], dtype=np.float64),
            power_unit="-",
        )
        with pytest.raises(
            ValueError,
            match=r"性能曲線ビルダーでは power 列の比率単位",
        ):
            build_im_performance_curve_catalogs(loaded)

    def test_power_unit_bracket_dash_raises(self) -> None:
        """``power_unit='[-]'`` （角括弧付き ratio）も ``ValueError``。"""
        loaded = _make_curve_loaded(
            power=np.array([0.1, 0.2, 0.3], dtype=np.float64),
            power_unit="[-]",
        )
        with pytest.raises(
            ValueError,
            match=r"性能曲線ビルダーでは power 列の比率単位",
        ):
            build_im_performance_curve_catalogs(loaded)

    def test_power_unit_percent_raises(self) -> None:
        """``power_unit='%'`` （percent of rated）は ``ValueError``。"""
        loaded = _make_curve_loaded(
            power=np.array([10.0, 20.0, 30.0], dtype=np.float64),
            power_unit="%",
        )
        with pytest.raises(
            ValueError,
            match=r"性能曲線ビルダーでは power 列の比率単位",
        ):
            build_im_performance_curve_catalogs(loaded)


class TestCurrentSeriesRejectsRatioUnits:
    """``current`` 列の比率単位を拒否する。"""

    def test_current_unit_dash_raises(self) -> None:
        loaded = _make_curve_loaded(
            current=np.array([0.5, 0.6, 0.7], dtype=np.float64),
            current_unit="-",
        )
        with pytest.raises(
            ValueError,
            match=r"性能曲線ビルダーでは current 列の比率単位",
        ):
            build_im_performance_curve_catalogs(loaded)

    def test_current_unit_percent_raises(self) -> None:
        loaded = _make_curve_loaded(
            current=np.array([12.0, 15.0, 18.0], dtype=np.float64),
            current_unit="%",
        )
        with pytest.raises(
            ValueError,
            match=r"性能曲線ビルダーでは current 列の比率単位",
        ):
            build_im_performance_curve_catalogs(loaded)

    def test_current_unit_bracket_percent_raises(self) -> None:
        loaded = _make_curve_loaded(
            current=np.array([12.0, 15.0, 18.0], dtype=np.float64),
            current_unit="[%]",
        )
        with pytest.raises(
            ValueError,
            match=r"性能曲線ビルダーでは current 列の比率単位",
        ):
            build_im_performance_curve_catalogs(loaded)


class TestTorqueSeriesRejectsRatioUnits:
    """``torque`` 列の比率単位を拒否する。"""

    def test_torque_unit_dash_raises(self) -> None:
        loaded = _make_curve_loaded(
            torque=np.array([1.0, 2.0, 3.0], dtype=np.float64),
            torque_unit="-",
        )
        with pytest.raises(
            ValueError,
            match=r"性能曲線ビルダーでは torque 列の比率単位",
        ):
            build_im_performance_curve_catalogs(loaded)

    def test_torque_unit_percent_raises(self) -> None:
        loaded = _make_curve_loaded(
            torque=np.array([1.0, 2.0, 3.0], dtype=np.float64),
            torque_unit="%",
        )
        with pytest.raises(
            ValueError,
            match=r"性能曲線ビルダーでは torque 列の比率単位",
        ):
            build_im_performance_curve_catalogs(loaded)


class TestAcceptsAbsoluteUnits:
    """正常系として、絶対単位は素通しすることを確認する。"""

    def test_power_w_and_current_a_pass_through(self) -> None:
        """``W`` / ``A`` は raise せず、各系列が組み立つ。

        ``power`` と ``torque`` を同時に渡すと
        :class:`ImPerformanceCurveCatalogDto.__post_init__` が
        ``P = T·ω`` 整合性を検証するため、ここでは ``torque`` を渡さず
        ``power`` / ``current`` の絶対単位素通しのみを確定する。
        """
        loaded = _make_curve_loaded(
            power=np.array([100.0, 200.0, 300.0], dtype=np.float64),
            power_unit="W",
            current=np.array([1.0, 1.5, 2.0], dtype=np.float64),
            current_unit="A",
        )
        catalogs = build_im_performance_curve_catalogs(loaded)
        cat = catalogs.get_all()[0]
        assert cat.power_series is not None
        assert cat.power_series.get_unit() == "W"
        assert cat.current_series is not None
        assert cat.current_series.get_unit() == "A"

    def test_torque_nm_passes_through_and_derives_power(self) -> None:
        """``Nm`` は raise されず、``P = T·ω`` 逆算経路で power が組み立つ。"""
        loaded = _make_curve_loaded(
            torque=np.array([0.5, 1.0, 1.5], dtype=np.float64),
            torque_unit="Nm",
        )
        catalogs = build_im_performance_curve_catalogs(loaded)
        cat = catalogs.get_all()[0]
        assert cat.torque_series is not None
        assert cat.torque_series.get_unit() == "Nm"
        assert cat.power_series is not None
        assert cat.power_series.get_unit() == "W"

    def test_power_kw_pass_through_unit_preserved(self) -> None:
        """``kW`` は ``ValueError`` にならず、単位文字列が保たれる。"""
        loaded = _make_curve_loaded(
            power=np.array([0.1, 0.2, 0.3], dtype=np.float64),
            power_unit="kW",
        )
        catalogs = build_im_performance_curve_catalogs(loaded)
        cat = catalogs.get_all()[0]
        assert cat.power_series is not None
        assert cat.power_series.get_unit() == "kW"

    def test_current_ka_pass_through_unit_preserved(self) -> None:
        """``kA`` は ``ValueError`` にならず、単位文字列が保たれる。"""
        loaded = _make_curve_loaded(
            current=np.array([0.001, 0.0015, 0.002], dtype=np.float64),
            current_unit="kA",
        )
        catalogs = build_im_performance_curve_catalogs(loaded)
        cat = catalogs.get_all()[0]
        assert cat.current_series is not None
        assert cat.current_series.get_unit() == "kA"


class TestSplitValueAndMaskRejectsInf:
    """``_split_value_and_mask`` が ``inf`` を ``ValueError`` で弾くこと。

    private 関数を直接 import せず、``power`` / ``current`` / ``torque``
    のいずれかに ``inf`` を仕込んだ ``ImPerformanceCurveLoadedData`` を
    ビルダーに渡すことで、間接的に挙動を固定する。
    """

    def test_inf_in_power_series_raises(self) -> None:
        loaded = _make_curve_loaded(
            power=np.array([100.0, np.inf, 300.0], dtype=np.float64),
            power_unit="W",
        )
        with pytest.raises(ValueError, match=r"power_series に inf"):
            build_im_performance_curve_catalogs(loaded)

    def test_inf_in_current_series_raises(self) -> None:
        loaded = _make_curve_loaded(
            current=np.array([1.0, np.inf, 2.0], dtype=np.float64),
            current_unit="A",
        )
        with pytest.raises(ValueError, match=r"current_series に inf"):
            build_im_performance_curve_catalogs(loaded)

    def test_inf_in_torque_series_raises(self) -> None:
        loaded = _make_curve_loaded(
            torque=np.array([1.0, 2.0, np.inf], dtype=np.float64),
            torque_unit="Nm",
        )
        with pytest.raises(ValueError, match=r"torque_series に inf"):
            build_im_performance_curve_catalogs(loaded)

    def test_negative_inf_in_power_series_raises(self) -> None:
        """``-inf`` も ``np.isinf`` で検知し ``ValueError``。"""
        loaded = _make_curve_loaded(
            power=np.array([100.0, -np.inf, 300.0], dtype=np.float64),
            power_unit="W",
        )
        with pytest.raises(ValueError, match=r"power_series に inf"):
            build_im_performance_curve_catalogs(loaded)

    def test_nan_in_power_series_does_not_raise(self) -> None:
        """``np.nan`` は欠損として許容され、placeholder + mask で表現される。

        inf との挙動差を 1 ケースで対比的に固定する。
        """
        loaded = _make_curve_loaded(
            power=np.array([100.0, np.nan, 300.0], dtype=np.float64),
            power_unit="W",
        )
        catalogs = build_im_performance_curve_catalogs(loaded)
        cat = catalogs.get_all()[0]
        assert cat.power_series is not None
        assert cat.power_series_mask is not None
        power_w = cat.power_series.get_value()
        assert np.isfinite(power_w).all()
        assert power_w[1] == 0.0
        assert cat.power_series_mask.tolist() == [True, False, True]
