"""supply_grid 図群が共有する単位付き DTO の値取り出しヘルパ。

slip 横軸・出力比横軸の双方のビルダーが使う、単位付き DTO から実数 ndarray を
取り出す純粋関数群を集約する。描画やレイアウトには関与しない。
"""

from __future__ import annotations

from typing import Protocol

import numpy as np


class _UnitValueLike(Protocol):
    """単位付き DTO のうち、本パッケージが使う最小契約。"""

    def get_value(self) -> object:
        """値を返す。"""
        ...

    def get_unit(self) -> str:
        """単位文字列を返す。"""
        ...

    def to_base_unit(self) -> _UnitValueLike:
        """基準単位へ変換した DTO を返す。"""
        ...

    def convert_to_unit(self, target_unit: str) -> _UnitValueLike:
        """指定単位へ変換した DTO を返す。"""
        ...


def _as_real_array(values: object) -> np.ndarray:
    """単位 DTO から実数 ndarray を取り出す。"""
    return np.asarray(np.real(np.asarray(values)), dtype=np.float64)


def _to_base_value_array(dto: _UnitValueLike) -> np.ndarray:
    """DTO を基準単位に変換して ndarray 値を返す。"""
    base_dto = dto.to_base_unit()
    return np.asarray(base_dto.get_value())


def _to_unit_value_array(
    dto: _UnitValueLike,
    *,
    target_unit: str,
) -> np.ndarray:
    """DTO を指定単位に変換して ndarray 値を返す。"""
    converted_dto = dto.convert_to_unit(target_unit)
    return np.asarray(converted_dto.get_value())


def _scalar_base_value(dto: _UnitValueLike) -> float:
    """スカラー DTO を基準単位の float として返す。"""
    value = _to_base_value_array(dto)
    return float(np.real(np.asarray(value).reshape(-1)[0]))


def _ratio_to_base_unit(dto: _UnitValueLike) -> np.ndarray:
    """効率・力率などの無次元系列を ``-`` 基準で返す。"""
    unit = dto.get_unit()
    values = np.asarray(dto.get_value(), dtype=np.float64)
    if unit == "%":
        return values / 100.0
    return values
