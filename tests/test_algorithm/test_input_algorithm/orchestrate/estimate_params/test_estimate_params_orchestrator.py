"""estimate_params オーケストレータ結合テスト。

1 ジョブ（統合 TSV 1 つ）から候補直積分の :class:`InputDtos` が
返ることを確認する。
"""

from __future__ import annotations

from im_cable_system.engine.algorithm.input_algorithm.orchestrate.estimate_params import (
    EstimateParamsInputOrchestrator,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.input import InputDtos
from tests.test_algorithm.test_input_algorithm._input_algorithm_helpers import (
    make_estimate_params_brief_job_spec,
)


def test_orchestrator_returns_input_dtos(
    config: IConfig,
    logger: ILogger,
) -> None:
    """1 ジョブから候補直積分の InputDtos が返る。"""
    orch = EstimateParamsInputOrchestrator.create(
        config=config,
        logger=logger,
    )
    result = orch.build_input_dto(make_estimate_params_brief_job_spec())
    assert isinstance(result, InputDtos)
    assert len(result) == 4
    first = result.get_all()[0]
    assert first.name.get_value().startswith("CurrentDependent03_")
    assert first.im is not None
