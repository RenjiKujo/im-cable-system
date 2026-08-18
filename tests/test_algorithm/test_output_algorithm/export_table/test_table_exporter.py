"""TableExporter の保存契約テスト。"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from im_cable_system.engine.algorithm.output_algorithm.export_table.table_exporter import (  # noqa: E501
    TableExporter,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ArrayKey,
    ArrayLayoutDto,
    ImCableSystemName,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArraySlipDto,
)
from im_cable_system.engine.shared.dto.output import OutputDto


def _output_dto() -> OutputDto:
    return OutputDto(
        name=ImCableSystemName(base="SYS/01"),
        array_layout=ArrayLayoutDto(
            arrays={
                ArrayKey.SLIP: ArraySlipDto(
                    value=np.array([0.1], dtype=np.float64),
                    unit="-",
                )
            },
            reference_axes=[ArrayKey.SLIP],
        ),
        im=object(),  # type: ignore[arg-type]
        cable=None,
        result=object(),  # type: ignore[arg-type]
    )


class TestTableExporter:
    """``dump_data_config.tables`` に従った CSV 保存。"""

    def test_export_writes_csv_under_dump_base_dir(
        self,
        dump_config: IConfig,
        logger: ILogger,
        tmp_path: Path,
    ) -> None:
        exporter = TableExporter.create(config=dump_config, logger=logger)
        table = pd.DataFrame({"slip": [0.1, 0.2]})
        exporter.export(table=table, output_dto=_output_dto())

        tables_dir = tmp_path / dump_config.dump_data_config.tables.sub_dir
        saved = list(tables_dir.glob("*.csv"))
        assert len(saved) == 1
        assert "SYS_01" in saved[0].name

    def test_export_skips_empty_dataframe(
        self,
        dump_config: IConfig,
        logger: ILogger,
        tmp_path: Path,
    ) -> None:
        exporter = TableExporter.create(config=dump_config, logger=logger)
        exporter.export(table=pd.DataFrame(), output_dto=_output_dto())

        tables_dir = tmp_path / dump_config.dump_data_config.tables.sub_dir
        assert not tables_dir.exists() or list(tables_dir.glob("*.csv")) == []
