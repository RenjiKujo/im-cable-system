"""output_algorithm 各ステップの ``create`` 契約テスト。

内部実装の単体テスト。``convert`` / ``make_*`` / ``export_figure`` /
``display_figure`` / ``export_table`` は orchestrate 内部ステップのため
リーフ直 import とする。``export_report`` は公開窓口経由。
"""

from __future__ import annotations

from im_cable_system.engine.algorithm.output_algorithm.convert.i_output_dto_converter import (  # noqa: E501
    IOutputDtoConverter,
)
from im_cable_system.engine.algorithm.output_algorithm.convert.output_dto_converter import (  # noqa: E501
    OutputDtoConverter,
)
from im_cable_system.engine.algorithm.output_algorithm.display_figure.figure_displayer import (  # noqa: E501
    FigureDisplayer,
)
from im_cable_system.engine.algorithm.output_algorithm.display_figure.i_figure_displayer import (  # noqa: E501
    IFigureDisplayer,
)
from im_cable_system.engine.algorithm.output_algorithm.export_figure.figure_exporter import (  # noqa: E501
    FigureExporter,
)
from im_cable_system.engine.algorithm.output_algorithm.export_figure.i_figure_exporter import (  # noqa: E501
    IFigureExporter,
)
from im_cable_system.engine.algorithm.output_algorithm.export_report import (
    FitSummaryCsvExporter,
    FittedCatalogYamlExporter,
    IReportArtifactExporter,
    NumericalStabilityCsvExporter,
)
from im_cable_system.engine.algorithm.output_algorithm.export_table.i_table_exporter import (  # noqa: E501
    ITableExporter,
)
from im_cable_system.engine.algorithm.output_algorithm.export_table.table_exporter import (  # noqa: E501
    TableExporter,
)
from im_cable_system.engine.algorithm.output_algorithm.make_figure.i_figure_builder import (  # noqa: E501
    IFigureBuilder,
)
from im_cable_system.engine.algorithm.output_algorithm.make_figure.operating_points.figure_builder import (  # noqa: E501
    OperatingPointsFigureBuilder,
)
from im_cable_system.engine.algorithm.output_algorithm.make_figure.supply_grid.output_ratio_axis.figure_builder import (  # noqa: E501
    SupplyGridOutputRatioFigureBuilder,
)
from im_cable_system.engine.algorithm.output_algorithm.make_figure.supply_grid.slip_axis.figure_builder import (  # noqa: E501
    SupplyGridSlipAxisFigureBuilder,
)
from im_cable_system.engine.algorithm.output_algorithm.make_report.estimate_params.report_builder import (  # noqa: E501
    EstimateParamsReportBuilder,
)
from im_cable_system.engine.algorithm.output_algorithm.make_report.i_report_builder import (  # noqa: E501
    IReportBuilder,
)
from im_cable_system.engine.algorithm.output_algorithm.make_table.i_table_builder import (  # noqa: E501
    ITableBuilder,
)
from im_cable_system.engine.algorithm.output_algorithm.make_table.operating_points.table_builder import (  # noqa: E501
    OperatingPointsTableBuilder,
)
from im_cable_system.engine.algorithm.output_algorithm.make_table.supply_grid.table_builder import (  # noqa: E501
    SupplyGridTableBuilder,
)
from im_cable_system.engine.shared.config import IConfig, ILogger


class TestSupplyGridStepFactories:
    """supply_grid 系 builder の ``create`` 契約。"""

    def test_builders_return_interfaces(
        self,
        config: IConfig,
        logger: ILogger,
    ) -> None:
        assert isinstance(
            SupplyGridSlipAxisFigureBuilder.create(
                config=config,
                logger=logger,
            ),
            IFigureBuilder,
        )
        assert isinstance(
            SupplyGridOutputRatioFigureBuilder.create(
                config=config,
                logger=logger,
            ),
            IFigureBuilder,
        )
        assert isinstance(
            SupplyGridTableBuilder.create(config=config, logger=logger),
            ITableBuilder,
        )


class TestOperatingPointsStepFactories:
    """operating_points 系 builder の ``create`` 契約。"""

    def test_builders_return_interfaces(
        self,
        config: IConfig,
        logger: ILogger,
    ) -> None:
        assert isinstance(
            OperatingPointsFigureBuilder.create(config=config, logger=logger),
            IFigureBuilder,
        )
        assert isinstance(
            OperatingPointsTableBuilder.create(config=config, logger=logger),
            ITableBuilder,
        )


class TestReportStepFactories:
    """make_report / export_report ステップの ``create`` 契約。"""

    def test_builders_and_exporters_return_interfaces(
        self,
        config: IConfig,
        logger: ILogger,
    ) -> None:
        assert isinstance(
            EstimateParamsReportBuilder.create(config=config, logger=logger),
            IReportBuilder,
        )
        assert isinstance(
            FitSummaryCsvExporter.create(config=config, logger=logger),
            IReportArtifactExporter,
        )
        assert isinstance(
            FittedCatalogYamlExporter.create(config=config, logger=logger),
            IReportArtifactExporter,
        )
        assert isinstance(
            NumericalStabilityCsvExporter.create(config=config, logger=logger),
            IReportArtifactExporter,
        )


class TestSharedStepFactories:
    """convert / export / display の共通ステップ ``create`` 契約。"""

    def test_steps_return_interfaces(
        self,
        config: IConfig,
        logger: ILogger,
    ) -> None:
        assert isinstance(
            OutputDtoConverter.create(config=config, logger=logger),
            IOutputDtoConverter,
        )
        assert isinstance(
            FigureExporter.create(config=config, logger=logger),
            IFigureExporter,
        )
        assert isinstance(
            FigureDisplayer.create(config=config, logger=logger),
            IFigureDisplayer,
        )
        assert isinstance(
            TableExporter.create(config=config, logger=logger),
            ITableExporter,
        )
