"""``calculation.execute.numerical_guard`` セクションのスキーマと factory。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from im_cable_system.engine.shared.config.schema._parsers import (
    parse_dict,
    parse_float,
)

_DEFAULT_EPS = 1.0e-12


@dataclass(frozen=True)
class NumericalGuardConfig:
    """近接ゼロ判定しきい値などの数値安定化設定。

    Attributes:
        eps: 近接ゼロ判定のしきい値（絶対値）。
    """

    eps: float


class NumericalGuardConfigFactory:
    """``calculation.execute.numerical_guard`` を dataclass に変換する。"""

    @staticmethod
    def create(raw: Any) -> NumericalGuardConfig:
        """YAML 由来の dict から :class:`NumericalGuardConfig` を組み立てる。

        Args:
            raw: ``calculation.execute.numerical_guard`` の生 dict（``None`` 可）。

        Returns:
            NumericalGuardConfig: 補完・検証済みの dataclass。

        Raises:
            ValueError: dict 以外、または eps が正の有限値でない場合。
        """
        block = parse_dict(
            raw,
            key_path="calculation.execute.numerical_guard",
        )
        return NumericalGuardConfig(
            eps=parse_float(
                block.get("eps"),
                key_path="calculation.execute.numerical_guard.eps",
                default=_DEFAULT_EPS,
                positive=True,
            ),
        )
