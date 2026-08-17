"""``performance_curve_loaded_data_builder`` の単体テスト。"""

from __future__ import annotations

from typing import Any, cast

import numpy as np
import pytest

from im_cable_system.engine.algorithm.input_algorithm.load_data.estimate_params.performance_curve_loaded_data_builder import (  # noqa: E501
    build_im_performance_curve_loaded_data,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data.estimate_params.unified_input_parser import (  # noqa: E501
    EstimateParamsParsedTables,
)


def _make_parsed(
    *,
    header: list[str],
    unit_row: list[str],
    data_rows: list[list[str]],
) -> EstimateParamsParsedTables:
    """性能曲線 builder 用の最小 ParsedTables を組む。"""
    return EstimateParamsParsedTables(
        im_performance_curve_name="curve_test",
        nameplate_block={},
        fixed={},
        candidate_primary=(),
        candidate_excitation=(),
        candidate_secondary_single=(),
        candidate_secondary_double_inner=(),
        candidate_secondary_double_outer=(),
        candidate_friction_windage=(),
        candidate_stray_load=(),
        candidate_cable_conductor=(),
        supply_block={
            "frequency": (50.0, "Hz"),
            "voltage": (400.0, "V"),
        },
        curve_header_row=header,
        curve_unit_row=unit_row,
        curve_data_rows=data_rows,
    )


def _assert_optional_array_allclose(
    actual: np.ndarray | None,
    expected: np.ndarray,
) -> None:
    """optional 系列が存在することを確認してから近似一致を検証する。"""
    if actual is None:
        raise AssertionError("actual array must not be None")
    np.testing.assert_allclose(cast(Any, actual), cast(Any, expected))


class TestBuildImPerformanceCurveLoadedData:
    """性能曲線中間表現 builder の正常・異常系。"""

    def test_accepts_rotational_speed_and_power_only(self) -> None:
        parsed = _make_parsed(
            header=["rotational_speed", "power"],
            unit_row=["rpm", "%"],
            data_rows=[
                ["3000", "100"],
                ["2900", "95"],
            ],
        )
        loaded = build_im_performance_curve_loaded_data(parsed, poles=4)
        np.testing.assert_allclose(
            loaded.rotational_speed,
            np.array([3000.0, 2900.0], dtype=np.float64),
        )
        _assert_optional_array_allclose(
            loaded.power,
            np.array([100.0, 95.0], dtype=np.float64),
        )
        assert loaded.power_unit == "%"
        assert loaded.current is None
        assert loaded.current_unit is None
        assert loaded.power_factor is None
        assert loaded.efficiency is None
        assert loaded.torque is None

    def test_accepts_rotational_speed_and_torque_only(self) -> None:
        parsed = _make_parsed(
            header=["rotational_speed", "torque"],
            unit_row=["rpm", "N*m"],
            data_rows=[
                ["3000", "10"],
                ["2900", "12"],
            ],
        )
        loaded = build_im_performance_curve_loaded_data(parsed, poles=4)
        np.testing.assert_allclose(
            loaded.rotational_speed,
            np.array([3000.0, 2900.0], dtype=np.float64),
        )
        _assert_optional_array_allclose(
            loaded.torque,
            np.array([10.0, 12.0], dtype=np.float64),
        )
        assert loaded.torque_unit == "N*m"
        assert loaded.power is None
        assert loaded.current is None
        assert loaded.power_factor is None
        assert loaded.efficiency is None

    def test_raises_when_rotational_speed_missing(self) -> None:
        parsed = _make_parsed(
            header=["power"],
            unit_row=["%"],
            data_rows=[["100"]],
        )
        with pytest.raises(ValueError, match="必須列 'rotational_speed'"):
            build_im_performance_curve_loaded_data(parsed, poles=4)

    def test_raises_when_observed_columns_missing(self) -> None:
        parsed = _make_parsed(
            header=["rotational_speed"],
            unit_row=["rpm"],
            data_rows=[["3000"]],
        )
        with pytest.raises(ValueError, match="少なくとも 1 列が必要"):
            build_im_performance_curve_loaded_data(parsed, poles=4)

    def test_observed_empty_cells_become_nan(self) -> None:
        """観測列の空セルは ``np.nan`` として保持される。"""
        parsed = _make_parsed(
            header=["rotational_speed", "power", "current"],
            unit_row=["rpm", "-", "%"],
            data_rows=[
                ["3000", "0.1", "10"],
                ["2900", "", "12"],
                ["2800", "0.3", ""],
            ],
        )
        loaded = build_im_performance_curve_loaded_data(parsed, poles=4)
        np.testing.assert_allclose(
            loaded.rotational_speed, [3000.0, 2900.0, 2800.0]
        )
        assert loaded.power is not None
        assert np.isnan(loaded.power[1])
        np.testing.assert_allclose(loaded.power[[0, 2]], [0.1, 0.3])
        assert loaded.current is not None
        assert np.isnan(loaded.current[2])
        np.testing.assert_allclose(loaded.current[[0, 1]], [10.0, 12.0])

    def test_raises_when_rotational_speed_cell_empty(self) -> None:
        """``rotational_speed`` セルが空だとエラー（独立軸として未観測点不可）。"""
        parsed = _make_parsed(
            header=["rotational_speed", "power"],
            unit_row=["rpm", "-"],
            data_rows=[
                ["3000", "0.1"],
                ["", "0.2"],
            ],
        )
        with pytest.raises(
            ValueError,
            match="rotational_speed セルが空",
        ):
            build_im_performance_curve_loaded_data(parsed, poles=4)

    def test_raises_when_observed_cell_not_numeric(self) -> None:
        """観測列の非空かつ非数値セルは ``ValueError``。"""
        parsed = _make_parsed(
            header=["rotational_speed", "power"],
            unit_row=["rpm", "-"],
            data_rows=[
                ["3000", "abc"],
            ],
        )
        with pytest.raises(ValueError):
            build_im_performance_curve_loaded_data(parsed, poles=4)
