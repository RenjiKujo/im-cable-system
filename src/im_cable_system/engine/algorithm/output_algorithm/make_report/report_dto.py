"""make_report → export_report の受け渡し契約となるレポート DTO。

estimate_params 1 件分の構造化レポートを、export_report が CSV / YAML へ
直列化できる形で保持する。図 (matplotlib Figure) / 表 (pandas DataFrame) と
同様、本 DTO はオーケストレーター内で build ステップから export ステップへ
渡す中間 artifact であり、戻り値の OutputDto には載せない。

CSV のレイアウト（行整形）は export_report の責務とし、本 DTO は意味の
ある数値・構造データのみを保持する。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from im_cable_system.engine.shared.dto.generic.reporting import (
    EstimateParamsFitSummaryDto,
    NumericalStabilityReportDto,
)


@dataclass(frozen=True)
class ReportDto:
    """estimate_params 1 件分の構造化レポート。

    Attributes:
        name: IM ケーブルシステム名（ファイル名・行ラベル用）。
        fit_summary: 最適化要約・適合指標・推定パラメータ。
        nameplate_power_w: 名板出力 [W]（指標の % / pu 換算に使う）。
        nameplate_current_a: 名板電流 [A]（指標の % 換算に使う）。
        curve_rows: sim/catalog 比較曲線の行列（12 列）。曲線が無い場合は
            None。各行は catalog_vs_sim_curve_rows の列順に従う。
        fitted_catalog: 推定モデルを catalog 形式で表した入れ子マッピング
            （YAML へ直列化する）。
        numerical_stability_report: 数値安定化イベント集計。発火が無い場合や
            集計スコープ外では None。専用 CSV へ直列化し、catalog YAML には
            含めない（重複回避）。
    """

    name: str
    fit_summary: EstimateParamsFitSummaryDto
    nameplate_power_w: float
    nameplate_current_a: float
    curve_rows: list[list[float]] | None
    fitted_catalog: dict[str, Any]
    numerical_stability_report: NumericalStabilityReportDto | None
