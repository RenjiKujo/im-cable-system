"""``build_array_layout`` の単体テスト。

``AxesLoadedData`` 1 件と ``reference_axes`` 指定から
:class:`ArrayLayoutDto` を構築する純粋関数。経路非依存（モード分岐は
``orchestrate`` 層が担う）なので、ここでは reference_axes ごとの
組み立て結果と、単位文字列の正規化・電圧の複素化を直接検証する。
"""

from __future__ import annotations

import numpy as np
import pytest

from im_cable_system.engine.algorithm.input_algorithm.assemble_input_dto.common.array_layout_builder import (  # noqa: E501, PLC2701
    build_array_layout,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data.data_class.axes_loaded_data import (  # noqa: E501, PLC2701
    AxesLoadedData,
)
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ArrayKey,
)


def _make_axes(
    *,
    slip_unit: str = "-",
    frequency_unit: str = "Hz",
    voltage_unit: str = "V",
) -> AxesLoadedData:
    """3 軸とも同じ長さ 3 で揃える共通ヘルパ。

    ``ArrayLayoutDto.__post_init__`` の OperatingPoints 構成
    （reference_axes=[SLIP] のときは非参照軸 ``FREQUENCY`` / ``VOLTAGE`` も
    参照軸と同じ shape の多次元配列でなければならない）と、CartesianGrid
    構成（3 軸とも reference に入る場合は各 1-D 配列、長さは任意）の両方
    で通せるように、全 3 軸を長さ 3 の 1-D 配列にしている。
    """
    return AxesLoadedData(
        slip=np.array([0.0, 0.02, 0.05], dtype=np.float64),
        frequency=np.array([50.0, 50.0, 50.0], dtype=np.float64),
        input_line_voltage=np.array([460.0, 460.0, 460.0], dtype=np.float64),
        slip_unit=slip_unit,
        frequency_unit=frequency_unit,
        voltage_unit=voltage_unit,
    )


class TestBuildArrayLayoutCartesianGridReferenceAxes:
    """CartesianGrid 用 3 軸構成。"""

    def test_returns_dto_with_all_three_axes(self) -> None:
        layout = build_array_layout(
            _make_axes(),
            reference_axes=[
                ArrayKey.SLIP,
                ArrayKey.INPUT_LINE_VOLTAGE,
                ArrayKey.FREQUENCY,
            ],
        )
        assert set(layout.arrays.keys()) == {
            ArrayKey.SLIP,
            ArrayKey.FREQUENCY,
            ArrayKey.INPUT_LINE_VOLTAGE,
        }
        assert layout.reference_axes == [
            ArrayKey.SLIP,
            ArrayKey.INPUT_LINE_VOLTAGE,
            ArrayKey.FREQUENCY,
        ]

    def test_preserves_array_values(self) -> None:
        layout = build_array_layout(
            _make_axes(),
            reference_axes=[
                ArrayKey.SLIP,
                ArrayKey.INPUT_LINE_VOLTAGE,
                ArrayKey.FREQUENCY,
            ],
        )
        slip = layout.arrays[ArrayKey.SLIP].get_value()
        assert np.allclose(slip, [0.0, 0.02, 0.05])
        freq = layout.arrays[ArrayKey.FREQUENCY].get_value()
        assert np.allclose(freq, [50.0, 50.0, 50.0])


class TestBuildArrayLayoutOperatingPointsReferenceAxes:
    """OperatingPoints 用 1 軸（``SLIP`` のみ）構成。"""

    def test_arrays_contain_all_three_but_reference_is_slip_only(self) -> None:
        """非参照軸も ``arrays`` には残し、参照軸の選別だけが
        ``reference_axes`` で表現されることを確認する。"""
        layout = build_array_layout(
            _make_axes(),
            reference_axes=[ArrayKey.SLIP],
        )
        assert set(layout.arrays.keys()) == {
            ArrayKey.SLIP,
            ArrayKey.FREQUENCY,
            ArrayKey.INPUT_LINE_VOLTAGE,
        }
        assert layout.reference_axes == [ArrayKey.SLIP]


class TestBuildArrayLayoutVoltageComplexification:
    """電圧配列が実数 → 複素数に昇格すること。"""

    def test_voltage_array_is_complex128(self) -> None:
        layout = build_array_layout(
            _make_axes(),
            reference_axes=[ArrayKey.SLIP],
        )
        volt = layout.arrays[ArrayKey.INPUT_LINE_VOLTAGE].get_value()
        assert volt.dtype == np.complex128
        assert np.allclose(np.real(volt), [460.0, 460.0, 460.0])
        assert np.allclose(np.imag(volt), [0.0, 0.0, 0.0])


class TestBuildArrayLayoutUnitNormalization:
    """単位セルの正規化（角括弧剥がし・slip 表記揺れ吸収）。"""

    @pytest.mark.parametrize(
        "raw_unit, normalized_unit",
        [
            ("[Hz]", "Hz"),
            ("Hz", "Hz"),
            (" Hz ", "Hz"),
        ],
    )
    def test_frequency_unit_is_normalized(
        self, raw_unit: str, normalized_unit: str
    ) -> None:
        layout = build_array_layout(
            _make_axes(frequency_unit=raw_unit),
            reference_axes=[ArrayKey.FREQUENCY],
        )
        assert layout.arrays[ArrayKey.FREQUENCY].get_unit() == normalized_unit

    @pytest.mark.parametrize(
        "raw_unit, normalized_unit",
        [
            ("[-]", "-"),
            ("-", "-"),
            ("[%]", "%"),
            ("%", "%"),
            ("percent", "%"),
            ("pct", "%"),
            ("dimensionless", "-"),
            ("1", "-"),
        ],
    )
    def test_slip_unit_is_normalized(
        self, raw_unit: str, normalized_unit: str
    ) -> None:
        """slip 列は ``%`` / ``-`` の表記揺れも吸収する。"""
        layout = build_array_layout(
            _make_axes(slip_unit=raw_unit),
            reference_axes=[ArrayKey.SLIP],
        )
        assert layout.arrays[ArrayKey.SLIP].get_unit() == normalized_unit

    def test_voltage_unit_bracket_stripping(self) -> None:
        layout = build_array_layout(
            _make_axes(voltage_unit="[V]"),
            reference_axes=[ArrayKey.SLIP],
        )
        assert layout.arrays[ArrayKey.INPUT_LINE_VOLTAGE].get_unit() == "V"
