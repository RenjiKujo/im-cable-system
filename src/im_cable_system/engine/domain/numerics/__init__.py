"""数値計算ユーティリティ（公開窓口）。

このパッケージは、物理ドメイン知識を持たない数値計算ユーティリティを提供する。
``physics`` が物理量計算を扱うのに対し、``numerics`` は配列ブロードキャストなどの
汎用的な数値手法を扱う。

含まれるモジュール:
    - ``array_broadcast``: ``ArrayLayoutDto`` に基づく配列ブロードキャスト。

層外からの import:
    >>> from im_cable_system.engine.domain.numerics import (
    ...     create_extended_arrays,
    ... )
"""

from im_cable_system.engine.domain.numerics.array_broadcast import (
    create_extended_arrays,
    extend_array,
)

__all__ = [
    "create_extended_arrays",
    "extend_array",
]
