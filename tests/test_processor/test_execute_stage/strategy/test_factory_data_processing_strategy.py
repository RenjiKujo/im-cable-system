"""DataProcessingStrategyFactory の単体テスト。

config の ``data_processing.method`` に応じて適切な戦略実装を返すこと、
想定外の値で ValueError を送出することを検証する。
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from im_cable_system.engine.processor.execute_stage.strategy import (
    DataProcessingStrategyFactory,
    IDataProcessingStrategy,
    ParallelProcessingStrategy,
    SequentialProcessingStrategy,
)
from im_cable_system.engine.shared.config import DataProcessingMethod, ILogger


def _config_with_method(method: object) -> object:
    """data_processing.method のみ持つ fake config を返す。"""
    return SimpleNamespace(
        data_processing=SimpleNamespace(
            method=method,
            max_workers=2,
            timeout_seconds=None,
        ),
    )


def test_create_returns_sequential_for_sequential_method(
    noop_logger: ILogger,
) -> None:
    """SEQUENTIAL では逐次戦略を返す。"""
    config = _config_with_method(DataProcessingMethod.SEQUENTIAL)
    strategy = DataProcessingStrategyFactory.create(
        config=config,  # type: ignore[arg-type]
        logger=noop_logger,
    )
    assert isinstance(strategy, SequentialProcessingStrategy)
    assert isinstance(strategy, IDataProcessingStrategy)


@pytest.mark.parametrize(
    "method",
    [DataProcessingMethod.THREAD, DataProcessingMethod.PROCESS],
)
def test_create_returns_parallel_for_thread_and_process(
    method: DataProcessingMethod,
    noop_logger: ILogger,
) -> None:
    """THREAD / PROCESS では並列戦略を返す。"""
    config = _config_with_method(method)
    strategy = DataProcessingStrategyFactory.create(
        config=config,  # type: ignore[arg-type]
        logger=noop_logger,
    )
    assert isinstance(strategy, ParallelProcessingStrategy)


def test_create_raises_value_error_for_unknown_method(
    noop_logger: ILogger,
) -> None:
    """想定外の method では ValueError を送出する。"""
    config = _config_with_method(SimpleNamespace(value="bogus"))
    with pytest.raises(ValueError):
        DataProcessingStrategyFactory.create(
            config=config,  # type: ignore[arg-type]
            logger=noop_logger,
        )
