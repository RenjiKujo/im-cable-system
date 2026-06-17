"""ParallelProcessingStrategy の単体テスト。

THREAD / PROCESS のいずれでも入力順序を保持して結果を返すこと、
ワーカーで発生した例外が呼び出し側へ伝播すること、無効な method で
ValueError を送出することを検証する。process_func はプロセス並列で
pickle 可能である必要があるため、モジュールトップレベルで定義する。
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from im_cable_system.engine.processor.execute_stage.strategy import (
    ParallelProcessingStrategy,
)
from im_cable_system.engine.shared.config import DataProcessingMethod, ILogger


def _plus_ten(value: int) -> int:
    """検証用の単純変換（プロセス並列のため top-level）。"""
    return value + 10


def _raise_value_error(value: int) -> int:
    """ワーカー内で例外を送出する。"""
    raise ValueError(f"boom: {value}")


def _config(method: DataProcessingMethod) -> object:
    """data_processing 設定を持つ fake config を返す。"""
    return SimpleNamespace(
        data_processing=SimpleNamespace(
            method=method,
            max_workers=2,
            timeout_seconds=None,
        ),
    )


@pytest.mark.parametrize(
    "method",
    [DataProcessingMethod.THREAD, DataProcessingMethod.PROCESS],
)
def test_process_preserves_order_for_each_method(
    method: DataProcessingMethod,
    noop_logger: ILogger,
) -> None:
    """並列でも入力順序どおりに結果を返す。"""
    strategy = ParallelProcessingStrategy.create(
        config=_config(method),  # type: ignore[arg-type]
        logger=noop_logger,
        method=method,
    )

    results = strategy.process(
        items=list(range(10)),  # type: ignore[arg-type]
        process_func=_plus_ten,  # type: ignore[arg-type]
    )

    assert results == [value + 10 for value in range(10)]


def test_process_propagates_worker_exception(
    noop_logger: ILogger,
) -> None:
    """ワーカーで発生した例外を呼び出し側へ伝播する。"""
    strategy = ParallelProcessingStrategy.create(
        config=_config(DataProcessingMethod.THREAD),  # type: ignore[arg-type]
        logger=noop_logger,
        method=DataProcessingMethod.THREAD,
    )

    with pytest.raises(ValueError):
        strategy.process(
            items=[1, 2, 3],  # type: ignore[list-item]
            process_func=_raise_value_error,  # type: ignore[arg-type]
        )


def test_create_raises_value_error_for_non_parallel_method(
    noop_logger: ILogger,
) -> None:
    """SEQUENTIAL を渡すと ValueError を送出する。"""
    with pytest.raises(ValueError):
        ParallelProcessingStrategy.create(
            config=_config(DataProcessingMethod.SEQUENTIAL),  # type: ignore[arg-type]
            logger=noop_logger,
            method=DataProcessingMethod.SEQUENTIAL,
        )
