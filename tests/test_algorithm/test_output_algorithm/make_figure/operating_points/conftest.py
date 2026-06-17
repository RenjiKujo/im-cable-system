"""operating_points 系 Figure / helper テストの共通フィクスチャ。

``reference_axes = [SLIP]`` の co-indexed な ``OutputDto`` stub を組み立て、
``make_figure.operating_points`` 配下の builder / helper テストで共有する。
運転点（リスト番号）ごとに slip / frequency / voltage と結果量が長さ N で
co-indexed になる。
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


def _output_name() -> Any:
    """Figure タイトル用の出力名 stub を返す。"""
    return SimpleNamespace(get_value=lambda: "test-op-system")


def _result(*, point_count: int) -> Any:
    """operating_points Figure 用の最小 result stub を返す（長さ N の 1 次元）。"""
    speed = np.linspace(1800.0, 1700.0, point_count)
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
            value=speed,
            unit="rpm",
        ),
    )


def _operating_points_layout(*, point_count: int) -> ArrayLayoutDto:
    """slip を参照軸に、frequency / voltage を co-indexed 非参照軸とする layout。"""
    return ArrayLayoutDto(
        arrays={
            ArrayKey.SLIP: ArraySlipDto(
                value=np.linspace(0.05, 0.2, point_count),
                unit="-",
            ),
            ArrayKey.FREQUENCY: ArrayFrequencyDto(
                value=np.linspace(50.0, 60.0, point_count),
                unit="Hz",
            ),
            ArrayKey.INPUT_LINE_VOLTAGE: ArrayComplexVoltageDto(
                value=np.linspace(380.0, 420.0, point_count).astype(
                    np.complex128
                ),
                unit="V",
            ),
        },
        reference_axes=[ArrayKey.SLIP],
    )


def _slip_only_layout(*, point_count: int) -> ArrayLayoutDto:
    """frequency / voltage を持たない（slip のみの）layout。"""
    return ArrayLayoutDto(
        arrays={
            ArrayKey.SLIP: ArraySlipDto(
                value=np.linspace(0.05, 0.2, point_count),
                unit="-",
            ),
        },
        reference_axes=[ArrayKey.SLIP],
    )


@pytest.fixture
def build_operating_points_output_dto() -> Callable[..., Any]:
    """最小 ``OutputDto`` stub を組み立てるファクトリ。

    Args:
        point_count: 運転点（リスト番号）の数。
        with_supply_axes: ``True`` で frequency / voltage 軸を含める。
    """

    def _build(
        *,
        point_count: int = 4,
        with_supply_axes: bool = True,
    ) -> Any:
        layout = (
            _operating_points_layout(point_count=point_count)
            if with_supply_axes
            else _slip_only_layout(point_count=point_count)
        )
        return SimpleNamespace(
            name=_output_name(),
            array_layout=layout,
            result=_result(point_count=point_count),
        )

    return _build


@pytest.fixture
def operating_points_output_dto(
    build_operating_points_output_dto: Callable[..., Any],
) -> Any:
    """frequency / voltage 軸を含む operating_points の ``OutputDto`` stub。"""
    return build_operating_points_output_dto()
