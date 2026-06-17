"""supply_grid 表テストの共通ヘルパー。"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import numpy as np

from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ArrayKey,
    ArrayLayoutDto,
    ImPerformanceCurveCatalogDto,
    ImPerformanceCurveCatalogDtos,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayActivePowerDto,
    ArrayComplexCurrentDto,
    ArrayComplexPowerDto,
    ArrayComplexVoltageDto,
    ArrayCurrentMagnitudeDto,
    ArrayEfficiencyDto,
    ArrayFrequencyDto,
    ArrayPowerFactorDto,
    ArrayRotationalSpeedDto,
    ArraySlipDto,
    ArrayTorqueDto,
    FloatFrequencyDto,
    FloatVoltageDto,
)


def output_name_stub() -> Any:
    """出力名 stub を返す。"""
    return SimpleNamespace(get_value=lambda: "test-system")


def result_stub() -> Any:
    """(slip, freq, voltage) = (2, 1, 2) の result stub を返す。"""
    shape = (2, 1, 2)
    output_power = np.array(
        [[[0.0 + 0.0j, 1.0 + 0.0j]], [[100.0 + 0.0j, 101.0 + 0.0j]]],
        dtype=np.complex128,
    )
    return SimpleNamespace(
        output_power=ArrayComplexPowerDto(value=output_power, unit="VA"),
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
        torque=ArrayTorqueDto(value=np.full(shape, 5.0), unit="Nm"),
        rotational_speed=ArrayRotationalSpeedDto(
            value=np.full(shape, 1800.0),
            unit="rpm",
        ),
    )


def supply_grid_layout() -> ArrayLayoutDto:
    """slip 2 点 × freq 1 点 × voltage 2 点の layout を返す。"""
    return ArrayLayoutDto(
        arrays={
            ArrayKey.SLIP: ArraySlipDto(value=np.array([0.1, 0.2]), unit="-"),
            ArrayKey.FREQUENCY: ArrayFrequencyDto(
                value=np.array([60.0]),
                unit="Hz",
            ),
            ArrayKey.INPUT_LINE_VOLTAGE: ArrayComplexVoltageDto(
                value=np.array([200.0 + 0.0j, 460.0 + 0.0j]),
                unit="V",
            ),
        },
        reference_axes=[
            ArrayKey.SLIP,
            ArrayKey.FREQUENCY,
            ArrayKey.INPUT_LINE_VOLTAGE,
        ],
    )


def catalog_dtos() -> ImPerformanceCurveCatalogDtos:
    """供給条件 (f=60, V=460) の参照カタログ 1 件を返す。"""
    catalog = ImPerformanceCurveCatalogDto(
        name="ref",
        supply_frequency=FloatFrequencyDto(value=60.0, unit="Hz"),
        supply_voltage=FloatVoltageDto(value=460.0, unit="V"),
        slip_series=ArraySlipDto(value=np.array([0.1, 0.2]), unit="-"),
        power_series=ArrayActivePowerDto(value=np.array([1.0, 2.0]), unit="W"),
        power_series_mask=np.ones(2, dtype=bool),
        current_series=ArrayCurrentMagnitudeDto(
            value=np.array([10.0, 20.0]),
            unit="A",
        ),
        current_series_mask=np.ones(2, dtype=bool),
        power_factor_series=ArrayPowerFactorDto(
            value=np.array([0.8, 0.9]),
            unit="-",
        ),
        power_factor_series_mask=np.ones(2, dtype=bool),
        efficiency_series=ArrayEfficiencyDto(
            value=np.array([0.85, 0.95]),
            unit="-",
        ),
        efficiency_series_mask=np.ones(2, dtype=bool),
    )
    return ImPerformanceCurveCatalogDtos(objects=[catalog])


def output_dto_stub(catalogs: ImPerformanceCurveCatalogDtos) -> Any:
    """builder が参照する最小 OutputDto stub を返す。"""
    return SimpleNamespace(
        name=output_name_stub(),
        array_layout=supply_grid_layout(),
        result=result_stub(),
        im_pc_catalogs=catalogs,
    )
