"""operating_points 系 表テストの共通フィクスチャ。

``reference_axes = [SLIP]`` の co-indexed な ``OutputDto`` stub を組み立て、
``make_table.operating_points`` の builder テストで共有する。
"""

from __future__ import annotations

from collections.abc import Callable
from types import SimpleNamespace
from typing import Any

import numpy as np
import pytest

from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ArrayKey,
    ArrayLayoutDto,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexCurrentDto,
    ArrayComplexPowerDto,
    ArrayComplexVoltageDto,
    ArrayEfficiencyDto,
    ArrayFrequencyDto,
    ArrayRotationalSpeedDto,
    ArraySlipDto,
    ArrayTorqueDto,
)


def _result(*, point_count: int) -> Any:
    """operating_points 表用の最小 result stub を返す（長さ N の 1 次元）。"""
    return SimpleNamespace(
        output_power=ArrayComplexPowerDto(
            value=np.linspace(50.0, 120.0, point_count).astype(np.complex128),
            unit="VA",
        ),
        cable_input_phase_power=ArrayComplexPowerDto(
            value=np.full(point_count, 100.0 + 30.0j, dtype=np.complex128),
            unit="VA",
        ),
        input_line_current=ArrayComplexCurrentDto(
            value=np.linspace(2.0, 3.0, point_count).astype(np.complex128),
            unit="A",
        ),
        system_efficiency=ArrayEfficiencyDto(
            value=np.linspace(0.7, 0.85, point_count),
            unit="-",
        ),
        torque=ArrayTorqueDto(
            value=np.linspace(4.0, 6.0, point_count),
            unit="Nm",
        ),
        rotational_speed=ArrayRotationalSpeedDto(
            value=np.linspace(1800.0, 1700.0, point_count),
            unit="rpm",
        ),
    )


def _layout(*, point_count: int, with_supply_axes: bool) -> ArrayLayoutDto:
    """slip 参照軸（＋任意で frequency / voltage 非参照軸）の layout を返す。"""
    arrays: dict[ArrayKey, Any] = {
        ArrayKey.SLIP: ArraySlipDto(
            value=np.linspace(0.05, 0.2, point_count),
            unit="-",
        ),
    }
    if with_supply_axes:
        arrays[ArrayKey.FREQUENCY] = ArrayFrequencyDto(
            value=np.linspace(50.0, 60.0, point_count),
            unit="Hz",
        )
        arrays[ArrayKey.INPUT_LINE_VOLTAGE] = ArrayComplexVoltageDto(
            value=np.linspace(380.0, 420.0, point_count).astype(np.complex128),
            unit="V",
        )
    return ArrayLayoutDto(arrays=arrays, reference_axes=[ArrayKey.SLIP])


@pytest.fixture
def build_operating_points_output_dto() -> Callable[..., Any]:
    """最小 ``OutputDto`` stub を組み立てるファクトリ。"""

    def _build(
        *,
        point_count: int = 4,
        with_supply_axes: bool = True,
    ) -> Any:
        return SimpleNamespace(
            name=SimpleNamespace(get_value=lambda: "test-op-system"),
            array_layout=_layout(
                point_count=point_count,
                with_supply_axes=with_supply_axes,
            ),
            result=_result(point_count=point_count),
        )

    return _build


@pytest.fixture
def operating_points_output_dto(
    build_operating_points_output_dto: Callable[..., Any],
) -> Any:
    """frequency / voltage 軸を含む operating_points の ``OutputDto`` stub。"""
    return build_operating_points_output_dto()
