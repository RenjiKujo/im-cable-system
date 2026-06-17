"""``calculation.input.validation`` セクションのスキーマと factory。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from im_cable_system.engine.shared.config.schema._parsers import (
    parse_dict,
    parse_int,
)

_DEFAULT_MAX_REFERENCE_AXES_GRID_POINTS = 25_000_000


@dataclass(frozen=True)
class InputValidationConfig:
    """input ステージの入力 DTO 検証設定。"""

    max_reference_axes_grid_points: int


class InputValidationConfigFactory:
    """``calculation.input.validation`` を dataclass に変換する。"""

    @staticmethod
    def create(raw: Any) -> InputValidationConfig:
        """YAML 由来の dict から :class:`InputValidationConfig` を組み立てる。

        Args:
            raw: ``calculation.input.validation`` の生 dict（``None`` 可）。

        Returns:
            InputValidationConfig: 補完・検証済みの dataclass。

        Raises:
            ValueError: dict 以外、または整数値の制約違反。
        """
        block = parse_dict(
            raw,
            key_path="calculation.input.validation",
        )
        return InputValidationConfig(
            max_reference_axes_grid_points=parse_int(
                block.get("max_reference_axes_grid_points"),
                key_path=(
                    "calculation.input.validation."
                    "max_reference_axes_grid_points"
                ),
                default=_DEFAULT_MAX_REFERENCE_AXES_GRID_POINTS,
                positive=True,
            ),
        )
