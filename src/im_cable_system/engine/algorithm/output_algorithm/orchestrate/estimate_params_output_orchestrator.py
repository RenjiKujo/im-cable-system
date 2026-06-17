"""EstimateParams モードの出力オーケストレーター実装。

推定結果を supply_grid 形状の Figure（slip 横軸 / 出力比横軸）で出力しつつ、
estimate_params 固有の **1 件分の構造化レポート**（フィット要約 CSV ＋ 推定モデル
catalog 形式 YAML ＋ 数値安定化イベント CSV）も出力する。
convert → make_figure → (保存 / 表示) → make_table → 保存 → make_report → 各
artifact 保存 を実行する。

レポート系 3 ファイルはいずれも make_report が組み立てた ``ReportDto`` を入力に
保存する（数値安定化イベントも ``ReportDto`` 経由）。Itm 横断の集計を要さない
ため、他の出力と同じく per-itm（1 Itm = 1 ファイル）で run() 内に閉じる。

NOTE: Forward 系と figure/table の run / ゲートが重複するが、出力モードごとに
    オーケストレーターを独立させる方針のため、意図的に共通化しない。
"""

from __future__ import annotations

import matplotlib.pyplot as plt

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
from im_cable_system.engine.algorithm.output_algorithm.i_output_orchestrator import (  # noqa: E501
    IOutputOrchestrator,
)
from im_cable_system.engine.algorithm.output_algorithm.make_figure.i_figure_builder import (  # noqa: E501
    IFigureBuilder,
)
from im_cable_system.engine.algorithm.output_algorithm.make_figure.supply_grid.output_ratio_axis.figure_builder import (  # noqa: E501
    SupplyGridOutputRatioFigureBuilder,
)
from im_cable_system.engine.algorithm.output_algorithm.make_figure.supply_grid.slip_axis.figure_builder import (  # noqa: E501
    SupplyGridSlipAxisFigureBuilder,
)
from im_cable_system.engine.algorithm.output_algorithm.make_report import (
    EstimateParamsReportBuilder,
    IReportBuilder,
)
from im_cable_system.engine.algorithm.output_algorithm.make_table.i_table_builder import (  # noqa: E501
    ITableBuilder,
)
from im_cable_system.engine.algorithm.output_algorithm.make_table.supply_grid.table_builder import (  # noqa: E501
    SupplyGridTableBuilder,
)
from im_cable_system.engine.shared.config import IConfig, ILogger, timer
from im_cable_system.engine.shared.dto.itm import ItmDto
from im_cable_system.engine.shared.dto.output import OutputDto

_FIGURE_KIND_SLIP_AXIS = "slip_axis"
_FIGURE_KIND_OUTPUT_RATIO_AXIS = "output_ratio_axis"


