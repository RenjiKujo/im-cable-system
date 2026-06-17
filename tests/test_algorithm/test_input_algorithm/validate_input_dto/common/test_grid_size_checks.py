"""``check_reference_axes_grid_size`` の経路非依存テスト。

``reference_axes`` 直積点数の上限超過と ``max_grid_points`` の
バリデーション挙動を直接検証する。
"""

from __future__ import annotations

import dataclasses
from collections.abc import Callable

import numpy as np
import pytest

from im_cable_system.engine.algorithm.input_algorithm.validate_input_dto.common.grid_size_checks import (  # noqa: E501, PLC2701
    check_reference_axes_grid_size,
)
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ArrayKey,
)
from im_cable_system.engine.shared.dto.generic.interfaces import (
    IArrayWithUnitDto,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexVoltageDto,
    ArrayFrequencyDto,
    ArraySlipDto,
)
from im_cable_system.engine.shared.dto.input import (
    InputDto,
)


def _replace_array_layout_arrays(
    dto: InputDto, arrays: dict[ArrayKey, IArrayWithUnitDto]
) -> InputDto:
    new_layout = dataclasses.replace(
        dto.array_layout,
        arrays=arrays,
    )
    return dataclasses.replace(dto, array_layout=new_layout)


class TestCheckReferenceAxesGridSize:
    """``check_reference_axes_grid_size`` の単体テスト。"""

    def test_accepts_small_grid(
        self,
        build_cartesian_dto: Callable[..., InputDto],
    ) -> None:
        """小規模グリッドは pass する。"""
        dto = build_cartesian_dto()
        check_reference_axes_grid_size(
            dto,
            max_grid_points=1_000_000,
        )

    def test_rejects_grid_exceeding_cap(
        self,
        build_cartesian_dto: Callable[..., InputDto],
    ) -> None:
        """直積点数が ``max_grid_points`` を超える場合 raise する。"""
        dto = build_cartesian_dto()
        big_slip = ArraySlipDto(
            value=np.linspace(0.0, 1.0, 5000, dtype=np.float64),
            unit="-",
        )
        big_freq = ArrayFrequencyDto(
            value=np.linspace(50.0, 60.0, 100, dtype=np.float64),
            unit="Hz",
        )
        big_volt = ArrayComplexVoltageDto(
            value=np.full(100, 460.0 + 0.0j, dtype=np.complex128),
            unit="V",
        )
        invalid = _replace_array_layout_arrays(
            dto,
            arrays={
                ArrayKey.SLIP: big_slip,
                ArrayKey.FREQUENCY: big_freq,
                ArrayKey.INPUT_LINE_VOLTAGE: big_volt,
            },
        )
        with pytest.raises(
            ValueError, match="reference_axes 直積グリッド点数が上限"
        ):
            check_reference_axes_grid_size(invalid, max_grid_points=10_000)

    def test_rejects_non_positive_max_grid_points(
        self,
        build_cartesian_dto: Callable[..., InputDto],
    ) -> None:
        """``max_grid_points <= 0`` は契約違反として raise する。"""
        dto = build_cartesian_dto()
        with pytest.raises(ValueError, match="max_grid_points"):
            check_reference_axes_grid_size(dto, max_grid_points=0)
        with pytest.raises(ValueError, match="max_grid_points"):
            check_reference_axes_grid_size(dto, max_grid_points=-1)
