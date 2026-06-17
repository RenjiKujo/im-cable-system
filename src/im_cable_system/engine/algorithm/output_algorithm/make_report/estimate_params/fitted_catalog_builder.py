"""推定モデルを catalog 形式に近い入れ子マッピングへ整形する。

``EstimateParamsFitSummaryDto`` の推定パラメータ・モデルラベル・適合指標と
名板値から、``im_series_catalog.yaml`` に類似した構造化マッピングを組み立てる。
YAML 直列化は export_report の責務。数値安定化イベントは本マッピングには含めず、
:class:`NumericalStabilityCsvExporter` が専用 CSV に出力する。
"""

from __future__ import annotations

from typing import Any

from im_cable_system.engine.shared.dto.generic.reporting import (
    EstimateParamsFitSummaryDto,
    FittedParameterReportDto,
)


def _bound_status(param: FittedParameterReportDto) -> str:
    """推定パラメータの境界張り付き状態を文字列で返す。"""
    if param.is_fixed:
        return "fixed"
    if param.is_at_lower_bound:
        return "lower"
    if param.is_at_upper_bound:
        return "upper"
    return "interior"


def _fitted_parameter_entry(
    param: FittedParameterReportDto,
) -> dict[str, Any]:
    """推定パラメータ 1 件を catalog 風のエントリへ整形する。"""
    return {
        "path": param.path,
        "value": param.fitted_value,
        "unit": param.unit,
        "initial_value": param.initial_value,
        "lower_bound": param.lower_bound,
        "upper_bound": param.upper_bound,
        "bound_status": _bound_status(param),
    }


def build_fitted_catalog(
    *,
    name: str,
    summary: EstimateParamsFitSummaryDto,
    nameplate_power_w: float,
    nameplate_current_a: float,
) -> dict[str, Any]:
    """推定モデルを catalog 形式の入れ子マッピングへ整形する。

    Args:
        name: IM ケーブルシステム名。
        summary: 最適化要約・適合指標・推定パラメータ。
        nameplate_power_w: 名板出力 [W]。
        nameplate_current_a: 名板電流 [A]。

    Returns:
        YAML 直列化向けの入れ子マッピング。
    """
    labels = summary.model_labels
    catalog: dict[str, Any] = {
        "version": 1,
        "name": name,
        "nameplate": {
            "power": {"value": nameplate_power_w, "unit": "W"},
            "current": {"value": nameplate_current_a, "unit": "A"},
        },
        "model_labels": {
            "im_primary": labels.im_primary,
            "im_excitation": labels.im_excitation,
            "im_secondary_inner": labels.im_secondary_inner,
            "im_secondary_outer": labels.im_secondary_outer,
            "cable_conductor": labels.cable_conductor,
        },
        "fitted_parameters": [
            _fitted_parameter_entry(param)
            for param in summary.fitted_parameters
        ],
        "fit_metrics": {
            "optimizer_success": summary.optimizer_result.success,
            "least_squares_cost": summary.optimizer_result.cost,
            "overall_rmse_weighted_residual": (
                summary.overall_rmse_weighted_residual
            ),
            "n_residual_elements": summary.n_residual_elements,
            "n_valid_curve_points": summary.n_valid_curve_points,
        },
    }
    return catalog
