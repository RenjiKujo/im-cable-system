"""FitSummaryCsvExporter の保存契約テスト。"""

from __future__ import annotations

from pathlib import Path

from im_cable_system.engine.algorithm.output_algorithm.export_report.fit_summary_csv_exporter import (  # noqa: E501
    FitSummaryCsvExporter,
)
from im_cable_system.engine.algorithm.output_algorithm.make_report import (
    ReportDto,
)
from im_cable_system.engine.shared.config import IConfig, ILogger


class TestFitSummaryCsvExporter:
    """フィット要約 CSV の保存。"""

    def test_export_writes_csv_under_reports_sub_dir(
        self,
        dump_config: IConfig,
        logger: ILogger,
        sample_report_dto: ReportDto,
        tmp_path: Path,
    ) -> None:
        exporter = FitSummaryCsvExporter.create(
            config=dump_config,
            logger=logger,
        )
        exporter.export(sample_report_dto)

        reports_dir = tmp_path / dump_config.dump_data_config.reports.sub_dir
        saved = list(reports_dir.glob("*.csv"))
        assert len(saved) == 1
        content = saved[0].read_text(encoding="utf-8")
        assert "fit_metric" in content
        assert "im.primary_resistance" in content
