"""1 件分の推定モデルを catalog 形式 YAML として保存する。

YAML は推定モデル（モデルラベル・名板値・推定パラメータ・適合指標）を
catalog 形式で表したマッピング。
"""

from __future__ import annotations

import yaml

from im_cable_system.engine.algorithm.output_algorithm.export_report.i_report_artifact_exporter import (  # noqa: E501
    IReportArtifactExporter,
)
from im_cable_system.engine.algorithm.output_algorithm.export_report.report_paths import (  # noqa: E501
    current_timestamp,
    format_report_filename,
    resolve_report_path,
    safe_system_name,
)
from im_cable_system.engine.algorithm.output_algorithm.make_report import (
    ReportDto,
)
from im_cable_system.engine.shared.config import IConfig, ILogger


class FittedCatalogYamlExporter(IReportArtifactExporter):
    """1 件分の推定モデルを catalog 形式 YAML で保存する。"""

    def __init__(self, config: IConfig, logger: ILogger) -> None:
        """インスタンスを初期化する。"""
        self._config: IConfig = config
        self._logger: ILogger = logger

    @classmethod
    def create(
        cls,
        config: IConfig,
        logger: ILogger,
    ) -> IReportArtifactExporter:
        """エクスポーターのインスタンスを生成する。"""
        return cls(config=config, logger=logger)

    def export(self, report: ReportDto) -> None:
        """推定モデルの catalog 形式 YAML を保存する。"""
        reports_config = self._config.dump_data_config.reports
        filename = format_report_filename(
            reports_config.fitted_catalog_pattern,
            timestamp=current_timestamp(self._config),
            im_cable_system_name=safe_system_name(report.name),
        )
        out_path = resolve_report_path(
            self._config,
            sub_dir=reports_config.sub_dir,
            filename=filename,
        )
        with out_path.open("w", encoding="utf-8") as handle:
            yaml.safe_dump(
                report.fitted_catalog,
                handle,
                allow_unicode=True,
                sort_keys=False,
            )
        self._logger.info("Report fitted catalog YAML saved to %s", out_path)
