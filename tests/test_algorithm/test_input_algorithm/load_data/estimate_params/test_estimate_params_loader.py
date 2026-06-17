"""estimate_params ローダの単体テスト。

1 つの統合 TSV から候補軸の直積展開済みの
:class:`EstimateParamsInputLoadedData` タプルが返ることを確認する。
"""

from __future__ import annotations

import numpy as np

from im_cable_system.engine.algorithm.input_algorithm.load_data.estimate_params import (
    EstimateParamsLoader,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from tests.test_algorithm.test_input_algorithm._input_algorithm_helpers import (
    make_estimate_params_brief_job_spec,
)


def test_loader_returns_combo_tuple(
    config: IConfig,
    logger: ILogger,
) -> None:
    """brief TSV から候補直積（1 × 2 × 2 = 4）の LoadedData が返る。"""
    loader = EstimateParamsLoader.create(config=config, logger=logger)
    loaded_tuple = loader.load(make_estimate_params_brief_job_spec())
    assert isinstance(loaded_tuple, tuple)
    assert len(loaded_tuple) == 4
    first = loaded_tuple[0]
    assert first.im is not None
    assert first.cable is None
    assert first.im_performance_curve is not None
    assert first.axes.slip.size > 0
    assert np.all(np.isfinite(first.axes.slip))
    names = {item.im_cable_system_name for item in loaded_tuple}
    assert len(names) == 4
    assert all(name.startswith("CurrentDependent03_") for name in names)
