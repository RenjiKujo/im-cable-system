"""EstimateParams output orchestrator の report ゲートテスト。"""

from __future__ import annotations

import pytest

from tests.test_algorithm.test_output_algorithm.orchestrate._orchestrate_helpers import (
    ITM_SENTINEL,
    OUTPUT_SENTINEL,
    REPORT_SENTINEL,
    build_estimate_params_orchestrator,
)


class TestEstimateParamsReportGate:
    """``reports.enabled`` による report build / artifact 保存。"""

    @pytest.mark.parametrize("report_enabled", [True, False])
    def test_report_gate(self, report_enabled: bool) -> None:
        """reports.enabled が ON のときだけ ReportDto を組み立てて保存する。"""
        (
            orchestrator,
            report_builder,
            report_exporters,
        ) = build_estimate_params_orchestrator(
            figure_enabled=False,
            figure_show=False,
            table_enabled=False,
            report_enabled=report_enabled,
        )

        result = orchestrator.run(itm_dto=ITM_SENTINEL)

        assert result is OUTPUT_SENTINEL
        assert report_builder.built == (
            [OUTPUT_SENTINEL] if report_enabled else []
        )
        for report_exporter in report_exporters:
            assert report_exporter.exported == (
                [REPORT_SENTINEL] if report_enabled else []
            )
