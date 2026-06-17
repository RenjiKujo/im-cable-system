"""estimate_params の構造化レポートビルダー実装。

``OutputDto`` から、フィット要約・名板値・sim/catalog 比較曲線・推定モデルの
catalog 形式マッピング・数値安定化イベント集計を集めて :class:`ReportDto` を
組み立てる。I/O は行わない。
"""

from __future__ import annotations

from im_cable_system.engine.algorithm.output_algorithm.make_report.estimate_params.catalog_vs_sim_curve_rows import (  # noqa: E501
    build_simulated_curve_rows_matching_input_estimate_params_csv,
    nameplate_power_current_w_a_for_estimate_params_table,
)
from im_cable_system.engine.algorithm.output_algorithm.make_report.estimate_params.fitted_catalog_builder import (  # noqa: E501
    build_fitted_catalog,
)
from im_cable_system.engine.algorithm.output_algorithm.make_report.i_report_builder import (  # noqa: E501
    IReportBuilder,
)
from im_cable_system.engine.algorithm.output_algorithm.make_report.report_dto import (  # noqa: E501
    ReportDto,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.output import OutputDto


class EstimateParamsReportBuilder(IReportBuilder):
    """estimate_params 1 件分の構造化レポートを組み立てるビルダー。"""

    def __init__(self, config: IConfig, logger: ILogger) -> None:
        """インスタンスを初期化する。

        Args:
            config: 設定オブジェクト。
            logger: ロガーオブジェクト。
        """
        self._config: IConfig = config
        self._logger: ILogger = logger

    @classmethod
    def create(
        cls,
        config: IConfig,
        logger: ILogger,
    ) -> IReportBuilder:
        """ビルダーのインスタンスを生成する。"""
        return cls(config=config, logger=logger)

    def build(self, output_dto: OutputDto) -> ReportDto | None:
        """OutputDto から :class:`ReportDto` を組み立てる。

        フィット要約を持たない出力（forward 等）は対象外として None を返す。
        """
        summary = output_dto.estimate_params_fit_summary
        if summary is None:
            return None

        p_w, i_a = nameplate_power_current_w_a_for_estimate_params_table(
            output_dto,
        )
        curve = build_simulated_curve_rows_matching_input_estimate_params_csv(
            output_dto,
        )
        curve_rows = curve[0] if curve is not None else None
        name = str(output_dto.name.get_value())
        fitted_catalog = build_fitted_catalog(
            name=name,
            summary=summary,
            nameplate_power_w=p_w,
            nameplate_current_a=i_a,
        )
        return ReportDto(
            name=name,
            fit_summary=summary,
            nameplate_power_w=p_w,
            nameplate_current_a=i_a,
            curve_rows=curve_rows,
            fitted_catalog=fitted_catalog,
            numerical_stability_report=output_dto.numerical_stability_report,
        )
