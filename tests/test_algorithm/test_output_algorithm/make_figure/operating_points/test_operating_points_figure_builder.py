"""``OperatingPointsFigureBuilder`` の単体テスト。"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, cast

import matplotlib

matplotlib.use("Agg")

from matplotlib.figure import Figure  # noqa: E402

from im_cable_system.engine.algorithm.output_algorithm.make_figure.operating_points.figure_builder import (  # noqa: E402, E501, PLC2701
    OperatingPointsFigureBuilder,
    _output_display_name,
)
from im_cable_system.engine.shared.config import IConfig, ILogger  # noqa: E402
from im_cable_system.engine.shared.dto.output import OutputDto  # noqa: E402


class TestOutputDisplayName:
    """``_output_display_name`` は ``name.get_base()``（候補一意化接尾辞を
    除いた表示専用の基底名）を返す。``supply_grid.plotting_common`` の同名
    private 関数とは別実装（窓口非公開のリーフ同士のため重複は許容）だが、
    挙動は揃える。"""

    def test_returns_base_from_name(self) -> None:
        output_dto = SimpleNamespace(
            name=SimpleNamespace(get_base=lambda: "sys-a")
        )
        assert _output_display_name(cast(Any, output_dto)) == "sys-a"


class TestOperatingPointsFigureBuilder:
    """運転点 index 横軸の Figure を組み立てる。"""

    def _builder(
        self,
        config: IConfig,
        logger: ILogger,
    ) -> OperatingPointsFigureBuilder:
        return cast(
            OperatingPointsFigureBuilder,
            OperatingPointsFigureBuilder.create(
                config=config,
                logger=logger,
            ),
        )

    def test_build_returns_figure_with_expected_axes_and_labels(
        self,
        config: IConfig,
        logger: ILogger,
        operating_points_output_dto: Any,
    ) -> None:
        figure = self._builder(config, logger).build(
            operating_points_output_dto
        )
        assert isinstance(figure, Figure)
        # 左ベース＋右3軸＋左3軸（PF/η, Pout, |I_line|, T, Speed, f, V）。
        assert len(figure.axes) == 7
        handles, labels = (
            figure.legend().legend_handles,
            [text.get_text() for text in figure.legends[0].get_texts()],
        )
        assert "PF [-]" in labels
        assert "Pout [W]" in labels
        assert "V [V]" in labels
        assert len(handles) == 8

    def test_x_axis_is_operating_point(
        self,
        config: IConfig,
        logger: ILogger,
        operating_points_output_dto: Any,
    ) -> None:
        figure = self._builder(config, logger).build(
            operating_points_output_dto
        )
        assert figure.axes[0].get_xlabel() == "Operating point"

    def test_build_skips_missing_supply_axes(
        self,
        config: IConfig,
        logger: ILogger,
        build_operating_points_output_dto: Any,
    ) -> None:
        output_dto = build_operating_points_output_dto(with_supply_axes=False)
        figure = self._builder(config, logger).build(
            cast(OutputDto, output_dto)
        )
        labels = [text.get_text() for text in figure.legend().get_texts()]
        assert "f [Hz]" not in labels
        assert "V [V]" not in labels
        assert "Speed [rpm]" in labels

    def test_build_returns_figure_for_single_point(
        self,
        config: IConfig,
        logger: ILogger,
        build_operating_points_output_dto: Any,
    ) -> None:
        output_dto = build_operating_points_output_dto(point_count=1)
        figure = self._builder(config, logger).build(
            cast(OutputDto, output_dto)
        )
        assert isinstance(figure, Figure)

    def test_build_returns_empty_figure_for_zero_points(
        self,
        config: IConfig,
        logger: ILogger,
    ) -> None:
        # ArrayLayoutDto は参照軸 0 点を許さないため、運転点 0 の早期 return
        # ガードは ``get_reference_total_length`` を 0 とする stub で検証する。
        output_dto = SimpleNamespace(
            array_layout=SimpleNamespace(
                get_reference_total_length=lambda: 0,
            ),
        )
        figure = self._builder(config, logger).build(
            cast(OutputDto, output_dto)
        )
        assert isinstance(figure, Figure)
        assert len(figure.axes) == 0
