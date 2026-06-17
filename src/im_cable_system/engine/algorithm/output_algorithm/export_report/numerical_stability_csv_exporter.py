"""estimate_params 1 件分の数値安定化イベント CSV。

1 行は ``[im_cable_system, event_code, count]``。``ReportDto`` が保持する
``numerical_stability_report`` のイベント種別ごとの発生回数を書き出す。
集計を持たない、または空のレポートでは何も出力しない。
"""

from __future__ import annotations

import csv

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


class NumericalStabilityCsvExporter(IReportArtifactExporter):
    """1 件分の数値安定化イベントを CSV に書き出す。"""

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
        """数値安定化イベント CSV を保存する。

        集計が無い、または空のレポートでは何もしない。
        """
        ns_report = report.numerical_stability_report
        if ns_report is None or ns_report.is_empty():
            return
        im_key = report.name

        reports_config = self._config.dump_data_config.reports
        filename = format_report_filename(
            reports_config.numerical_stability_pattern,
            timestamp=current_timestamp(self._config),
            im_cable_system_name=safe_system_name(im_key),
        )
        out_path = resolve_report_path(
            self._config,
            sub_dir=reports_config.sub_dir,
            filename=filename,
        )
        with out_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["im_cable_system", "event_code", "count"])
            for event_code, count in ns_report.event_counts:
                writer.writerow([im_key, event_code, str(count)])

        self._logger.info(
            "Report numerical stability CSV saved to %s",
            out_path,
        )
