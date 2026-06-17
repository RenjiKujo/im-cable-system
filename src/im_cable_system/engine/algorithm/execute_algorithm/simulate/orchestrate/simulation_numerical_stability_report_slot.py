"""IM ケーブルシステム Simulation オーケストレータの数値安定レポート受け渡し。

:class:`SimulationOrchestrator` は戻り値を
:class:`ItmSimulationDto` のみに保ち、
:func:`publish_simulation_numerical_stability_report` で直近実行のレポートを
contextvar に載せる。呼び出し側は ``calculate`` / ``calculate_voltage_current_only``
の直後に :func:`take_simulation_numerical_stability_report` で取得すること。
"""

from __future__ import annotations

from contextvars import ContextVar
from typing import cast

from im_cable_system.engine.shared.dto.generic.reporting import (
    NumericalStabilityReportDto,
)

_SENTINEL: object = object()

_report_slot: ContextVar[object] = ContextVar(
    "im_cable_system_simulation_numerical_stability_report",
    default=_SENTINEL,
)


def publish_simulation_numerical_stability_report(
    report: NumericalStabilityReportDto | None,
) -> None:
    """直近の simulate 実行に対応するレポートをスロットに書き込む。

    Args:
        report: 集計 DTO。イベントが空なら None。
    """
    _report_slot.set(report)


def take_simulation_numerical_stability_report() -> (
    NumericalStabilityReportDto | None
):
    """スロットからレポートを取り出し、スロットを未設定に戻す。

    Returns:
        公開されたレポート。空集計のときは None。

    Raises:
        RuntimeError: 対応する publish が無い（take の重複など）場合。
    """
    token = _report_slot.get()
    _report_slot.set(_SENTINEL)
    if token is _SENTINEL:
        raise RuntimeError(
            "take_simulation_numerical_stability_report: "
            "公開されたレポートがありません。"
            "SimulationOrchestrator.calculate （または "
            "calculate_voltage_current_only）の直後に 1 回だけ呼んでください。"
        )
    return cast(NumericalStabilityReportDto | None, token)
