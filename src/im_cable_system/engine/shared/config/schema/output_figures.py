"""``calculation.output.figures`` セクションのスキーマと factory。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from im_cable_system.engine.shared.config.schema._parsers import (
    parse_bool,
    parse_dict,
    parse_float,
)

_DEFAULT_SHOW = False
_DEFAULT_SHOW_DURATION_SECONDS = 3.0


@dataclass(frozen=True)
class OutputFiguresConfig:
    """図表示設定。"""

    show: bool
    show_duration_seconds: float


class OutputFiguresConfigFactory:
    """``calculation.output.figures`` を dataclass に変換する。"""

    @staticmethod
    def create(raw: Any) -> OutputFiguresConfig:
        """YAML 由来の dict から :class:`OutputFiguresConfig` を組み立てる。

        Args:
            raw: ``calculation.output.figures`` の生 dict（``None`` 可）。

        Returns:
            OutputFiguresConfig: 補完・検証済みの dataclass。

        Raises:
            ValueError: dict 以外、または各値の制約違反。
        """
        block = parse_dict(
            raw,
            key_path="calculation.output.figures",
        )
        return OutputFiguresConfig(
            show=parse_bool(
                block.get("show"),
                key_path="calculation.output.figures.show",
                default=_DEFAULT_SHOW,
            ),
            show_duration_seconds=parse_float(
                block.get("show_duration_seconds"),
                key_path=("calculation.output.figures.show_duration_seconds"),
                default=_DEFAULT_SHOW_DURATION_SECONDS,
                non_negative=True,
            ),
        )
