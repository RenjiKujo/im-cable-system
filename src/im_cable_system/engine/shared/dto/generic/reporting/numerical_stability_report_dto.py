"""数値安定化イベント集計の汎用レポート DTO（generic、Itm 非依存）。

NOTE: イベント種別ごとの発生回数のみを保持する純データ DTO。
    集計器（``NumericalStabilityAccumulator``）からの生成は simulate 層の
    ファクトリ（``build_numerical_stability_report``）が担い、本 DTO は
    ``shared.numerical_stability`` に依存しない。itm / output の双方から
    ``generic.reporting`` 窓口経由で参照する。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NumericalStabilityReportDto:
    """ルーチン・クランプ等のイベント種別ごとの発生回数。

    Attributes:
        event_counts: (イベントコード, 回数) をキー順にソートしたタプル。
    """

    event_counts: tuple[tuple[str, int], ...]

    def is_empty(self) -> bool:
        """集計が空かどうか。"""
        return len(self.event_counts) == 0
