"""ArrayLayoutDto の shape 契約テスト。

特に OperatingPoints モード（``reference_axes = [SLIP]``）で、
``frequency`` / ``input_line_voltage`` を非参照軸として渡したときに、
それらの長さが SLIP と一致しない場合に ``__post_init__`` が
``ValueError`` を出すことを保証する。

Forward の :class:`ForwardInputDtoValidator` 側で同等の長さ一致チェックを
重複して持たない設計にした（DTO 側で強制する）ため、本テストでその契約を
明文化する。
"""

from __future__ import annotations

import numpy as np
import pytest

from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ArrayKey,
    ArrayLayoutDto,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexVoltageDto,
    ArrayFrequencyDto,
    ArraySlipDto,
)


def _make_slip(values: list[float]) -> ArraySlipDto:
    return ArraySlipDto(value=np.array(values, dtype=np.float64), unit="-")


def _make_frequency(values: list[float]) -> ArrayFrequencyDto:
    return ArrayFrequencyDto(
        value=np.array(values, dtype=np.float64), unit="Hz"
    )


def _make_voltage(values: list[complex]) -> ArrayComplexVoltageDto:
    return ArrayComplexVoltageDto(
        value=np.array(values, dtype=np.complex128),
        unit="V",
    )


class TestArrayLayoutDtoOperatingPointsShapeContract:
    """OperatingPoints (reference_axes=[SLIP]) の non-reference 軸 shape 契約。"""

    def test_co_indexed_three_axes_with_same_length_passes(self) -> None:
        ArrayLayoutDto(
            arrays={
                ArrayKey.SLIP: _make_slip([0.01, 0.02, 0.03]),
                ArrayKey.FREQUENCY: _make_frequency([50.0, 50.0, 60.0]),
                ArrayKey.INPUT_LINE_VOLTAGE: _make_voltage(
                    [400.0 + 0j, 400.0 + 0j, 460.0 + 0j],
                ),
            },
            reference_axes=[ArrayKey.SLIP],
        )

    def test_frequency_length_mismatch_raises(self) -> None:
        with pytest.raises(
            ValueError,
            match="non-reference arrays must be multidimensional arrays",
        ):
            ArrayLayoutDto(
                arrays={
                    ArrayKey.SLIP: _make_slip([0.01, 0.02, 0.03]),
                    ArrayKey.FREQUENCY: _make_frequency([50.0, 60.0]),
                    ArrayKey.INPUT_LINE_VOLTAGE: _make_voltage(
                        [400.0 + 0j, 400.0 + 0j, 460.0 + 0j],
                    ),
                },
                reference_axes=[ArrayKey.SLIP],
            )

    def test_voltage_length_mismatch_raises(self) -> None:
        with pytest.raises(
            ValueError,
            match="non-reference arrays must be multidimensional arrays",
        ):
            ArrayLayoutDto(
                arrays={
                    ArrayKey.SLIP: _make_slip([0.01, 0.02, 0.03]),
                    ArrayKey.FREQUENCY: _make_frequency([50.0, 50.0, 60.0]),
                    ArrayKey.INPUT_LINE_VOLTAGE: _make_voltage(
                        [400.0 + 0j, 460.0 + 0j],
                    ),
                },
                reference_axes=[ArrayKey.SLIP],
            )

    def test_both_non_reference_axes_length_mismatch_raises(self) -> None:
        with pytest.raises(
            ValueError,
            match="non-reference arrays must be multidimensional arrays",
        ):
            ArrayLayoutDto(
                arrays={
                    ArrayKey.SLIP: _make_slip([0.01, 0.02, 0.03]),
                    ArrayKey.FREQUENCY: _make_frequency([50.0]),
                    ArrayKey.INPUT_LINE_VOLTAGE: _make_voltage(
                        [400.0 + 0j, 460.0 + 0j],
                    ),
                },
                reference_axes=[ArrayKey.SLIP],
            )


class TestArrayLayoutDtoCartesianGridShapeContract:
    """CartesianGrid (reference_axes=[SLIP, VOLT, FREQ]) の参照軸長さ契約。"""

    def test_three_reference_axes_with_distinct_lengths_passes(self) -> None:
        ArrayLayoutDto(
            arrays={
                ArrayKey.SLIP: _make_slip([0.01, 0.02, 0.03]),
                ArrayKey.INPUT_LINE_VOLTAGE: _make_voltage(
                    [400.0 + 0j, 460.0 + 0j],
                ),
                ArrayKey.FREQUENCY: _make_frequency([50.0]),
            },
            reference_axes=[
                ArrayKey.SLIP,
                ArrayKey.INPUT_LINE_VOLTAGE,
                ArrayKey.FREQUENCY,
            ],
        )

    def test_non_one_dim_reference_axis_raises(self) -> None:
        slip_2d = ArraySlipDto(
            value=np.array([[0.01, 0.02], [0.03, 0.04]], dtype=np.float64),
            unit="-",
        )
        with pytest.raises(ValueError, match="must be a 1-D array"):
            ArrayLayoutDto(
                arrays={ArrayKey.SLIP: slip_2d},
                reference_axes=[ArrayKey.SLIP],
            )
