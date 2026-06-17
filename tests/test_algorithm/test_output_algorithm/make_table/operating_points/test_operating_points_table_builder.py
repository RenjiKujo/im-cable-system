"""``OperatingPointsTableBuilder`` の単体テスト。"""

from __future__ import annotations

from typing import Any, cast

import numpy as np
from pandas import DataFrame

from im_cable_system.engine.algorithm.output_algorithm.make_table.operating_points.table_builder import (  # noqa: E501
    OperatingPointsTableBuilder,
)
from im_cable_system.engine.shared.config import IConfig, ILogger


class TestOperatingPointsTableBuilder:
    """運転点ごと 1 行の性能表を組み立てる。"""

    def _builder(
        self,
        config: IConfig,
        logger: ILogger,
    ) -> OperatingPointsTableBuilder:
        return cast(
            OperatingPointsTableBuilder,
            OperatingPointsTableBuilder.create(
                config=config,
                logger=logger,
            ),
        )

    def test_build_returns_one_row_per_operating_point(
        self,
        config: IConfig,
        logger: ILogger,
        operating_points_output_dto: Any,
    ) -> None:
        table = self._builder(config, logger).build(operating_points_output_dto)
        assert isinstance(table, DataFrame)
        assert len(table) == 4
        assert list(table["operating_point"]) == [0, 1, 2, 3]

    def test_columns_cover_figure_quantities(
        self,
        config: IConfig,
        logger: ILogger,
        operating_points_output_dto: Any,
    ) -> None:
        table = self._builder(config, logger).build(operating_points_output_dto)
        for column in (
            "operating_point",
            "slip",
            "rotational_speed_rpm",
            "input_current_magnitude_a",
            "voltage_v",
            "frequency_hz",
            "output_power_w",
            "torque_nm",
            "efficiency",
            "power_factor",
        ):
            assert column in table.columns
        assert np.isclose(table["frequency_hz"].iloc[0], 50.0)
        assert np.allclose(
            table["efficiency"].to_numpy(), np.linspace(0.7, 0.85, 4)
        )

    def test_missing_supply_axes_drop_columns(
        self,
        config: IConfig,
        logger: ILogger,
        build_operating_points_output_dto: Any,
    ) -> None:
        output_dto = build_operating_points_output_dto(with_supply_axes=False)
        table = self._builder(config, logger).build(output_dto)
        assert "slip" in table.columns
        assert "voltage_v" not in table.columns
        assert "frequency_hz" not in table.columns
        assert "rotational_speed_rpm" in table.columns
