"""単カゴ（single cage）教科書値検証の共通ヘルパー。

``orchestrate/forward`` の教科書値モジュールと、``build_model`` の eps 伝播
テストから共有する「代表 InputDto の特定」と「運転点インデックス解決」を提供する。

教科書の問題条件（運転点）:

- すべり ``0.036``
- 周波数 ``50 Hz``
- 線間電圧の大きさ ``200 V``

層外（processor 等）からの import は禁止。``test_execute_algorithm`` 配下の
テストと conftest のみが利用する。
"""

from __future__ import annotations

import numpy as np

from im_cable_system.engine.shared.dto.input import InputDto, InputDtos

# 教科書ケースの代表 InputDto 名（全 BASIC・理想ケーブル・L 型回路）。
TEXTBOOK_SYSTEM_NAME = "broadcast_TEST1_ALL_BASIC_IDEAL"

# ケーブルなし代表 InputDto 名（理想導体クランプ・eps 伝播の検証用）。
TEXTBOOK_NO_CABLE_SYSTEM_NAME = "broadcast_TEST1_no_cable"

# 教科書の問題条件（運転点）。
TEXTBOOK_SLIP = 0.036
TEXTBOOK_FREQUENCY_HZ = 50.0
TEXTBOOK_LINE_VOLTAGE_MAGNITUDE_V = 200.0


def find_input_by_name(input_dtos: InputDtos, name: str) -> InputDto:
    """``name.get_value()`` が ``name`` と一致する InputDto を返す。

    Args:
        input_dtos: 単カゴ fixture 由来の InputDtos。
        name: 探索対象のシステム名。

    Returns:
        InputDto: 一致した 1 件。

    Raises:
        AssertionError: 該当 InputDto が無い場合。
    """
    for dto in input_dtos.get_all():
        if dto.name.get_value() == name:
            return dto
    msg = f"InputDto not found: {name!r}"
    raise AssertionError(msg)


def find_textbook_input(input_dtos: InputDtos) -> InputDto:
    """教科書ケースの代表 InputDto（全 BASIC・理想ケーブル）を返す。"""
    return find_input_by_name(input_dtos, TEXTBOOK_SYSTEM_NAME)


def find_textbook_no_cable_input(input_dtos: InputDtos) -> InputDto:
    """ケーブルなし代表 InputDto（理想導体クランプ検証用）を返す。"""
    return find_input_by_name(input_dtos, TEXTBOOK_NO_CABLE_SYSTEM_NAME)


def resolve_operating_point_index(
    array_layout: object,
    *,
    slip: float = TEXTBOOK_SLIP,
    frequency_hz: float = TEXTBOOK_FREQUENCY_HZ,
    line_voltage_magnitude_v: float = TEXTBOOK_LINE_VOLTAGE_MAGNITUDE_V,
) -> tuple[int, ...]:
    """教科書の運転点に対応する多次元インデックスを ``reference_axes`` 順で返す。

    Args:
        array_layout: ``ItmModelDto.array_layout`` 相当（``arrays`` /
            ``reference_axes`` を持つ）。
        slip: すべり。
        frequency_hz: 周波数 [Hz]。
        line_voltage_magnitude_v: 線間電圧の大きさ [V]。

    Returns:
        tuple[int, ...]: ``reference_axes`` の並びに対応するインデックス。

    Raises:
        AssertionError: 指定運転点が配列に存在しない場合。
    """
    arrays = array_layout.arrays  # type: ignore[attr-defined]
    reference_axes = array_layout.reference_axes  # type: ignore[attr-defined]

    slip_idx = _find_close_index(arrays["slip"].get_value(), slip, "slip")
    freq_idx = _find_close_index(
        arrays["frequency"].get_value(), frequency_hz, "frequency"
    )
    voltage_idx = _find_close_index(
        np.abs(arrays["input_line_voltage"].get_value()),
        line_voltage_magnitude_v,
        "input_line_voltage",
    )

    axis_to_index = {
        "slip": slip_idx,
        "frequency": freq_idx,
        "input_line_voltage": voltage_idx,
    }
    return tuple(axis_to_index.get(axis, 0) for axis in reference_axes)


def _find_close_index(array: np.ndarray, target: float, axis_name: str) -> int:
    """1 次元配列から ``target`` に最も近い要素のインデックスを返す。"""
    matches = np.where(np.isclose(array, target))[0]
    if len(matches) == 0:
        msg = f"運転点 {axis_name}={target} が配列に見つかりません。"
        raise AssertionError(msg)
    return int(matches[0])
