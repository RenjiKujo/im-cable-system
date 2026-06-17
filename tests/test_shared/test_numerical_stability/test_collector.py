"""Tests for numerical stability collector.

スコープ未開始時の no-op、加算集計、ネストスコープでの再利用、
スコープ終了後の contextvar 復元など、横断機構としての契約を担保する。
"""

from __future__ import annotations

from im_cable_system.engine.shared.numerical_stability import (
    NumericalStabilityAccumulator,
    numerical_stability_scope,
    record_numerical_stability_event,
)


class TestNumericalStabilityAccumulator:
    """加算集計の単体契約。"""

    def test_initial_state_is_empty(self) -> None:
        acc = NumericalStabilityAccumulator()
        assert acc.is_empty()
        assert acc.to_sorted_items() == ()

    def test_record_increments_count(self) -> None:
        acc = NumericalStabilityAccumulator()
        acc.record("a")
        acc.record("a", count=2)
        assert acc.to_sorted_items() == (("a", 3),)
        assert not acc.is_empty()

    def test_record_multiple_codes_sorted(self) -> None:
        acc = NumericalStabilityAccumulator()
        acc.record("b")
        acc.record("a", count=4)
        acc.record("c", count=2)
        assert acc.to_sorted_items() == (("a", 4), ("b", 1), ("c", 2))

    def test_record_non_positive_count_is_ignored(self) -> None:
        acc = NumericalStabilityAccumulator()
        acc.record("x", count=0)
        acc.record("x", count=-3)
        assert acc.is_empty()
        assert acc.to_sorted_items() == ()


class TestNumericalStabilityScope:
    """contextvar スコープの契約。"""

    def test_record_outside_scope_is_noop(self) -> None:
        # スコープ外で例外を出さず、副作用も残さない。
        record_numerical_stability_event("anywhere_code", count=10)

    def test_scope_collects_events(self) -> None:
        with numerical_stability_scope() as acc:
            record_numerical_stability_event("c1")
            record_numerical_stability_event("c1", count=2)
            record_numerical_stability_event("c2")
            assert acc.to_sorted_items() == (("c1", 3), ("c2", 1))

    def test_scope_restores_contextvar_on_exit(self) -> None:
        with numerical_stability_scope():
            pass
        # スコープ終了後は再び no-op になる。
        record_numerical_stability_event("after_exit")

    def test_scope_restores_contextvar_on_exception(self) -> None:
        try:
            with numerical_stability_scope():
                record_numerical_stability_event("before_raise")
                raise RuntimeError("boom")
        except RuntimeError:
            pass
        record_numerical_stability_event("after_exception")  # no-op であること

    def test_nested_scope_reuses_outer_accumulator(self) -> None:
        with numerical_stability_scope() as outer:
            record_numerical_stability_event("outer")
            with numerical_stability_scope() as inner:
                assert inner is outer
                record_numerical_stability_event("inner")
            # 内側終了後も外側スコープは継続する。
            record_numerical_stability_event("outer_again")
            assert outer.to_sorted_items() == (
                ("inner", 1),
                ("outer", 1),
                ("outer_again", 1),
            )

    def test_sequential_scopes_are_independent(self) -> None:
        with numerical_stability_scope() as first:
            record_numerical_stability_event("a")
        with numerical_stability_scope() as second:
            record_numerical_stability_event("b")
        assert first is not second
        assert first.to_sorted_items() == (("a", 1),)
        assert second.to_sorted_items() == (("b", 1),)
