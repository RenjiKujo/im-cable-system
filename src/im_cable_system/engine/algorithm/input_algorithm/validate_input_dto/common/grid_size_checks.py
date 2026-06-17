"""``reference_axes`` 直積点数の上限チェック（Forward / EstimateParams 共通）。

上限値は呼び出し側が ``max_grid_points`` で明示する。実運用では
``IConfig.input_validation_config.max_reference_axes_grid_points`` を渡す
想定。
"""

from __future__ import annotations

import numpy as np

from im_cable_system.engine.shared.dto.input import (
    InputDto,
)


def check_reference_axes_grid_size(
    input_dto: InputDto,
    max_grid_points: int,
) -> None:
    """``reference_axes`` 軸の直積点数が ``max_grid_points`` 以下か検証する。

    Args:
        input_dto: 検証対象 InputDto。
        max_grid_points: 直積点数の上限（正の整数）。

    Raises:
        ValueError: ``max_grid_points`` が 0 以下、または直積点数が上限を
            超える場合。
    """
    if max_grid_points <= 0:
        raise ValueError(
            "max_grid_points は正の整数で指定してください: "
            f"max_grid_points={max_grid_points}"
        )
    arrays = input_dto.array_layout.arrays
    sizes: list[tuple[str, int]] = [
        (
            axis_key.value,
            int(np.asarray(arrays[axis_key].get_value()).size),
        )
        for axis_key in input_dto.array_layout.reference_axes
    ]
    grid_points = 1
    for _, size in sizes:
        grid_points *= size
    if grid_points > max_grid_points:
        size_repr = ", ".join(f"len({name})={size}" for name, size in sizes)
        raise ValueError(
            "reference_axes 直積グリッド点数が上限を超えています。"
            f" ({size_repr}, grid_points={grid_points} > {max_grid_points})"
        )
