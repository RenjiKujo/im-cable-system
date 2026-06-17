"""二次イミタンス計算前の枝キー検証。"""

from __future__ import annotations

from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ImSecondaryCageBranchType,
    ImSeriesDto,
)


def ensure_secondary_branch_for_immittance(
    src: ImSeriesDto,
    secondary_cage_branch_type: ImSecondaryCageBranchType,
) -> None:
    """二次辞書に指定枝が含まれることを検証する。

    Args:
        src: モーターシリーズDTO。
        secondary_cage_branch_type: 計算対象の二次枝。

    Raises:
        ValueError: ``secondary_models`` / ``secondary_resistances`` /
            ``secondary_inductances`` のいずれかに枝が無い場合。
    """
    branch = secondary_cage_branch_type
    if branch not in src.secondary_models:
        raise ValueError(
            f"secondary_models に指定の二次枝がありません: {branch!s}"
        )
    if branch not in src.secondary_resistances:
        raise ValueError(
            f"secondary_resistances に指定の二次枝がありません: {branch!s}"
        )
    if branch not in src.secondary_inductances:
        raise ValueError(
            f"secondary_inductances に指定の二次枝がありません: {branch!s}"
        )
