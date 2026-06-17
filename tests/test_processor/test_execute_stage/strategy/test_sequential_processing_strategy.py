"""SequentialProcessingStrategy の単体テスト。

逐次処理で process_func を全要素に適用し、入力順序を保つことを検証する。
items / process_func は戦略にとって不透明なため、検証用に int と単純関数を用いる。
"""

from __future__ import annotations

from types import SimpleNamespace

from im_cable_system.engine.processor.execute_stage.strategy import (
    SequentialProcessingStrategy,
)
from im_cable_system.engine.shared.config import ILogger


def _plus_ten(value: int) -> int:
    """検証用の単純変換。"""
    return value + 10


def test_process_applies_func_and_preserves_order(
    noop_logger: ILogger,
) -> None:
    """全要素へ process_func を適用し、順序を保持する。"""
    strategy = SequentialProcessingStrategy.create(
        config=SimpleNamespace(),  # type: ignore[arg-type]
        logger=noop_logger,
    )

    results = strategy.process(
        items=[1, 2, 3],  # type: ignore[list-item]
        process_func=_plus_ten,  # type: ignore[arg-type]
    )

    assert results == [11, 12, 13]


def test_process_returns_empty_for_empty_items(
    noop_logger: ILogger,
) -> None:
    """空入力では空リストを返す。"""
    strategy = SequentialProcessingStrategy.create(
        config=SimpleNamespace(),  # type: ignore[arg-type]
        logger=noop_logger,
    )

    results = strategy.process(
        items=[],
        process_func=_plus_ten,  # type: ignore[arg-type]
    )

    assert results == []
