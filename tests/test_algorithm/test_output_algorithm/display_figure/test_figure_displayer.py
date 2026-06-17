"""FigureDisplayer の表示後 close 契約テスト。"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, cast

import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from im_cable_system.engine.algorithm.output_algorithm.display_figure.figure_displayer import (  # noqa: E501
    FigureDisplayer,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.output import OutputDto


class TestFigureDisplayer:
    """FigureDisplayer.show の契約テスト。"""

    def test_show_closes_figure_after_display(
        self,
        logger: ILogger,
        monkeypatch: Any,
    ) -> None:
        """表示後に Figure を close する。"""
        config = SimpleNamespace(
            output_figures_config=SimpleNamespace(show_duration_seconds=0.0),
        )
        displayer = FigureDisplayer.create(
            config=cast(IConfig, config),
            logger=logger,
        )
        figure = plt.figure()
        closed: list[object] = []

        def _show(*, block: bool) -> None:
            assert block is False

        def _pause(duration: float) -> None:
            assert duration >= 0.01

        def _close(fig: object) -> None:
            closed.append(fig)

        monkeypatch.setattr(plt, "show", _show)
        monkeypatch.setattr(plt, "pause", _pause)
        monkeypatch.setattr(plt, "close", _close)

        displayer.show(figure=figure, output_dto=cast(OutputDto, object()))

        assert closed == [figure]

    def test_show_accepts_unmanaged_empty_figure(
        self,
        logger: ILogger,
        monkeypatch: Any,
    ) -> None:
        """pyplot 管理外の空 Figure でも表示・close できる。"""
        config = SimpleNamespace(
            output_figures_config=SimpleNamespace(show_duration_seconds=0.0),
        )
        displayer = FigureDisplayer.create(
            config=cast(IConfig, config),
            logger=logger,
        )
        figure = Figure()
        closed: list[object] = []

        def _figure(_number: int) -> None:
            raise AssertionError("unmanaged Figure should not be activated")

        def _show(*, block: bool) -> None:
            assert block is False

        def _pause(duration: float) -> None:
            assert duration >= 0.01

        def _close(fig: object) -> None:
            closed.append(fig)

        monkeypatch.setattr(plt, "figure", _figure)
        monkeypatch.setattr(plt, "show", _show)
        monkeypatch.setattr(plt, "pause", _pause)
        monkeypatch.setattr(plt, "close", _close)

        displayer.show(figure=figure, output_dto=cast(OutputDto, object()))

        assert closed == [figure]
