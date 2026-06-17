"""EstimateParamsReportBuilder の単体テスト。"""

from __future__ import annotations

from collections.abc import Callable

from im_cable_system.engine.algorithm.output_algorithm.make_report.estimate_params.report_builder import (  # noqa: E501
    EstimateParamsReportBuilder,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.output import OutputDto


class TestEstimateParamsReportBuilder:
    """``OutputDto`` から ``ReportDto`` を組み立てる契約。"""

    def test_returns_none_without_fit_summary(
        self,
        config: IConfig,
        logger: ILogger,
        build_estimate_params_output_dto: Callable[..., OutputDto],
    ) -> None:
        builder = EstimateParamsReportBuilder.create(
            config=config,
            logger=logger,
        )
        output_dto = build_estimate_params_output_dto(with_summary=False)
        assert builder.build(output_dto) is None

    def test_returns_report_dto_with_summary(
        self,
        config: IConfig,
        logger: ILogger,
        build_estimate_params_output_dto: Callable[..., OutputDto],
    ) -> None:
        builder = EstimateParamsReportBuilder.create(
            config=config,
            logger=logger,
        )
        output_dto = build_estimate_params_output_dto(with_summary=True)
        report = builder.build(output_dto)
        assert report is not None
        assert report.name == "SYS01"
        assert report.nameplate_power_w == 1000.0
        assert report.nameplate_current_a == 10.0
        assert report.fitted_catalog["name"] == "SYS01"
