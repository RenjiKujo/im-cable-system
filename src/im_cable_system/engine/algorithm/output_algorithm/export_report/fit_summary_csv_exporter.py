"""1 件分のフィット要約 CSV を保存する。

CSV はモデル候補・適合指標・推定パラメータ・実行条件（最適化／残差設定）・
sim/catalog 比較曲線を 1 ファイルに積み重ねた詳細形式。

NOTE: CSV 行整形ヘルパー（``_model_and_metric_rows`` 等）は、本 CSV 形式に
    固有の直列化ロジックであり、Exporter 本体と同じ責務ツリー（export_report）
    に属する。別ファイルへ分離する余地はあるが、現状の Dir 構成で十分整理
    されているため、あえて分けずに本モジュールへ同居させる。
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
from im_cable_system.engine.shared.dto.generic.reporting import (
    EstimateParamsFitSummaryDto,
)


def _model_and_metric_rows(
    summary: EstimateParamsFitSummaryDto,
    *,
    nameplate_power_w: float,
    nameplate_current_a: float,
) -> list[list[str]]:
    """モデル候補・最適化結果・適合指標・推定パラメータの行を返す。"""
    rmse_i_pct = summary.line_current.rmse / nameplate_current_a * 100.0
    rmse_p_pu = summary.output_power.rmse / nameplate_power_w
    std_i_pct = summary.line_current.std_delta / nameplate_current_a * 100.0
    std_p_pu = summary.output_power.std_delta / nameplate_power_w
    opt = summary.optimizer_result
    rows: list[list[str]] = [
        ["model_candidate_axis", "candidate_selected", "", "", "", "", ""],
        ["im_primary", summary.model_labels.im_primary, "", "", "", "", ""],
        [
            "im_excitation",
            summary.model_labels.im_excitation,
            "",
            "",
            "",
            "",
            "",
        ],
        [
            "im_secondary(inner)",
            summary.model_labels.im_secondary_inner or "",
            "",
            "",
            "",
            "",
            "",
        ],
        [
            "im_secondary(outer)",
            summary.model_labels.im_secondary_outer,
            "",
            "",
            "",
            "",
            "",
        ],
        [
            "cable_conductor_model",
            summary.model_labels.cable_conductor or "",
            "",
            "",
            "",
            "",
            "",
        ],
        ["", "", "", "", "", "", ""],
        ["fit_metric", "value", "unit", "", "", "", ""],
        ["optimizer_success", str(opt.success), "", "", "", "", ""],
        [
            "optimizer_message",
            opt.message.replace("\n", " ").replace("\r", " "),
            "",
            "",
            "",
            "",
            "",
        ],
        ["nfev", str(opt.nfev), "", "", "", "", ""],
        ["least_squares_cost", f"{opt.cost:.12g}", "", "", "", "", ""],
        [
            "overall_rmse_weighted_residual",
            f"{summary.overall_rmse_weighted_residual:.12g}",
            "",
            "",
            "",
            "",
            "",
        ],
        [
            "n_residual_elements",
            str(summary.n_residual_elements),
            "",
            "",
            "",
            "",
            "",
        ],
        [
            "n_valid_curve_points",
            str(summary.n_valid_curve_points),
            "",
            "",
            "",
            "",
            "",
        ],
        ["rmse_line_current", f"{rmse_i_pct:.12g}", "%", "", "", "", ""],
        ["rmse_output_power", f"{rmse_p_pu:.12g}", "[-]", "", "", "", ""],
        [
            "rmse_power_factor",
            f"{summary.power_factor.rmse:.12g}",
            "-",
            "",
            "",
            "",
            "",
        ],
        [
            "rmse_im_efficiency",
            f"{summary.im_efficiency.rmse:.12g}",
            "-",
            "",
            "",
            "",
            "",
        ],
        ["std_delta_line_current", f"{std_i_pct:.12g}", "%", "", "", "", ""],
        ["std_delta_output_power", f"{std_p_pu:.12g}", "[-]", "", "", "", ""],
        [
            "std_delta_power_factor",
            f"{summary.power_factor.std_delta:.12g}",
            "-",
            "",
            "",
            "",
            "",
        ],
        [
            "std_delta_im_efficiency",
            f"{summary.im_efficiency.std_delta:.12g}",
            "-",
            "",
            "",
            "",
            "",
        ],
        ["", "", "", "", "", "", ""],
        ["fitted_param", "path", "value", "unit", "", "", ""],
    ]
    for param in summary.fitted_parameters:
        unit_s = param.unit if param.unit is not None else ""
        rows.append(
            ["", param.path, f"{param.fitted_value:.12g}", unit_s, "", "", ""],
        )
    return rows


def _run_condition_rows(
    summary: EstimateParamsFitSummaryDto,
) -> list[list[str]]:
    """最適化器・残差の実行条件行を返す。"""
    opt = summary.optimizer_settings
    res = summary.residual_objective_settings
    pad = ["", "", "", "", ""]
    return [
        ["", "", "", "", "", "", ""],
        ["run_condition", "value", "", "", "", "", ""],
        ["optimizer_algorithm", opt.algorithm, *pad],
        ["optimizer_max_nfev", str(opt.max_nfev), *pad],
        ["optimizer_ftol", f"{opt.ftol:.12g}", *pad],
        ["optimizer_xtol", f"{opt.xtol:.12g}", *pad],
        ["optimizer_gtol", f"{opt.gtol:.12g}", *pad],
        ["residual_weight_current", f"{res.current_weight:.12g}", *pad],
        ["residual_weight_power", f"{res.power_weight:.12g}", *pad],
        [
            "residual_weight_power_factor",
            f"{res.power_factor_weight:.12g}",
            *pad,
        ],
        ["residual_weight_efficiency", f"{res.efficiency_weight:.12g}", *pad],
        ["residual_normalization_method", res.normalization_method, *pad],
        [
            "residual_normalization_statistic",
            res.normalization_statistic,
            *pad,
        ],
        ["residual_normalization_eps", f"{res.normalization_eps:.12g}", *pad],
        ["normalize_by_point_count", str(res.normalize_by_point_count), *pad],
    ]


def _curve_rows(curve_rows: list[list[float]] | None) -> list[list[str]]:
    """sim/catalog 比較曲線のヘッダ・単位・データ行を返す。"""
    rows: list[list[str]] = [
        ["", "", "", "", "", "", ""],
        [
            "slip",
            "rotational_speed(sim)",
            "power(sim)",
            "power(catalog)",
            "current(sim)",
            "current(catalog)",
            "power_factor(sim)",
            "power_factor(catalog)",
            "efficiency(sim)",
            "efficiency(catalog)",
            "torque(sim)",
            "torque(catalog)",
        ],
        [
            "[-]",
            "[rpm]",
            "[W]",
            "[W]",
            "[A]",
            "[A]",
            "[-]",
            "[-]",
            "[-]",
            "[-]",
            "[N·m]",
            "[N·m]",
        ],
    ]
    if curve_rows is not None:
        for row in curve_rows:
            rows.append([f"{v:.12g}" for v in row])
    return rows


class FitSummaryCsvExporter(IReportArtifactExporter):
    """1 件分のフィット要約を詳細 CSV で保存する。"""

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
        """詳細フィット要約 CSV を保存する。"""
        reports_config = self._config.dump_data_config.reports
        filename = format_report_filename(
            reports_config.fit_summary_pattern,
            timestamp=current_timestamp(self._config),
            im_cable_system_name=safe_system_name(report.name),
        )
        out_path = resolve_report_path(
            self._config,
            sub_dir=reports_config.sub_dir,
            filename=filename,
        )
        rows = _model_and_metric_rows(
            report.fit_summary,
            nameplate_power_w=report.nameplate_power_w,
            nameplate_current_a=report.nameplate_current_a,
        )
        rows.extend(_run_condition_rows(report.fit_summary))
        rows.extend(_curve_rows(report.curve_rows))
        with out_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerows(rows)
        self._logger.info("Report fit summary CSV saved to %s", out_path)
