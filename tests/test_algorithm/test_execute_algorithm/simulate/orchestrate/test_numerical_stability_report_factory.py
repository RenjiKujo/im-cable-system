"""``build_numerical_stability_report`` ファクトリのテスト。

集計器が空のときは ``None``、非空のときはソート済みタプルで
``NumericalStabilityReportDto`` を構築することを検証する
（旧 ``NumericalStabilityReportDto.from_accumulator`` の移設先）。
"""

from __future__ import annotations

from im_cable_system.engine.algorithm.execute_algorithm.simulate.orchestrate.numerical_stability_report_factory import (  # noqa: E501
    build_numerical_stability_report,
)
from im_cable_system.engine.shared.numerical_stability import (
    NumericalStabilityAccumulator,
)


class TestBuildNumericalStabilityReport:
    def test_empty_returns_none(self) -> None:
        accumulator = NumericalStabilityAccumulator()
        assert build_numerical_stability_report(accumulator=accumulator) is None

    def test_records_sorted(self) -> None:
        accumulator = NumericalStabilityAccumulator()
        accumulator.record("zeta", 2)
        accumulator.record("alpha", 1)
        accumulator.record("alpha", 1)
        report = build_numerical_stability_report(accumulator=accumulator)
        assert report is not None
        assert report.event_counts == (("alpha", 2), ("zeta", 2))
