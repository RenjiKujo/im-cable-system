"""配列レイアウトから二次電流を解決する。"""

from __future__ import annotations

import numpy as np

from im_cable_system.engine.domain.numerics import (
    create_extended_arrays,
)
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ArrayKey,
    ArrayLayoutDto,
    ImSecondaryCageBranchType,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexCurrentDto,
)


def _array_key_for_secondary_branch(
    secondary_cage_branch_type: ImSecondaryCageBranchType,
) -> ArrayKey:
    """枝種別に対応する ``ArrayLayoutDto.arrays`` のキーを返す。"""
    if secondary_cage_branch_type == ImSecondaryCageBranchType.SINGLE:
        return ArrayKey.SINGLE_CAGE_IM_SECONDARY_CURRENT
    if secondary_cage_branch_type == ImSecondaryCageBranchType.INNER:
        return ArrayKey.DOUBLE_CAGE_IM_SECONDARY_INNER_CURRENT
    if secondary_cage_branch_type == ImSecondaryCageBranchType.OUTER:
        return ArrayKey.DOUBLE_CAGE_IM_SECONDARY_OUTER_CURRENT
    raise ValueError(f"未対応の二次枝です: {secondary_cage_branch_type!s}")


def resolve_secondary_current_for_branch(
    model_array_layout: ArrayLayoutDto,
    secondary_cage_branch_type: ImSecondaryCageBranchType,
) -> ArrayComplexCurrentDto:
    """配列レイアウトから当該枝の二次相電流を取得する（基本単位）。

    キーが無い場合は参照形状のゼロ電流（A 基本単位）を返す。

    Args:
        model_array_layout: 配列レイアウトDTO。
        secondary_cage_branch_type: ``SINGLE`` / ``INNER`` / ``OUTER``。

    Returns:
        ArrayComplexCurrentDto: 二次相電流（基本単位）。

    Raises:
        ValueError: 未対応の枝種別の場合。
    """
    extended_arrays = create_extended_arrays(model_array_layout)
    ref_shape = model_array_layout.get_reference_shape()
    sec_i_key = _array_key_for_secondary_branch(secondary_cage_branch_type)
    if sec_i_key in extended_arrays:
        return ArrayComplexCurrentDto(
            value=extended_arrays[sec_i_key],
            unit=model_array_layout.arrays[sec_i_key].get_unit(),
        ).to_base_unit()
    return ArrayComplexCurrentDto(
        value=np.zeros(ref_shape, dtype=np.complex128),
        unit="A",
    ).to_base_unit()


def resolve_secondary_current_for_layout(
    model_array_layout: ArrayLayoutDto,
) -> ArrayComplexCurrentDto:
    """単一かご: ``single_cage_im_secondary_current`` から二次電流を取得する。

    :func:`resolve_secondary_current_for_branch` に ``SINGLE`` を渡す。

    Args:
        model_array_layout: 配列レイアウトDTO。

    Returns:
        ArrayComplexCurrentDto: 二次相電流（基本単位）。
    """
    return resolve_secondary_current_for_branch(
        model_array_layout,
        ImSecondaryCageBranchType.SINGLE,
    )
