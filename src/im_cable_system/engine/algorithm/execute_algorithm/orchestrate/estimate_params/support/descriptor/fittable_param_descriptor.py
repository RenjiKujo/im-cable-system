"""estimate_params 用フィット記述子（1 スカラパラメータ分）。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FittableParamDescriptor:
    """estimate_params フィット用の 1 スカラパラメータ記述子。

    ExecuteAlgorithm 内の collect → fit → apply → summary パイプラインで
    生成・消費される中間オブジェクト。層をまたぐ DTO ではない。

    ``path`` の解釈例:
        ``("im", "primary_resistance")`` または
        ``("cable", "conductor_resistance_per_length")``。
    ``path[0]`` は対象エンティティ種別を表す。

    Attributes:
        path: パラメータパス（エンティティ種別とフィールド）。
        current_value: 現在値（InputDto 由来の初期値）。
        lb: 探索下限。
        ub: 探索上限。
        unit: 単位文字列。無次元のときは None。
    """

    path: tuple[str, ...]
    current_value: float
    lb: float
    ub: float
    unit: str | None
