"""図に注記する「選ばれたモデル名一覧」の組み立て。

データ源は ``OutputDto.im`` と ``OutputDto.cable``
（`docs/architecture` が「モデル選択ラベルの原典」と宣言済み）。
fit summary に依存しないため、estimate_params 経路だけでなく forward 経路
でも同じ注記が出せる。
"""

from __future__ import annotations

from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ImCageMultiplicityType,
    ImSecondaryCageBranchType,
)
from im_cable_system.engine.shared.dto.output import OutputDto


def model_label_lines(output_dto: OutputDto) -> list[str]:
    """選ばれたモデル名一覧を、図に注記する行のリストとして返す。

    項目: primary / excitation / secondary（単一かごは 1 行、二重かごは
    inner・outer の 2 行）/ friction_windage / stray_load / cable_conductor。
    ケーブル無し（``output_dto.cable is None``）は ``(none)`` と出す。

    Args:
        output_dto: 変換元の出力 DTO。

    Returns:
        list[str]: 注記行（``"ラベル: モデル名"`` 形式）。
    """
    series = output_dto.im.im_series
    lines: list[str] = [
        f"primary: {series.primary_model.get_name()}",
        f"excitation: {series.excitation_model.get_name()}",
    ]
    if series.cage_multiplicity == ImCageMultiplicityType.SINGLE_CAGE:
        branch = ImSecondaryCageBranchType.SINGLE
        lines.append(f"secondary: {series.secondary_models[branch].get_name()}")
    else:
        inner_model = series.secondary_models[ImSecondaryCageBranchType.INNER]
        outer_model = series.secondary_models[ImSecondaryCageBranchType.OUTER]
        lines.append(f"secondary(inner): {inner_model.get_name()}")
        lines.append(f"secondary(outer): {outer_model.get_name()}")
    lines.append(
        f"friction_windage: {series.friction_windage_model.get_name()}"
    )
    lines.append(f"stray_load: {series.stray_load_model.get_name()}")

    cable = output_dto.cable
    cable_label = (
        cable.conductor_model.get_name() if cable is not None else "(none)"
    )
    lines.append(f"cable_conductor: {cable_label}")
    return lines
