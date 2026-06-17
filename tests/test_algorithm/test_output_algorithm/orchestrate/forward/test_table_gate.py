"""Forward 系 output orchestrator の table ゲートテスト。"""

from __future__ import annotations

from typing import Any

import pytest

from tests.test_algorithm.test_output_algorithm.orchestrate._orchestrate_helpers import (
    FORWARD_ORCHESTRATOR_CLASSES,
    ITM_SENTINEL,
    OUTPUT_SENTINEL,
    TABLE_SENTINEL,
    build_forward_orchestrator,
)


@pytest.mark.parametrize("orchestrator_cls", FORWARD_ORCHESTRATOR_CLASSES)
class TestForwardTableGate:
    """``tables.enabled`` による table build / 保存。"""

    @pytest.mark.parametrize("table_enabled", [True, False])
    def test_table_gate(
        self,
        orchestrator_cls: type[Any],
        table_enabled: bool,
    ) -> None:
        """tables.enabled が ON のときだけ build / 保存する。"""
        (
            orchestrator,
            _converter,
            _figure_builders,
            table_builder,
            _figure_exporter,
            _figure_displayer,
            table_exporter,
        ) = build_forward_orchestrator(
            orchestrator_cls,
            figure_enabled=False,
            figure_show=False,
            table_enabled=table_enabled,
        )

        orchestrator.run(itm_dto=ITM_SENTINEL)

        assert table_builder.built == (
            [OUTPUT_SENTINEL] if table_enabled else []
        )
        assert table_exporter.exported == (
            [(TABLE_SENTINEL, OUTPUT_SENTINEL)] if table_enabled else []
        )
