"""シミュレーション実行スコープ内での数値安定化イベント収集。

contextvars により、深い domain / DTO / algorithm からも
追加情報なしでイベントを記録できる。
スコープ外では :func:`record_numerical_stability_event` は何もしない。

既にアクティブなスコープがある場合、:func:`numerical_stability_scope` は
新しい集計器を作らず既存のものを再利用する（build_model と simulate を
同一スコープで包むため）。
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field


@dataclass
class NumericalStabilityAccumulator:
    """イベントコードごとの発生回数（加算集計）。"""

    _counts: dict[str, int] = field(default_factory=dict)

    def record(self, code: str, count: int = 1) -> None:
        """イベントを記録する。

        Args:
            code: :mod:`event_codes` の定数など、安定したキー文字列。
            count: 加算する回数。0 以下は無視する。
        """
        if count <= 0:
            return
        self._counts[code] = self._counts.get(code, 0) + count

    def to_sorted_items(self) -> tuple[tuple[str, int], ...]:
        """ソート済みの (code, count) タプルを返す。"""
        return tuple(sorted(self._counts.items()))

    def is_empty(self) -> bool:
        """記録が空かどうか。"""
        return not self._counts


_accumulator_var: ContextVar[NumericalStabilityAccumulator | None] = ContextVar(
    "numerical_stability_accumulator", default=None
)


def record_numerical_stability_event(code: str, count: int = 1) -> None:
    """現在のスコープに数値安定化イベントを記録する。

    アクティブな :func:`numerical_stability_scope` がなければ何もしない。

    Args:
        code: イベント種別キー。
        count: 加算回数。
    """
    accumulator = _accumulator_var.get()
    if accumulator is not None:
        accumulator.record(code, count)


@contextmanager
def numerical_stability_scope() -> Iterator[NumericalStabilityAccumulator]:
    """シミュレーション1実行分のイベント収集スコープ。

    外側で既にスコープが開いている場合はその集計器を yield し、
    当該コンテキストの終了時に contextvar を復元しない。

    Yields:
        NumericalStabilityAccumulator: このブロック内で更新される集計器。
    """
    existing = _accumulator_var.get()
    if existing is not None:
        yield existing
        return
    accumulator = NumericalStabilityAccumulator()
    token = _accumulator_var.set(accumulator)
    try:
        yield accumulator
    finally:
        _accumulator_var.reset(token)
