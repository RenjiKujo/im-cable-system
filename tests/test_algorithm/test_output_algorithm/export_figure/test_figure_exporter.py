"""FigureExporter の保存契約テスト。"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from im_cable_system.engine.algorithm.output_algorithm.export_figure.figure_exporter import (  # noqa: E501
    FigureExporter,
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


class TestFigureExporter:
    """``dump_data_config.figures`` に従った保存。"""

    def test_export_writes_png_under_dump_base_dir(
        self,
        dump_config: IConfig,
        logger: ILogger,
        tmp_path: Path,
    ) -> None:
        exporter = FigureExporter.create(config=dump_config, logger=logger)
        figure = plt.figure()
        exporter.export(
            figure=figure, output_dto=_output_dto(), kind="slip_axis"
        )
        plt.close(figure)

        figures_dir = tmp_path / dump_config.dump_data_config.figures.sub_dir
        saved = list(figures_dir.glob("*.png"))
        assert len(saved) == 1
        assert "slip_axis" in saved[0].name
        assert "SYS_01" in saved[0].name
