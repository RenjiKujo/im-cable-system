"""``model_label_annotation.model_label_lines`` の単体テスト。

単一かご／二重かご／ケーブル無しで期待する行が出ることを確認する。
データ源は ``OutputDto.im`` / ``OutputDto.cable`` のみで fit summary に
依存しないため、forward 経路相当の最小 stub で検証できる。
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from im_cable_system.engine.algorithm.output_algorithm.make_figure.supply_grid.model_label_annotation import (  # noqa: E501
    model_label_lines,
)
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ImCageMultiplicityType,
    ImSecondaryCageBranchType,
)


def _named(name: str) -> Any:
    return SimpleNamespace(get_name=lambda: name)


def _output_dto_single_cage(*, with_cable: bool) -> Any:
    im_series = SimpleNamespace(
        primary_model=_named("BASIC"),
        excitation_model=_named("SLIP_DEPENDENT_SATURATION_V1"),
        cage_multiplicity=ImCageMultiplicityType.SINGLE_CAGE,
        secondary_models={
            ImSecondaryCageBranchType.SINGLE: _named(
                "SLIP_DEPENDENT_SKIN_EFFECT_V1"
            ),
        },
        friction_windage_model=_named("CONSTANT_V1"),
        stray_load_model=_named("NONE"),
    )
    cable = (
        SimpleNamespace(conductor_model=_named("BASIC")) if with_cable else None
    )
    return SimpleNamespace(im=SimpleNamespace(im_series=im_series), cable=cable)


def _output_dto_double_cage() -> Any:
    im_series = SimpleNamespace(
        primary_model=_named("BASIC"),
        excitation_model=_named("BASIC"),
        cage_multiplicity=ImCageMultiplicityType.DOUBLE_CAGE,
        secondary_models={
            ImSecondaryCageBranchType.INNER: _named("BASIC"),
            ImSecondaryCageBranchType.OUTER: _named(
                "CURRENT_DEPENDENT_SKIN_EFFECT_V1"
            ),
        },
        friction_windage_model=_named("NONE"),
        stray_load_model=_named("CURRENT_DEPENDENT_QUADRATIC_V1"),
    )
    return SimpleNamespace(im=SimpleNamespace(im_series=im_series), cable=None)


class TestModelLabelLinesSingleCage:
    """単一かご: secondary は 1 行。"""

    def test_lines_with_cable(self) -> None:
        lines = model_label_lines(_output_dto_single_cage(with_cable=True))
        assert lines == [
            "primary: BASIC",
            "excitation: SLIP_DEPENDENT_SATURATION_V1",
            "secondary: SLIP_DEPENDENT_SKIN_EFFECT_V1",
            "friction_windage: CONSTANT_V1",
            "stray_load: NONE",
            "cable_conductor: BASIC",
        ]

    def test_lines_without_cable_show_none(self) -> None:
        lines = model_label_lines(_output_dto_single_cage(with_cable=False))
        assert lines[-1] == "cable_conductor: (none)"


class TestModelLabelLinesDoubleCage:
    """二重かご: secondary は inner/outer の 2 行。"""

    def test_lines_have_inner_and_outer_secondary_rows(self) -> None:
        lines = model_label_lines(_output_dto_double_cage())
        assert "secondary(inner): BASIC" in lines
        assert "secondary(outer): CURRENT_DEPENDENT_SKIN_EFFECT_V1" in lines
        assert "friction_windage: NONE" in lines
        assert "stray_load: CURRENT_DEPENDENT_QUADRATIC_V1" in lines
        assert lines[-1] == "cable_conductor: (none)"
