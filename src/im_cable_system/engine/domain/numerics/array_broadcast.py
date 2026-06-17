"""配列ブロードキャスト計算ロジック（ドメイン層）。

このモジュールは、配列のブロードキャスト（拡張）を提供します。
（1次元配列を多次元配列にブロードキャスト）

特徴:
    - 入力・出力にはDTOを用いる
    - アルゴリズム層から利用される純粋計算ロジックを集約する
"""

from __future__ import annotations

import numpy as np

from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ArrayKey,
    ArrayLayoutDto,
)
from im_cable_system.engine.shared.dto.generic.interfaces import (
    IArrayWithUnitDto,
)


def create_extended_arrays(
    array_layout: ArrayLayoutDto,
) -> dict[ArrayKey, np.ndarray]:
    """ブロードキャストされた拡張配列を作成する。

    各軸の1次元配列を多次元配列にブロードキャストします。
    各軸の配列は、その軸方向にのみ値を持ち、他の軸方向にはブロードキャストされます。

    Args:
        array_layout: 配列レイアウトDTO。

    Returns:
        dict[ArrayKey, np.ndarray]: 軸キーをキーとするブロードキャストされた拡張配列の辞書。
            各配列の形状はarray_layout.shapeと同じになります。

    Raises:
        ValueError: 軸名が存在しない場合、または配列の長さが一致しない場合。

    Note:
        この関数は`extend_array`のラッパー関数であり、`array_layout.arrays`を
        ループして各軸に対して`extend_array`を呼び出すだけの処理を行います。
    """
    return {
        axis_name: extend_array(
            array_layout=array_layout,
            axis_name=axis_name,
            array_dto=dto,
        )
        for axis_name, dto in array_layout.arrays.items()
    }


def extend_array(
    array_layout: ArrayLayoutDto,
    axis_name: ArrayKey,
    array_dto: IArrayWithUnitDto,
) -> np.ndarray:
    """ArrayLayoutDtoの参照軸（reference_axes）に合わせて配列を拡張する。

    参照軸は1次元配列を前提とし、参照軸のshapeにブロードキャストした多次元配列を返す。
    非参照軸（current系など）は、既に参照軸のshapeと同じ多次元配列を
    持っていることを前提とし、そのまま返す。
    （flattenした1次元配列を渡すことは許可しない）

    Args:
        array_layout: 配列レイアウトDTO。reference_axes は必須。
        axis_name: 拡張対象の軸キー。
        array_dto: 拡張する配列DTO。

    Returns:
        np.ndarray: 拡張後の配列。参照軸・非参照軸ともに参照軸のshapeと同じになる。

    Raises:
        ValueError: 軸名が存在しない場合、reference_axes が未指定の場合、
            または配列shape/長さがレイアウトと整合しない場合。
    """
    if axis_name not in array_layout.axes:
        raise ValueError(
            f"軸名 '{axis_name}' が存在しません。"
            f"利用可能な軸名: {list(array_layout.axes)}"
        )

    if not array_layout.reference_axes:
        raise ValueError("reference_axesを指定する必要があります")

    values = array_dto.get_value()
    ref_shape = array_layout.get_reference_shape()
    ref_lengths = list(ref_shape)
    is_reference_axis = axis_name in array_layout.reference_axes

    if is_reference_axis:
        # 参照軸は1次元配列で、対応する参照軸長と一致している必要がある
        if values.ndim != 1:
            raise ValueError(
                "参照軸配列は1次元である必要があります。"
                f"軸 '{axis_name}' の現在の次元数: {values.ndim}"
            )
        ref_axis_index = array_layout.reference_axes.index(axis_name)
        expected_length = ref_lengths[ref_axis_index]
        if len(values) != expected_length:
            raise ValueError(
                f"参照軸 '{axis_name}' の配列の長さが一致しません。"
                f"期待値: {expected_length}, 実際: {len(values)}"
            )

        # 参照軸のshapeに合わせてブロードキャスト
        ndim = len(ref_shape)
        reshape_shape = [1] * ndim
        reshape_shape[ref_axis_index] = -1
        reps = list(ref_shape)
        reps[ref_axis_index] = 1
        reshaped = values.reshape(tuple(reshape_shape))
        return np.tile(reshaped, tuple(reps))

    # 非参照軸は参照軸のshapeと完全一致する多次元配列のみ許容する
    if values.shape != ref_shape:
        raise ValueError(
            "参照軸以外の配列は参照軸のshapeと"
            "完全に一致する多次元配列である必要があります。"
            f"軸 '{axis_name}' のshape: {values.shape}, "
            f"参照軸shape: {ref_shape} "
            f"（参照軸: {array_layout.reference_axes}）"
        )
    return values
