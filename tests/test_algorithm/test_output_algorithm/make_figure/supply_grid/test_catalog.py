"""supply_grid ``catalog`` の単体テスト。"""

from __future__ import annotations

from typing import Any

import numpy as np

from im_cable_system.engine.algorithm.output_algorithm.make_figure.supply_grid.catalog import (  # noqa: E501, PLC2701
    _build_catalog_slices,
    _match_catalog,
    _supply_keys_close,
)
from im_cable_system.engine.algorithm.output_algorithm.make_figure.supply_grid.series import (  # noqa: E501, PLC2701
    _build_simulated_slices,
)
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ImPerformanceCurveCatalogDto,
    ImPerformanceCurveCatalogDtos,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayActivePowerDto,
    ArrayCurrentMagnitudeDto,
    ArrayEfficiencyDto,
    ArrayPowerFactorDto,
    ArraySlipDto,
    FloatFrequencyDto,
    FloatVoltageDto,
)


def _catalog_dtos() -> ImPerformanceCurveCatalogDtos:
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


class TestCatalog:
    """カタログ正規化と (f, V) マッチ。"""

    def test_supply_keys_close(self) -> None:
        assert _supply_keys_close(60.0, 460.0, 60.0, 460.0) is True
        assert _supply_keys_close(60.0, 460.0, 61.0, 460.0) is False

    def test_build_catalog_slices_skips_incomplete_catalog(
        self,
        supply_grid_output_dto: Any,
    ) -> None:
        supply_grid_output_dto.im_pc_catalogs = _catalog_dtos()
        slices = _build_catalog_slices(supply_grid_output_dto)
        assert len(slices) == 1
        assert slices[0].frequency_hz == 60.0
        assert slices[0].voltage_v == 460.0
        assert slices[0].slip.size == 2

    def test_match_catalog_finds_same_supply_condition(
        self,
        supply_grid_output_dto: Any,
    ) -> None:
        supply_grid_output_dto.im_pc_catalogs = _catalog_dtos()
        simulated = _build_simulated_slices(supply_grid_output_dto)[0]
        catalog_slices = _build_catalog_slices(supply_grid_output_dto)
        matched = _match_catalog(simulated, catalog_slices)
        assert matched is not None
        assert matched.frequency_hz == simulated.frequency_hz
        assert matched.voltage_v == simulated.voltage_v
