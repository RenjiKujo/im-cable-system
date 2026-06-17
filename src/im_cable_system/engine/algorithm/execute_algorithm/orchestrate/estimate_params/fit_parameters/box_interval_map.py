"""箱制約 [lb, ub] と単位区間 [0, 1] の間のアフィン変換（estimate_params フィット用）。

最適化ルーチンで変数スケールを揃えるため、`physical = lb + z * (ub - lb)` とする
内部座標 z を用いる。各次元は独立。

lb_i == ub_i の次元は**固定次元**とみなす（実質1点に拘束）。そのとき span_i = 0 とし、
`to_physical` は z_i に依存せず lb_i を返す。`to_unit` は内部表現として z_i = 0.5 を用い、
`unit_lower_bounds` / `unit_upper_bounds` がともに 0.5 となり least_squares の
変数固定と整合する。

API は 2 つ用意する:
- `BoxIntervalMap`（メソッド）: `lb/ub` の検証や固定次元判定、`span` の計算を **1回だけ**行い、
  反復評価（例: least_squares の residual 計算）で `to_unit` / `to_physical` を何度も呼ぶ用途。
- `physical_to_unit_interval` / `unit_interval_to_physical`（関数）: 変換を **1回だけ**行いたい用途の
  薄いラッパー（内部で `BoxIntervalMap.create(lb, ub)` を生成して呼ぶ）。
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# 可動次元の (ub - lb) の下限（ゼロ除算・極小幅の検出）。lb == ub の固定次元は対象外。
_MIN_FINITE_SPAN = float(np.finfo(np.float64).resolution) * 8

# 固定次元 (span=0) の内部座標の代表値（[0,1] の中央。bounds を一点にする用途）
_FIXED_INTERNAL_Z = 0.5


@dataclass(frozen=True)
class BoxIntervalMap:
    """検証済みの [lb, ub] 箱と span を保持し、物理座標と単位区間座標を相互変換する。

    Note:
        ``@dataclass`` は不変の状態（lb/ub/span）を明示するための実装都合であり、
        プロジェクトでいう **DTO（層をまたぐ受け渡し用のデータの形）ではない**。
        検証・座標変換などの **振る舞いが本体**のドメイン層の最適化用ユーティリティである。

    Attributes:
        lb: 各次元の下界（float64、1次元）。
        ub: 各次元の上界（float64、1次元）。
        span: ub - lb（float64、1次元）。0 の次元は固定。
    """

    lb: np.ndarray
    ub: np.ndarray
    span: np.ndarray

    @classmethod
    def create(cls, lb: np.ndarray, ub: np.ndarray) -> BoxIntervalMap:
        """lb / ub を検証し、BoxIntervalMap を生成する。

        Args:
            lb: 各次元の下界。
            ub: 各次元の上界。

        Returns:
            BoxIntervalMap: 検証済みの写像。

        Raises:
            ValueError: lb/ub が不正な場合。
        """
        lb_arr, ub_arr = cls._validate_box_vectors(lb, ub)
        span_arr = ub_arr - lb_arr
        return cls(
            lb=lb_arr,
            ub=ub_arr,
            span=span_arr,
        )

    @staticmethod
    def _validate_box_vectors(
        lb: np.ndarray,
        ub: np.ndarray,
        *,
        name_lb: str = "lb",
        name_ub: str = "ub",
    ) -> tuple[np.ndarray, np.ndarray]:
        """lb / ub を検証し、float64 の1次元コピーを返す。

        lb_i == ub_i は許可する（固定次元）。ub_i < lb_i のみ拒否する。

        Args:
            lb: 下界ベクトル。
            ub: 上界ベクトル。
            name_lb: エラーメッセージ用の lb 引数名。
            name_ub: エラーメッセージ用の ub 引数名。

        Returns:
            (lb, ub) の float64 コピー（形状一致）。

        Raises:
            ValueError: 形状不一致、非有限値、ub < lb、
                可動次元で幅が小さすぎる場合。
        """
        lb_arr = np.asarray(lb, dtype=np.float64).reshape(-1)
        ub_arr = np.asarray(ub, dtype=np.float64).reshape(-1)
        if lb_arr.shape != ub_arr.shape:
            raise ValueError(
                f"{name_lb} と {name_ub} の長さが一致しません: "
                f"{lb_arr.shape} vs {ub_arr.shape}"
            )
        if not np.all(np.isfinite(lb_arr)) or not np.all(np.isfinite(ub_arr)):
            raise ValueError(
                f"{name_lb} / {name_ub} には有限値のみ指定してください。"
            )
        span = ub_arr - lb_arr
        if np.any(span < 0.0):
            raise ValueError(
                f"{name_ub} は {name_lb} 以上である必要があります（全次元）。"
            )
        movable = span > 0.0
        if np.any(movable & (span < _MIN_FINITE_SPAN)):
            raise ValueError(
                "可動次元の箱の幅 (ub - lb) が小さすぎます（"
                f"最小 {_MIN_FINITE_SPAN:g} 未満）。"
            )
        return lb_arr, ub_arr

    def unit_lower_bounds(self) -> np.ndarray:
        """least_squares 用の内部変数 z の下界ベクトルを返す。

        可動次元は 0、固定次元 (lb == ub) は `_FIXED_INTERNAL_Z`（一点拘束）。

        Returns:
            z の各次元の下界（lb と同じ長さ）。
        """
        free = self.span > 0.0
        bounds = np.full(self.lb.shape, _FIXED_INTERNAL_Z, dtype=np.float64)
        bounds[free] = 0.0
        return bounds

    def unit_upper_bounds(self) -> np.ndarray:
        """least_squares 用の内部変数 z の上界ベクトルを返す。

        可動次元は 1、固定次元は `_FIXED_INTERNAL_Z`（一点拘束）。

        Returns:
            z の各次元の上界（lb と同じ長さ）。
        """
        free = self.span > 0.0
        bounds = np.full(self.lb.shape, _FIXED_INTERNAL_Z, dtype=np.float64)
        bounds[free] = 1.0
        return bounds

    def to_unit(self, x: np.ndarray) -> np.ndarray:
        """物理座標を単位内部座標へ写す。

        可動次元: z = (x - lb) / span（線形、境界外は外延）。
        固定次元: z = _FIXED_INTERNAL_Z（x は参照せず、最適化では z を動かさない前提）。

        Args:
            x: 物理パラメータベクトル。

        Returns:
            内部座標 z。

        Raises:
            ValueError: 長さ不一致、x に非有限値が含まれる場合。
        """
        x_arr = np.asarray(x, dtype=np.float64).reshape(-1)
        if x_arr.shape != self.lb.shape:
            raise ValueError(
                f"x の長さが lb/ub と一致しません: {x_arr.shape} vs {self.lb.shape}"
            )
        if not np.all(np.isfinite(x_arr)):
            raise ValueError("x には有限値のみ指定してください。")
        free = self.span > 0.0
        z = np.empty_like(x_arr, dtype=np.float64)
        z[free] = (x_arr[free] - self.lb[free]) / self.span[free]
        z[~free] = _FIXED_INTERNAL_Z
        return z

    def to_physical(self, z: np.ndarray) -> np.ndarray:
        """内部座標を物理座標へ写す。

        可動次元: x = lb + z * span。
        固定次元: x = lb（z は無視）。

        Args:
            z: 内部座標ベクトル。

        Returns:
            物理パラメータベクトル。

        Raises:
            ValueError: 長さ不一致、z に非有限値が含まれる場合。
        """
        z_arr = np.asarray(z, dtype=np.float64).reshape(-1)
        if z_arr.shape != self.lb.shape:
            raise ValueError(
                f"z の長さが lb/ub と一致しません: {z_arr.shape} vs {self.lb.shape}"
            )
        if not np.all(np.isfinite(z_arr)):
            raise ValueError("z には有限値のみ指定してください。")
        free = self.span > 0.0
        x_out = np.empty_like(z_arr, dtype=np.float64)
        x_out[free] = self.lb[free] + z_arr[free] * self.span[free]
        x_out[~free] = self.lb[~free]
        return x_out


def physical_to_unit_interval(
    x: np.ndarray,
    lb: np.ndarray,
    ub: np.ndarray,
) -> np.ndarray:
    """物理座標 x を単位内部座標へ写す。

    Args:
        x: 物理パラメータベクトル（lb, ub と同じ長さ）。
        lb: 各次元の下界。
        ub: 各次元の上界。

    Returns:
        内部座標 z。

    Raises:
        ValueError: lb/ub / x が不正な場合。
    """
    return BoxIntervalMap.create(lb, ub).to_unit(x)


def unit_interval_to_physical(
    z: np.ndarray,
    lb: np.ndarray,
    ub: np.ndarray,
) -> np.ndarray:
    """内部座標 z を物理座標へ写す。

    Args:
        z: 内部座標ベクトル（lb, ub と同じ長さ）。
        lb: 各次元の下界。
        ub: 各次元の上界。

    Returns:
        物理パラメータベクトル（float64）。

    Raises:
        ValueError: lb/ub / z が不正な場合。
    """
    return BoxIntervalMap.create(lb, ub).to_physical(z)
