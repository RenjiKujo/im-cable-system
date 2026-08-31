"""``NumericalStabilityReportDto``（generic 純データ）テスト。

``is_empty`` の挙動を検証する。集計器からの生成は simulate 層のビルダー
（``build_numerical_stability_report``）側でテストする。
"""

from __future__ import annotations

from im_cable_system.engine.shared.dto.generic.reporting import (
    NumericalStabilityReportDto,
)


class TestNumericalStabilityReportDto:
    def test_is_empty_true(self) -> None:
        report = NumericalStabilityReportDto(event_counts=())
        assert report.is_empty()

    def test_is_empty_false(self) -> None:
        report = NumericalStabilityReportDto(
            event_counts=(("event_a", 3),),
        )
        assert not report.is_empty()
