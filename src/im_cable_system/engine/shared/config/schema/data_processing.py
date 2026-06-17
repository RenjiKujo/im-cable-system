"""``calculation.execute.data_processing`` セクションのスキーマと factory。

並列／逐次の実行戦略を保持する。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from im_cable_system.engine.shared.config.schema._parsers import (
    parse_dict,
    parse_enum,
    parse_float,
    parse_int,
)


class DataProcessingMethod(str, Enum):
    """データ処理方式。"""

    SEQUENTIAL = "sequential"
    THREAD = "thread"
    PROCESS = "process"


@dataclass(frozen=True)
class DataProcessingConfig:
    """ExecuteStage のデータ処理戦略設定。"""

    method: DataProcessingMethod
    max_workers: int | None
    timeout_seconds: float | None


class DataProcessingConfigFactory:
    """``calculation.execute.data_processing`` を dataclass に変換する。"""

    @staticmethod
    def create(raw: Any) -> DataProcessingConfig:
        """YAML 由来の dict から :class:`DataProcessingConfig` を組み立てる。

        Args:
            raw: ``calculation.execute.data_processing`` の生 dict（``None`` 可）。

        Returns:
            DataProcessingConfig: 補完・検証済みの dataclass。

        Raises:
            ValueError: dict 以外、または各値の制約違反。
        """
        block = parse_dict(
            raw,
            key_path="calculation.execute.data_processing",
        )
        return DataProcessingConfig(
            method=parse_enum(
                block.get("method"),
                DataProcessingMethod,
                key_path="calculation.execute.data_processing.method",
                default=DataProcessingMethod.SEQUENTIAL,
            ),
            max_workers=parse_int(
                block.get("max_workers"),
                key_path="calculation.execute.data_processing.max_workers",
                positive=True,
                allow_none=True,
            ),
            timeout_seconds=parse_float(
                block.get("timeout_seconds"),
                key_path=(
                    "calculation.execute.data_processing.timeout_seconds"
                ),
                positive=True,
                allow_none=True,
            ),
        )
