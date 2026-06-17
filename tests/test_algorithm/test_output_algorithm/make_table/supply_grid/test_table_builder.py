"""SupplyGridTableBuilder.build の列順・行順・カタログ重ねテスト。"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import numpy as np

from im_cable_system.engine.algorithm.output_algorithm.make_table.supply_grid.table_builder import (  # noqa: E501
    SupplyGridTableBuilder,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ArrayKey,
    ArrayLayoutDto,
    ImPerformanceCurveCatalogDtos,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArraySlipDto,
)
from tests.test_algorithm.test_output_algorithm.make_table.supply_grid._supply_grid_helpers import (  # noqa: E501
    catalog_dtos,
    output_dto_stub,
    result_stub,
)


class TestSupplyGridTableBuilder:
    """SupplyGridTableBuilder.build の契約テスト。"""

    def test_first_three_columns_and_row_order(
        self,
        config: IConfig,
        logger: ILogger,
    ) -> None:
        builder = SupplyGridTableBuilder.create(config=config, logger=logger)

        table = builder.build(
            output_dto_stub(ImPerformanceCurveCatalogDtos(objects=[]))
        )

        assert list(table.columns[:3]) == ["voltage_v", "frequency_hz", "slip"]
        assert table["voltage_v"].tolist() == [200.0, 200.0, 460.0, 460.0]
        assert table["frequency_hz"].tolist() == [60.0, 60.0, 60.0, 60.0]
        assert table["slip"].tolist() == [0.1, 0.2, 0.1, 0.2]
        assert table["output_power_w"].tolist() == [0.0, 100.0, 1.0, 101.0]

    def test_catalog_columns_merged_on_matching_rows(
        self,
        config: IConfig,
        logger: ILogger,
    ) -> None:
        builder = SupplyGridTableBuilder.create(config=config, logger=logger)

        table = builder.build(output_dto_stub(catalog_dtos()))

        assert "catalog_torque_nm" not in table.columns
        assert "catalog_rotational_speed_rpm" not in table.columns
        np.testing.assert_array_equal(
            table["catalog_output_power_w"].to_numpy(),
            np.array([np.nan, np.nan, 1.0, 2.0]),
        )
        np.testing.assert_array_equal(
            table["catalog_input_current_magnitude_a"].to_numpy(),
            np.array([np.nan, np.nan, 10.0, 20.0]),
        )
        np.testing.assert_array_equal(
            table["catalog_power_factor"].to_numpy(),
            np.array([np.nan, np.nan, 0.8, 0.9]),
        )
        np.testing.assert_array_equal(
            table["catalog_efficiency"].to_numpy(),
            np.array([np.nan, np.nan, 0.85, 0.95]),
        )

    def test_returns_empty_when_required_axes_missing(
        self,
        config: IConfig,
        logger: ILogger,
    ) -> None:
        builder = SupplyGridTableBuilder.create(config=config, logger=logger)
        layout = ArrayLayoutDto(
            arrays={
                ArrayKey.SLIP: ArraySlipDto(
                    value=np.array([0.1, 0.2]), unit="-"
                ),
            },
            reference_axes=[ArrayKey.SLIP],
        )
        base = output_dto_stub(ImPerformanceCurveCatalogDtos(objects=[]))
        output_dto: Any = SimpleNamespace(
            name=base.name,
            array_layout=layout,
            result=result_stub(),
            im_pc_catalogs=base.im_pc_catalogs,
        )

        table = builder.build(output_dto)

        assert table.empty
