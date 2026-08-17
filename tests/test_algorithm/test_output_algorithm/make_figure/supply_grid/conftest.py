"""supply_grid 系 Figure / helper テストの共通フィクスチャ。

``OutputDto`` の最小 stub と ``array_layout`` を組み立て、
``make_figure.supply_grid`` 配下の builder / helper テストで共有する。
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
    ImCageMultiplicityType,
    ImPerformanceCurveCatalogDtos,
    ImSecondaryCageBranchType,
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
    FloatActivePowerDto,
    FloatCurrentDto,
)


def _output_name() -> Any:
    """Figure タイトル用の出力名 stub を返す。

    ``get_value()``（識別子）と ``get_base()``（表示名）をあえて異なる文字列
    にしている。両者を取り違えて実装が ``get_value()`` を表示に使うように
    戻っても、この stub ならテストが検出できる。
    """
    return SimpleNamespace(
        get_value=lambda: "test-system_1_1_1_0_0_1_1_0",
        get_base=lambda: "test-system",
    )


def _named_model(name: str) -> Any:
    """``get_name()`` だけを持つモデル DTO stub を返す（注記用）。"""
    return SimpleNamespace(get_name=lambda: name)


def _im() -> Any:
    """出力比 Figure 用の最小 IM stub を返す（モデル名注記に必要な属性込み）。"""
    return SimpleNamespace(
        im_series=SimpleNamespace(
            nameplate_power=FloatActivePowerDto(value=200.0, unit="W"),
            nameplate_current=FloatCurrentDto(value=2.0, unit="A"),
            primary_model=_named_model("BASIC"),
            excitation_model=_named_model("BASIC"),
            cage_multiplicity=ImCageMultiplicityType.SINGLE_CAGE,
            secondary_models={
                ImSecondaryCageBranchType.SINGLE: _named_model("BASIC"),
            },
            friction_windage_model=_named_model("NONE"),
            stray_load_model=_named_model("NONE"),
        ),
    )


def _result(*, slip_count: int = 2) -> Any:
    """supply_grid Figure 用の最小 result stub を返す。"""
    shape = (slip_count, 1, 1)
    output_power_values = np.array(
        [[[50.0 + 0.0j]], [[100.0 + 0.0j]]]
        if slip_count == 2
        else [[[50.0 + 0.0j]], [[100.0 + 0.0j]], [[30.0 + 0.0j]]],
        dtype=np.complex128,
    )
    return SimpleNamespace(
        output_power=ArrayComplexPowerDto(
            value=output_power_values,
            unit="VA",
        ),
        cable_input_phase_power=ArrayComplexPowerDto(
            value=np.full(shape, 100.0 + 0.0j, dtype=np.complex128),
            unit="VA",
        ),
        input_line_current=ArrayComplexCurrentDto(
            value=np.full(shape, 2.0 + 0.0j, dtype=np.complex128),
            unit="A",
        ),
        system_efficiency=ArrayEfficiencyDto(
            value=np.full(shape, 0.8),
            unit="-",
        ),
        torque=ArrayTorqueDto(
            value=np.full(shape, 5.0),
            unit="Nm",
        ),
        rotational_speed=ArrayRotationalSpeedDto(
            value=np.array(
                [[[1800.0]]]
                if slip_count == 1
                else [[[1800.0]], [[1750.0]]]
                if slip_count == 2
                else [[[1850.0]], [[1800.0]], [[1700.0]]],
                dtype=np.float64,
            ),
            unit="rpm",
        ),
    )


def _supply_grid_layout(*, slip_count: int = 2) -> ArrayLayoutDto:
    """slip / frequency / input_line_voltage を持つ layout を返す。"""
    slip_values = (
        np.array([0.1], dtype=np.float64)
        if slip_count == 1
        else np.array([0.1, 0.2], dtype=np.float64)
        if slip_count == 2
        else np.array([0.05, 0.1, 0.3], dtype=np.float64)
    )
    return ArrayLayoutDto(
        arrays={
            ArrayKey.SLIP: ArraySlipDto(value=slip_values, unit="-"),
            ArrayKey.FREQUENCY: ArrayFrequencyDto(
                value=np.array([60.0], dtype=np.float64),
                unit="Hz",
            ),
            ArrayKey.INPUT_LINE_VOLTAGE: ArrayComplexVoltageDto(
                value=np.array([460.0 + 0.0j], dtype=np.complex128),
                unit="V",
            ),
        },
        reference_axes=[
            ArrayKey.SLIP,
            ArrayKey.FREQUENCY,
            ArrayKey.INPUT_LINE_VOLTAGE,
        ],
    )


def _slip_only_layout() -> ArrayLayoutDto:
    """supply_grid 必須軸が不足した layout を返す。"""
    return ArrayLayoutDto(
        arrays={
            ArrayKey.SLIP: ArraySlipDto(
                value=np.array([0.1, 0.2], dtype=np.float64),
                unit="-",
            ),
        },
        reference_axes=[ArrayKey.SLIP],
    )


@pytest.fixture
def build_supply_grid_output_dto() -> Callable[..., Any]:
    """最小 ``OutputDto`` stub を組み立てるファクトリ。

    Args:
        layout: 参照軸レイアウト。省略時は supply_grid 必須 3 軸。
        slip_count: ``layout`` 省略時の slip 点数（1 / 2 / 3）。
        catalogs: 性能カーブカタログ。省略時は空。
    """

    def _build(
        *,
        layout: ArrayLayoutDto | None = None,
        slip_count: int = 2,
        catalogs: ImPerformanceCurveCatalogDtos | None = None,
    ) -> Any:
        resolved_layout = (
            layout
            if layout is not None
            else _supply_grid_layout(slip_count=slip_count)
        )
        resolved_slip_count = int(
            resolved_layout.arrays[ArrayKey.SLIP].get_value().size
        )
        return SimpleNamespace(
            name=_output_name(),
            im=_im(),
            cable=None,
            array_layout=resolved_layout,
            result=_result(slip_count=resolved_slip_count),
            im_pc_catalogs=(
                catalogs
                if catalogs is not None
                else ImPerformanceCurveCatalogDtos(objects=[])
            ),
        )

    return _build


@pytest.fixture
def supply_grid_output_dto(
    build_supply_grid_output_dto: Callable[..., Any],
) -> Any:
    """supply_grid 必須 3 軸を持つ最小 ``OutputDto`` stub。"""
    return build_supply_grid_output_dto()


@pytest.fixture
def slip_only_output_dto(
    build_supply_grid_output_dto: Callable[..., Any],
) -> Any:
    """必須軸不足の ``OutputDto`` stub。"""
    return build_supply_grid_output_dto(layout=_slip_only_layout())


@pytest.fixture
def peak_at_middle_slip_output_dto(
    build_supply_grid_output_dto: Callable[..., Any],
) -> Any:
    """出力ピークが中間 slip にある ``OutputDto`` stub（3 slip 点）。"""
    return build_supply_grid_output_dto(slip_count=3)
