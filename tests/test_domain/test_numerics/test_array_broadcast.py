"""``numerics.array_broadcast`` の単体テスト。

``ArrayLayoutDto`` に基づいて配列をブロードキャストする
``extend_array`` / ``create_extended_arrays`` を検証する。
"""

from __future__ import annotations

import numpy as np
import pytest

from im_cable_system.engine.domain.numerics import (
    create_extended_arrays,
    extend_array,
)
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ArrayKey,
    ArrayLayoutDto,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexCurrentDto,
    ArrayFrequencyDto,
    ArraySlipDto,
)


def _slip() -> ArraySlipDto:
    return ArraySlipDto(value=np.array([0.0, 0.05, 0.1]), unit="-")


def _frequency() -> ArrayFrequencyDto:
    return ArrayFrequencyDto(value=np.array([50.0, 60.0]), unit="Hz")


class TestExtendArrayReferenceAxis:
    """参照軸（1次元入力）の拡張を確認する。"""

    def test_returns_array_with_reference_shape(self) -> None:
        slip = _slip()
        freq = _frequency()
        layout = ArrayLayoutDto(
            arrays={ArrayKey.SLIP: slip, ArrayKey.FREQUENCY: freq},
            reference_axes=[ArrayKey.SLIP, ArrayKey.FREQUENCY],
        )
        extended = extend_array(
            array_layout=layout,
            axis_name=ArrayKey.SLIP,
            array_dto=slip,
        )
        assert extended.shape == (3, 2)
        np.testing.assert_allclose(extended[:, 0], slip.get_value())
        np.testing.assert_allclose(extended[:, 1], slip.get_value())

    def test_rejects_multi_dimensional_reference_input(self) -> None:
        slip = _slip()
        freq = _frequency()
        layout = ArrayLayoutDto(
            arrays={ArrayKey.SLIP: slip, ArrayKey.FREQUENCY: freq},
            reference_axes=[ArrayKey.SLIP, ArrayKey.FREQUENCY],
        )
        wrong_slip = ArraySlipDto(
            value=np.zeros((3, 2), dtype=np.float64), unit="-"
        )
        with pytest.raises(ValueError, match="1次元"):
            extend_array(
                array_layout=layout,
                axis_name=ArrayKey.SLIP,
                array_dto=wrong_slip,
            )

    def test_rejects_reference_array_with_wrong_length(self) -> None:
        slip = _slip()
        freq = _frequency()
        layout = ArrayLayoutDto(
            arrays={ArrayKey.SLIP: slip, ArrayKey.FREQUENCY: freq},
            reference_axes=[ArrayKey.SLIP, ArrayKey.FREQUENCY],
        )
        wrong_slip = ArraySlipDto(value=np.array([0.0, 0.1]), unit="-")
        with pytest.raises(ValueError, match="長さが一致しません"):
            extend_array(
                array_layout=layout,
                axis_name=ArrayKey.SLIP,
                array_dto=wrong_slip,
            )


class TestExtendArrayNonReferenceAxis:
    """非参照軸（既に多次元）の入力をそのまま返すこと。"""

    def test_returns_input_as_is_when_shape_matches(self) -> None:
        slip = _slip()
        freq = _frequency()
        ref_shape = (slip.get_value().size, freq.get_value().size)
        current_values = np.ones(ref_shape, dtype=np.complex128)
        current = ArrayComplexCurrentDto(value=current_values, unit="A")
        layout = ArrayLayoutDto(
            arrays={
                ArrayKey.SLIP: slip,
                ArrayKey.FREQUENCY: freq,
                ArrayKey.IM_PRIMARY_CURRENT: current,
            },
            reference_axes=[ArrayKey.SLIP, ArrayKey.FREQUENCY],
        )
        extended = extend_array(
            array_layout=layout,
            axis_name=ArrayKey.IM_PRIMARY_CURRENT,
            array_dto=current,
        )
        np.testing.assert_allclose(extended, current_values)

    def test_rejects_non_reference_input_with_wrong_shape(self) -> None:
        """非参照軸が flatten 1D のように shape が違うと拒否される。"""
        slip = _slip()
        freq = _frequency()
        ref_shape = (slip.get_value().size, freq.get_value().size)
        flatten_size = int(np.prod(ref_shape))
        wrong_current = ArrayComplexCurrentDto(
            value=np.ones(flatten_size, dtype=np.complex128), unit="A"
        )
        with pytest.raises(ValueError):
            layout = ArrayLayoutDto(
                arrays={
                    ArrayKey.SLIP: slip,
                    ArrayKey.FREQUENCY: freq,
                    ArrayKey.IM_PRIMARY_CURRENT: wrong_current,
                },
                reference_axes=[ArrayKey.SLIP, ArrayKey.FREQUENCY],
            )
            extend_array(
                array_layout=layout,
                axis_name=ArrayKey.IM_PRIMARY_CURRENT,
                array_dto=wrong_current,
            )


class TestExtendArrayInvalidArguments:
    """不正な引数で ValueError が出ること。"""

    def test_rejects_unknown_axis_name(self) -> None:
        slip = _slip()
        layout = ArrayLayoutDto(
            arrays={ArrayKey.SLIP: slip},
            reference_axes=[ArrayKey.SLIP],
        )
        with pytest.raises(ValueError, match="存在しません"):
            extend_array(
                array_layout=layout,
                axis_name=ArrayKey.FREQUENCY,
                array_dto=ArrayFrequencyDto(value=np.array([50.0]), unit="Hz"),
            )


class TestCreateExtendedArrays:
    """``create_extended_arrays`` が全軸をループ拡張すること。"""

    def test_returns_all_axes_with_reference_shape(self) -> None:
        slip = _slip()
        freq = _frequency()
        layout = ArrayLayoutDto(
            arrays={ArrayKey.SLIP: slip, ArrayKey.FREQUENCY: freq},
            reference_axes=[ArrayKey.SLIP, ArrayKey.FREQUENCY],
        )
        extended = create_extended_arrays(layout)
        assert set(extended.keys()) == {ArrayKey.SLIP, ArrayKey.FREQUENCY}
        for arr in extended.values():
            assert arr.shape == (3, 2)
        np.testing.assert_allclose(
            extended[ArrayKey.SLIP][:, 0], [0.0, 0.05, 0.1]
        )
        np.testing.assert_allclose(
            extended[ArrayKey.FREQUENCY][0, :], [50.0, 60.0]
        )
