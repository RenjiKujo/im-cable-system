"""output orchestrator 配線テスト用の fake ステップとビルダー（共有ヘルパー）。

各オーケストレーターは ``ItmDto`` / ``OutputDto`` を不透明に扱うため、
配線テストでは sentinel オブジェクトで呼び出し順序と config ゲートのみを
検証する。
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, cast

from matplotlib.figure import Figure

from im_cable_system.engine.algorithm.output_algorithm.convert.i_output_dto_converter import (  # noqa: E501
    IOutputDtoConverter,
)
from im_cable_system.engine.algorithm.output_algorithm.display_figure.i_figure_displayer import (  # noqa: E501
    IFigureDisplayer,
)
from im_cable_system.engine.algorithm.output_algorithm.export_figure.i_figure_exporter import (  # noqa: E501
    IFigureExporter,
)
from im_cable_system.engine.algorithm.output_algorithm.export_report.i_report_artifact_exporter import (  # noqa: E501
    IReportArtifactExporter,
)
from im_cable_system.engine.algorithm.output_algorithm.export_table.i_table_exporter import (  # noqa: E501
    ITableExporter,
)
from im_cable_system.engine.algorithm.output_algorithm.i_output_orchestrator import (  # noqa: E501
    IOutputOrchestrator,
)
from im_cable_system.engine.algorithm.output_algorithm.make_figure.i_figure_builder import (  # noqa: E501
    IFigureBuilder,
)
from im_cable_system.engine.algorithm.output_algorithm.make_report.i_report_builder import (  # noqa: E501
    IReportBuilder,
)
from im_cable_system.engine.algorithm.output_algorithm.make_table.i_table_builder import (  # noqa: E501
    ITableBuilder,
)
from im_cable_system.engine.algorithm.output_algorithm.orchestrate.estimate_params_output_orchestrator import (  # noqa: E501
    EstimateParamsOutputOrchestrator,
)
from im_cable_system.engine.algorithm.output_algorithm.orchestrate.forward_by_cartesian_grid_output_orchestrator import (  # noqa: E501
    ForwardByCartesianGridOutputOrchestrator,
)
from im_cable_system.engine.algorithm.output_algorithm.orchestrate.forward_by_operating_points_output_orchestrator import (  # noqa: E501
    ForwardByOperatingPointsOutputOrchestrator,
)
from im_cable_system.engine.shared.config import ILogger

# Figure sentinel は実 Figure とする（orchestrator が build 後に
# ``plt.close(figure)`` を呼ぶため、object() だと TypeError になる）。
# pyplot 管理外の Figure なので close は安全な no-op になる。
OUTPUT_SENTINEL: Any = object()
FIGURE_SENTINEL: Any = Figure()
OUTPUT_RATIO_FIGURE_SENTINEL: Any = Figure()
TABLE_SENTINEL: Any = object()
REPORT_SENTINEL: Any = object()
ITM_SENTINEL: Any = object()

FORWARD_ORCHESTRATOR_CLASSES: list[type[Any]] = [
    ForwardByCartesianGridOutputOrchestrator,
    ForwardByOperatingPointsOutputOrchestrator,
]
ALL_ORCHESTRATOR_CLASSES: list[type[Any]] = [
    ForwardByCartesianGridOutputOrchestrator,
    ForwardByOperatingPointsOutputOrchestrator,
    EstimateParamsOutputOrchestrator,
]


class FakeConverter(IOutputDtoConverter):
    """convert 呼び出しを記録する fake converter。"""

    def __init__(self) -> None:
        self.calls: list[Any] = []

    @classmethod
    def create(cls, config: Any, logger: Any) -> IOutputDtoConverter:  # noqa: ARG003
        return cls()

    def convert(self, itm_dto: Any) -> Any:
        self.calls.append(itm_dto)
        return OUTPUT_SENTINEL


class FakeFigureBuilder(IFigureBuilder):
    """build 呼び出しを記録する fake figure builder。"""

    def __init__(self, figure: Any = FIGURE_SENTINEL) -> None:
        self.built: list[Any] = []
        self._figure: Any = figure

    @classmethod
    def create(cls, config: Any, logger: Any) -> IFigureBuilder:  # noqa: ARG003
        return cls()

    def build(self, output_dto: Any) -> Any:
        self.built.append(output_dto)
        return self._figure


class FakeTableBuilder(ITableBuilder):
    """build 呼び出しを記録する fake table builder。"""

    def __init__(self) -> None:
        self.built: list[Any] = []

    @classmethod
    def create(cls, config: Any, logger: Any) -> ITableBuilder:  # noqa: ARG003
        return cls()

    def build(self, output_dto: Any) -> Any:
        self.built.append(output_dto)
        return TABLE_SENTINEL


class FakeFigureExporter(IFigureExporter):
    """export 呼び出しを記録する fake figure exporter。"""

    def __init__(self) -> None:
        self.exported: list[tuple[Any, Any, str]] = []

    @classmethod
    def create(cls, config: Any, logger: Any) -> IFigureExporter:  # noqa: ARG003
        return cls()

    def export(
        self,
        figure: Any,
        output_dto: Any,
        *,
        kind: str = "figure",
    ) -> None:
        self.exported.append((figure, output_dto, kind))


class FakeFigureDisplayer(IFigureDisplayer):
    """show 呼び出しを記録する fake figure displayer。"""

    def __init__(self) -> None:
        self.shown: list[tuple[Any, Any]] = []

    @classmethod
    def create(cls, config: Any, logger: Any) -> IFigureDisplayer:  # noqa: ARG003
        return cls()

    def show(self, figure: Any, output_dto: Any) -> None:
        self.shown.append((figure, output_dto))


class FakeTableExporter(ITableExporter):
    """export 呼び出しを記録する fake table exporter。"""

    def __init__(self) -> None:
        self.exported: list[tuple[Any, Any]] = []

    @classmethod
    def create(cls, config: Any, logger: Any) -> ITableExporter:  # noqa: ARG003
        return cls()

    def export(self, table: Any, output_dto: Any) -> None:
        self.exported.append((table, output_dto))


class FakeReportBuilder(IReportBuilder):
    """build 呼び出しを記録する fake report builder。"""

    def __init__(self) -> None:
        self.built: list[Any] = []

    @classmethod
    def create(cls, config: Any, logger: Any) -> IReportBuilder:  # noqa: ARG003
        return cls()

    def build(self, output_dto: Any) -> Any:
        self.built.append(output_dto)
        return REPORT_SENTINEL


class FakeReportArtifactExporter(IReportArtifactExporter):
    """export 呼び出しを記録する fake report artifact exporter。"""

    def __init__(self) -> None:
        self.exported: list[Any] = []

    @classmethod
    def create(
        cls,
        config: Any,  # noqa: ARG003
        logger: Any,  # noqa: ARG003
    ) -> IReportArtifactExporter:
        return cls()

    def export(self, report: Any) -> None:
        self.exported.append(report)


def config_stub(
    *,
    figure_enabled: bool,
    figure_show: bool,
    table_enabled: bool,
    report_enabled: bool = False,
) -> Any:
    """orchestrator が参照する config の stub。"""
    return SimpleNamespace(
        dump_data_config=SimpleNamespace(
            figures=SimpleNamespace(enabled=figure_enabled),
            tables=SimpleNamespace(enabled=table_enabled),
            reports=SimpleNamespace(enabled=report_enabled),
        ),
        output_figures_config=SimpleNamespace(
            show=figure_show,
            show_duration_seconds=3.0,
        ),
    )


def build_forward_orchestrator(
    orchestrator_cls: type[Any],
    *,
    figure_enabled: bool,
    figure_show: bool,
    table_enabled: bool,
) -> tuple[
    IOutputOrchestrator,
    FakeConverter,
    tuple[FakeFigureBuilder, ...],
    FakeTableBuilder,
    FakeFigureExporter,
    FakeFigureDisplayer,
    FakeTableExporter,
]:
    """Forward 系 orchestrator に fake ステップを注入して返す。"""
    converter = FakeConverter()
    figure_builder = FakeFigureBuilder()
    output_ratio_figure_builder = FakeFigureBuilder(
        figure=OUTPUT_RATIO_FIGURE_SENTINEL
    )
    table_builder = FakeTableBuilder()
    figure_exporter = FakeFigureExporter()
    figure_displayer = FakeFigureDisplayer()
    table_exporter = FakeTableExporter()
    kwargs: dict[str, Any] = {
        "config": config_stub(
            figure_enabled=figure_enabled,
            figure_show=figure_show,
            table_enabled=table_enabled,
        ),
        "logger": SimpleNamespace(info=lambda *_args, **_kwargs: None),
        "converter": converter,
        "table_builder": table_builder,
        "figure_exporter": figure_exporter,
        "figure_displayer": figure_displayer,
        "table_exporter": table_exporter,
    }
    if orchestrator_cls is ForwardByCartesianGridOutputOrchestrator:
        kwargs["figure_builders"] = (
            ("slip_axis", figure_builder),
            ("output_ratio_axis", output_ratio_figure_builder),
        )
        figure_builders: tuple[FakeFigureBuilder, ...] = (
            figure_builder,
            output_ratio_figure_builder,
        )
    else:
        kwargs["figure_builder"] = figure_builder
        figure_builders = (figure_builder,)
    orchestrator = orchestrator_cls(**kwargs)
    return (
        orchestrator,
        converter,
        figure_builders,
        table_builder,
        figure_exporter,
        figure_displayer,
        table_exporter,
    )


def build_estimate_params_orchestrator(
    *,
    figure_enabled: bool,
    figure_show: bool,
    table_enabled: bool,
    report_enabled: bool,
) -> tuple[
    IOutputOrchestrator,
    FakeReportBuilder,
    tuple[FakeReportArtifactExporter, ...],
]:
    """EstimateParams orchestrator に fake ステップを注入して返す。"""
    report_builder = FakeReportBuilder()
    report_exporters = (
        FakeReportArtifactExporter(),
        FakeReportArtifactExporter(),
        FakeReportArtifactExporter(),
    )
    figure_builder = FakeFigureBuilder()
    output_ratio_figure_builder = FakeFigureBuilder(
        figure=OUTPUT_RATIO_FIGURE_SENTINEL
    )
    orchestrator = EstimateParamsOutputOrchestrator(
        config=config_stub(
            figure_enabled=figure_enabled,
            figure_show=figure_show,
            table_enabled=table_enabled,
            report_enabled=report_enabled,
        ),
        logger=cast(
            ILogger,
            SimpleNamespace(info=lambda *_args, **_kwargs: None),
        ),
        converter=FakeConverter(),
        figure_builders=(
            ("slip_axis", figure_builder),
            ("output_ratio_axis", output_ratio_figure_builder),
        ),
        table_builder=FakeTableBuilder(),
        figure_exporter=FakeFigureExporter(),
        figure_displayer=FakeFigureDisplayer(),
        table_exporter=FakeTableExporter(),
        report_builder=report_builder,
        report_exporters=report_exporters,
    )
    return (
        orchestrator,
        report_builder,
        report_exporters,
    )


def figure_builder_calls(
    figure_builders: tuple[FakeFigureBuilder, ...],
) -> list[Any]:
    """複数 Figure builder の build 呼び出し履歴を平坦化する。"""
    calls: list[Any] = []
    for figure_builder in figure_builders:
        calls.extend(figure_builder.built)
    return calls


def expected_figure_exports(
    orchestrator_cls: type[Any],
) -> list[tuple[Any, Any, str]]:
    """orchestrator ごとの Figure 保存期待値を返す。"""
    if orchestrator_cls is ForwardByCartesianGridOutputOrchestrator:
        return [
            (FIGURE_SENTINEL, OUTPUT_SENTINEL, "slip_axis"),
            (
                OUTPUT_RATIO_FIGURE_SENTINEL,
                OUTPUT_SENTINEL,
                "output_ratio_axis",
            ),
        ]
    if orchestrator_cls is ForwardByOperatingPointsOutputOrchestrator:
        return [(FIGURE_SENTINEL, OUTPUT_SENTINEL, "operating_points")]
    return [(FIGURE_SENTINEL, OUTPUT_SENTINEL, "figure")]


def expected_figure_displays(
    orchestrator_cls: type[Any],
) -> list[tuple[Any, Any]]:
    """orchestrator ごとの Figure 表示期待値を返す。"""
    if orchestrator_cls is ForwardByCartesianGridOutputOrchestrator:
        return [
            (FIGURE_SENTINEL, OUTPUT_SENTINEL),
            (OUTPUT_RATIO_FIGURE_SENTINEL, OUTPUT_SENTINEL),
        ]
    return [(FIGURE_SENTINEL, OUTPUT_SENTINEL)]
