"""``test_domain`` 共通ヘルパー。

各テストモジュールから ``record_numerical_stability_event`` の発火状況を
照合するためのユーティリティを提供する。
"""

from __future__ import annotations

from im_cable_system.engine.shared.numerical_stability import (
    NumericalStabilityAccumulator,
)

# テスト用の数値ガードしきい値（実装側は既定値を撤廃したため、テストから
# 明示的に注入する）。旧 domain 既定値と同値にして数値挙動を保つ。
TEST_EPS: float = 1e-12
TEST_MAX_MAG: float = 1.0 / TEST_EPS


def assert_event_counts(
    accumulator: NumericalStabilityAccumulator,
    *expected: tuple[str, int],
) -> None:
    """集計器のイベント件数を期待値（タプル列）と照合する。

    Args:
        accumulator: ``numerical_stability_scope`` が yield する集計器。
        *expected: (イベントコード, 回数) の組。順不同で比較する。

    Raises:
        AssertionError: 集計結果が期待値と一致しない場合。
    """
    got = accumulator.to_sorted_items()
    want = tuple(sorted(expected))
    assert got == want, f"expected {want}, got {got}"


def assert_no_events(accumulator: NumericalStabilityAccumulator) -> None:
    """集計器に何も記録されていないことを検証する。

    Args:
        accumulator: ``numerical_stability_scope`` が yield する集計器。

    Raises:
        AssertionError: 何らかのイベントが記録されている場合。
    """
    assert accumulator.is_empty(), (
        f"expected no events, got {accumulator.to_sorted_items()}"
    )
