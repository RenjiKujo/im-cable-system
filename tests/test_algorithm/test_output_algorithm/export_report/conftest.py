"""export_report テスト用フィクスチャ。"""

from __future__ import annotations

import pytest

from im_cable_system.engine.algorithm.output_algorithm.make_report import (
    ReportDto,
)
from tests.test_algorithm.test_output_algorithm.make_report.estimate_params._estimate_params_report_helpers import (  # noqa: E501
    minimal_fit_summary,
)


@pytest.fixture
def sample_report_dto() -> ReportDto:
    """最小の :class:`ReportDto`。"""
    return ReportDto(
        name="SYS01",
        fit_summary=minimal_fit_summary(),
        nameplate_power_w=1000.0,
        nameplate_current_a=10.0,
        curve_rows=[
            [
                0.1,
                1800.0,
                100.0,
                99.0,
                10.0,
                9.5,
                0.8,
                0.79,
                0.9,
                0.89,
                5.0,
                4.9,
            ]
        ],
        fitted_catalog={"name": "SYS01", "version": 1},
        numerical_stability_report=None,
    )
