"""FittedCatalogYamlExporter の保存契約テスト。"""

from __future__ import annotations

from pathlib import Path

import yaml

from im_cable_system.engine.algorithm.output_algorithm.export_report.fitted_catalog_yaml_exporter import (  # noqa: E501
    FittedCatalogYamlExporter,
)
from im_cable_system.engine.algorithm.output_algorithm.make_report import (
    ReportDto,
)
from im_cable_system.engine.shared.config import IConfig, ILogger


class TestFittedCatalogYamlExporter:
    """catalog 形式 YAML の保存。"""

    def test_export_writes_yaml_under_reports_sub_dir(
        self,
        dump_config: IConfig,
        logger: ILogger,
        sample_report_dto: ReportDto,
        tmp_path: Path,
    ) -> None:
        exporter = FittedCatalogYamlExporter.create(
            config=dump_config,
            logger=logger,
        )
        exporter.export(sample_report_dto)

        reports_dir = tmp_path / dump_config.dump_data_config.reports.sub_dir
        saved = list(reports_dir.glob("*.yaml"))
        assert len(saved) == 1
        loaded = yaml.safe_load(saved[0].read_text(encoding="utf-8"))
        assert loaded["name"] == "SYS01"
