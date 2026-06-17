"""output orchestrator の ``create`` 契約テスト。"""

from __future__ import annotations

from typing import Any

import pytest

from im_cable_system.engine.algorithm.output_algorithm.i_output_orchestrator import (  # noqa: E501
    IOutputOrchestrator,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from tests.test_algorithm.test_output_algorithm.orchestrate._orchestrate_helpers import (
    ALL_ORCHESTRATOR_CLASSES,
)


class TestOrchestratorCreate:
    """具象 orchestrator の ``create`` が I/F を返す。"""

    @pytest.mark.parametrize("orchestrator_cls", ALL_ORCHESTRATOR_CLASSES)
    def test_create_returns_interface(
        self,
        orchestrator_cls: type[Any],
        config: IConfig,
        logger: ILogger,
    ) -> None:
        orchestrator = orchestrator_cls.create(
            config=config,
            logger=logger,
        )
        assert isinstance(orchestrator, IOutputOrchestrator)