class EstimateParamsOutputOrchestrator(IOutputOrchestrator):
    """EstimateParams モードの slip 軸グリッド出力＋レポートを束ねる。"""

    def __init__(
        self,
        config: IConfig,
        logger: ILogger,
        converter: IOutputDtoConverter,
        figure_builders: tuple[tuple[str, IFigureBuilder], ...],
        table_builder: ITableBuilder,
        figure_exporter: IFigureExporter,
        figure_displayer: IFigureDisplayer,
        table_exporter: ITableExporter,
        report_builder: IReportBuilder,
        report_exporters: tuple[IReportArtifactExporter, ...],
    ) -> None:
        """インスタンスを初期化する。

        Args:
            config: 設定オブジェクト。
            logger: ロガーオブジェクト。
            converter: ItmDto → OutputDto 変換ステップ。
            figure_builders: Figure 種別と build ステップのペア。
            table_builder: 表 build ステップ。
            figure_exporter: Figure 保存ステップ。
            figure_displayer: Figure 表示ステップ。
            table_exporter: 表 保存ステップ。
            report_builder: 1 件分レポート build ステップ。
            report_exporters: 1 件分レポートの各 artifact 保存ステップ
                （フィット要約 CSV / catalog YAML / 数値安定化 CSV）。
        """
        self._config: IConfig = config
        self._logger: ILogger = logger
        self._converter: IOutputDtoConverter = converter
        self._figure_builders: tuple[tuple[str, IFigureBuilder], ...] = (
            figure_builders
        )
        self._table_builder: ITableBuilder = table_builder
        self._figure_exporter: IFigureExporter = figure_exporter
        self._figure_displayer: IFigureDisplayer = figure_displayer
        self._table_exporter: ITableExporter = table_exporter
        self._report_builder: IReportBuilder = report_builder
        self._report_exporters: tuple[IReportArtifactExporter, ...] = (
            report_exporters
        )

    @classmethod
    def create(
        cls,
        config: IConfig,
        logger: ILogger,
    ) -> IOutputOrchestrator:
        """EstimateParams 系の各ステップを生成・配線して返す。"""
        return cls(
            config=config,
            logger=logger,
            converter=OutputDtoConverter.create(config=config, logger=logger),
            figure_builders=(
                (
                    _FIGURE_KIND_SLIP_AXIS,
                    SupplyGridSlipAxisFigureBuilder.create(
                        config=config,
                        logger=logger,
                    ),
                ),
                (
                    _FIGURE_KIND_OUTPUT_RATIO_AXIS,
                    SupplyGridOutputRatioFigureBuilder.create(
                        config=config,
                        logger=logger,
                    ),
                ),
            ),
            table_builder=SupplyGridTableBuilder.create(
                config=config,
                logger=logger,
            ),
            figure_exporter=FigureExporter.create(
                config=config,
                logger=logger,
            ),
            figure_displayer=FigureDisplayer.create(
                config=config,
                logger=logger,
            ),
            table_exporter=TableExporter.create(config=config, logger=logger),
            report_builder=EstimateParamsReportBuilder.create(
                config=config,
                logger=logger,
            ),
            report_exporters=(
                FitSummaryCsvExporter.create(config=config, logger=logger),
                FittedCatalogYamlExporter.create(config=config, logger=logger),
                NumericalStabilityCsvExporter.create(
                    config=config,
                    logger=logger,
                ),
            ),
        )

    @timer(logger=None, line="#", min_duration=0.01)
    def run(self, itm_dto: ItmDto) -> OutputDto:
        """convert → (figure 保存/表示) → (table 保存) → (report 保存) を実行する。

        figure / table / report のエクスポート可否は config で **個別** に
        判定する（``dump.output.figures.enabled`` /
        ``calculation.output.figures.show`` / ``dump.output.tables.enabled`` /
        ``dump.output.reports.enabled``）。report 出力では 1 件分の ``ReportDto``
        を組み立て、各 artifact（フィット要約 CSV / catalog YAML / 数値安定化
        CSV）を保存する。``ReportDto`` が None（フィット要約無し）のときは何も
        保存しない。
        """
        output_dto = self._converter.convert(itm_dto)
        if self._is_figure_enabled() or self._is_figure_show():
            for figure_kind, figure_builder in self._figure_builders:
                figure = figure_builder.build(output_dto)
                # 保存・表示後は figure を必ず閉じる（保存のみの経路でも
                # matplotlib のメモリリークを防ぐ。close は冪等のため表示側で
                # 既に閉じていても問題ない）。
                try:
                    if self._is_figure_enabled():
                        self._figure_exporter.export(
                            figure=figure,
                            output_dto=output_dto,
                            kind=figure_kind,
                        )
                    if self._is_figure_show():
                        self._figure_displayer.show(
                            figure=figure,
                            output_dto=output_dto,
                        )
                finally:
                    plt.close(figure)
        if self._is_table_enabled():
            table = self._table_builder.build(output_dto)
            self._table_exporter.export(table=table, output_dto=output_dto)
        if self._is_report_enabled():
            report = self._report_builder.build(output_dto)
            if report is not None:
                for report_exporter in self._report_exporters:
                    report_exporter.export(report)
        return output_dto

    def _is_figure_enabled(self) -> bool:
        """Figure 保存可否を config から判定する。"""
        return self._config.dump_data_config.figures.enabled

    def _is_figure_show(self) -> bool:
        """Figure 表示可否を config から判定する。"""
        return self._config.output_figures_config.show

    def _is_table_enabled(self) -> bool:
        """表 保存可否を config から判定する。"""
        return self._config.dump_data_config.tables.enabled

    def _is_report_enabled(self) -> bool:
        """レポート保存可否を config から判定する。"""
        return self._config.dump_data_config.reports.enabled
