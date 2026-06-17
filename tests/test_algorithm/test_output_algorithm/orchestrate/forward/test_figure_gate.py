"""Forward 系 output orchestrator の Figure ゲートテスト。"""

from __future__ import annotations

from typing import Any

import pytest

from tests.test_algorithm.test_output_algorithm.orchestrate._orchestrate_helpers import (
    FIGURE_SENTINEL,
    FORWARD_ORCHESTRATOR_CLASSES,
    ITM_SENTINEL,
    OUTPUT_SENTINEL,
    build_forward_orchestrator,
    expected_figure_displays,
    expected_figure_exports,
    figure_builder_calls,
)


@pytest.mark.parametrize("orchestrator_cls", FORWARD_ORCHESTRATOR_CLASSES)
class TestForwardFigureGate:
    """``(figures.enabled, figures.show)`` による Figure build / 保存 / 表示。"""

    @pytest.mark.parametrize(
        (
            "figure_enabled",
            "figure_show",
            "expect_build",
            "expect_export",
            "expect_display",
        ),
        [
            (False, False, False, False, False),
            (True, False, True, True, False),
            (False, True, True, False, True),
            (True, True, True, True, True),
        ],
    )
    def test_figure_gate(
        self,
        orchestrator_cls: type[Any],
        figure_enabled: bool,
        figure_show: bool,
        expect_build: bool,
        expect_export: bool,
        expect_display: bool,
    ) -> None:
        """保存 or 表示のどちらかが有効なら build する。"""
        (
            orchestrator,
            converter,
            figure_builders,
            _table_builder,
            figure_exporter,
            figure_displayer,
            _table_exporter,
        ) = build_forward_orchestrator(
            orchestrator_cls,
            figure_enabled=figure_enabled,
            figure_show=figure_show,
            table_enabled=False,
        )

        result = orchestrator.run(itm_dto=ITM_SENTINEL)

        assert result is OUTPUT_SENTINEL
        assert converter.calls == [ITM_SENTINEL]
        assert figure_builder_calls(figure_builders) == (
            [OUTPUT_SENTINEL] * len(figure_builders) if expect_build else []
        )
        assert figure_exporter.exported == (
            expected_figure_exports(orchestrator_cls) if expect_export else []
        )
        assert figure_displayer.shown == (
            expected_figure_displays(orchestrator_cls) if expect_display else []
        )

    def test_same_figure_passed_to_export_and_display(
        self,
        orchestrator_cls: type[Any],
    ) -> None:
        """各 Figure は build 1 回で、同一 Figure を保存・表示に渡す。"""
        (
            orchestrator,
            _converter,
            figure_builders,
            _table_builder,
            figure_exporter,
            figure_displayer,
            _table_exporter,
        ) = build_forward_orchestrator(
            orchestrator_cls,
            figure_enabled=True,
            figure_show=True,
            table_enabled=False,
        )

        orchestrator.run(itm_dto=ITM_SENTINEL)

        assert figure_builder_calls(figure_builders) == [OUTPUT_SENTINEL] * len(
            figure_builders
        )
        assert figure_exporter.exported[0][0] is FIGURE_SENTINEL
        assert figure_displayer.shown[0][0] is FIGURE_SENTINEL
