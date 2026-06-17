"""パラメータフィット仕様（bounds + init）の値オブジェクト。

estimate_params の InputStage では、推定の初期値となる R/L とモデル係数を
:class:`ImParameterFitDescriptorBounds` /
:class:`CableParameterFitDescriptorBounds` の bounds と init 設定から決定する。

YAML スキーマ::

    bounds: { lb: <float>, ub: <float> }
    init: { method: "midpoint" }                   # (lb + ub) / 2
    init: { method: "lb" }                         # lb をそのまま採用
    init: { method: "ub" }                         # ub をそのまま採用
    init: { method: "value", value: <float> }      # 明示的な値（[lb, ub] 範囲内）

責務:
    - 1 パラメータ分の bounds と init 仕様を保持する値オブジェクト
    - init 仕様から初期値を解決するメソッド ``resolve_initial`` を提供する
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import cast


class InitMethod(Enum):
    """初期値の決め方。"""

    MIDPOINT = "midpoint"
    LB = "lb"
    UB = "ub"
    VALUE = "value"


@dataclass(frozen=True)
class ParameterFitSpec:
    """1 パラメータ分の探索境界と初期化仕様。

    Attributes:
        lb: 探索下限。
        ub: 探索上限（``lb <= ub`` であること）。
        init_method: 初期値の決め方。
        init_value: ``init_method == VALUE`` のときに採用する値。それ以外の
            method では ``None`` であること。
    """

    lb: float
    ub: float
    init_method: InitMethod
    init_value: float | None = None

    def __post_init__(self) -> None:
        # NOTE: bounds/init は探索境界・初期値として後段で物理量 DTO に
        # 包まれるとは限らないため、ここで NaN / inf を終端拒否する。
        # lb > ub 判定は NaN を取りこぼすので finite チェックを先に置く。
        if not math.isfinite(self.lb) or not math.isfinite(self.ub):
            raise ValueError(
                f"lb/ub must be finite (got lb={self.lb}, ub={self.ub})"
            )
        if self.lb > self.ub:
            raise ValueError(f"lb={self.lb} must not exceed ub={self.ub}")
        if self.init_method == InitMethod.VALUE:
            if self.init_value is None:
                raise ValueError(
                    "init.method='value' requires 'init.value' field"
                )
            if not math.isfinite(self.init_value):
                raise ValueError(
                    f"init.value must be finite (got {self.init_value})"
                )
            if not (self.lb <= self.init_value <= self.ub):
                raise ValueError(
                    f"init.value={self.init_value} is outside bounds "
                    f"[{self.lb}, {self.ub}]"
                )
        elif self.init_value is not None:
            raise ValueError(
                f"init.method='{self.init_method.value}' must not provide "
                f"'init.value' (got {self.init_value})"
            )

    def resolve_initial(self) -> float:
        """init 仕様から初期値を解決する。

        Returns:
            float: ``init_method`` に応じて決まる初期値。
        """
        if self.init_method == InitMethod.MIDPOINT:
            return 0.5 * (self.lb + self.ub)
        if self.init_method == InitMethod.LB:
            return self.lb
        if self.init_method == InitMethod.UB:
            return self.ub
        return cast(float, self.init_value)
