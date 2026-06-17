"""``build_catalog_columns`` の単体テスト。"""

from __future__ import annotations

import numpy as np

from im_cable_system.engine.algorithm.output_algorithm.make_table.supply_grid.catalog_columns import (  # noqa: E501, PLC2701
    build_catalog_columns,
)
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ImPerformanceCurveCatalogDtos,
)
from tests.test_algorithm.test_output_algorithm.make_table.supply_grid._supply_grid_helpers import (  # noqa: E501
    catalog_dtos,
    output_dto_stub,
)


class TestBuildCatalogColumns:
    """表行へのカタログ参照列のマージ。"""

    def test_returns_empty_when_no_catalog(self) -> None:
        slip = np.array([0.1, 0.2, 0.1, 0.2], dtype=np.float64)
        voltage_v = np.array([200.0, 200.0, 460.0, 460.0], dtype=np.float64)
        frequency_hz = np.array([60.0, 60.0, 60.0, 60.0], dtype=np.float64)
        output_dto = output_dto_stub(ImPerformanceCurveCatalogDtos(objects=[]))

        columns = build_catalog_columns(
            output_dto,
            voltage_v=voltage_v,
            frequency_hz=frequency_hz,
            slip=slip,
        )

        assert columns == {}

    def test_fills_matching_supply_and_slip_rows(self) -> None:
        slip = np.array([0.1, 0.2, 0.1, 0.2], dtype=np.float64)
        voltage_v = np.array([200.0, 200.0, 460.0, 460.0], dtype=np.float64)
        frequency_hz = np.array([60.0, 60.0, 60.0, 60.0], dtype=np.float64)
        output_dto = output_dto_stub(catalog_dtos())

        columns = build_catalog_columns(
            output_dto,
            voltage_v=voltage_v,
            frequency_hz=frequency_hz,
            slip=slip,
        )

        np.testing.assert_array_equal(
            columns["catalog_output_power_w"],
            np.array([np.nan, np.nan, 1.0, 2.0]),
        )
