"""数値安定化レポート DTO の生成ファクトリ（simulate 層）。

集計器（:class:`NumericalStabilityAccumulator`）から
:class:`NumericalStabilityReportDto` を構築する。DTO 自体を
``shared.numerical_stability`` から切り離すため、accumulator 結合の
変換ロジックを本モジュールに置く（旧 ``DTO.from_accumulator`` の移設先）。
"""

from __future__ import annotations

from im_cable_system.engine.shared.dto.generic.reporting import (
    NumericalStabilityReportDto,
)
from im_cable_system.engine.shared.numerical_stability import (
    NumericalStabilityAccumulator,
)


def build_numerical_stability_report(
    accumulator: NumericalStabilityAccumulator,
) -> NumericalStabilityReportDto | None:
    """集計器が空でなければレポート DTO を生成する。

    Args:
        accumulator: :func:`numerical_stability_scope` が yield する集計器。

    Returns:
        NumericalStabilityReportDto | None: 空集計のときは None。
    """
    if accumulator.is_empty():
        return None
    return NumericalStabilityReportDto(
        event_counts=accumulator.to_sorted_items(),
    )
