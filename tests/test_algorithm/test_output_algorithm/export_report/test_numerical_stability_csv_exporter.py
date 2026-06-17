"""NumericalStabilityCsvExporter の保存契約テスト。"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from im_cable_system.engine.algorithm.output_algorithm.export_report.numerical_stability_csv_exporter import (  # noqa: E501
    NumericalStabilityCsvExporter,
)
from im_cable_system.engine.algorithm.output_algorithm.make_report import (
    ReportDto,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.generic.reporting import (
    NumericalStabilityReportDto,
)


class TestNumericalStabilityCsvExporter:
    """数値安定化イベント CSV の保存。"""

    def test_export_skips_empty_report(
        self,
        dump_config: IConfig,
        logger: ILogger,
        sample_report_dto: ReportDto,
        tmp_path: Path,
    ) -> None:
        exporter = NumericalStabilityCsvExporter.create(
            config=dump_config,
            logger=logger,
        )
        exporter.export(sample_report_dto)

        reports_dir = tmp_path / dump_config.dump_data_config.reports.sub_dir
        assert not reports_dir.exists() or list(reports_dir.glob("*.csv")) == []

    def test_export_writes_csv_when_events_present(
        self,
        dump_config: IConfig,
        logger: ILogger,
        sample_report_dto: ReportDto,
        tmp_path: Path,
    ) -> None:
        report = replace(
            sample_report_dto,
            numerical_stability_report=NumericalStabilityReportDto(
                event_counts=(("clamp_zero", 2),),
            ),
        )
        exporter = NumericalStabilityCsvExporter.create(
            config=dump_config,
            logger=logger,
        )
        exporter.export(report)

        reports_dir = tmp_path / dump_config.dump_data_config.reports.sub_dir
        saved = list(reports_dir.glob("*.csv"))
        assert len(saved) == 1
        content = saved[0].read_text(encoding="utf-8")
        assert "clamp_zero" in content
        assert "SYS01" in content
