"""``project_info`` セクションのスキーマと factory。

YAML キー: ``project_info``
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from im_cable_system.engine.shared.config.schema._parsers import (
    parse_dict,
    parse_required_str,
)


@dataclass(frozen=True)
class ProjectInfoConfig:
    """プロジェクト基本情報。"""

    project_name: str
    version: str
    default_encoding: str
    timezone: str


class ProjectInfoConfigFactory:
    """``project_info`` ブロックを :class:`ProjectInfoConfig` に変換する。"""

    @staticmethod
    def create(raw: Any) -> ProjectInfoConfig:
        """YAML 由来の dict から :class:`ProjectInfoConfig` を組み立てる。

        Args:
            raw: ``project_info`` セクションの生 dict（``None`` 可）。

        Returns:
            ProjectInfoConfig: 補完・検証済みの dataclass。

        Raises:
            ValueError: dict 以外が来た場合。
        """
        block = parse_dict(raw, key_path="project_info")
        return ProjectInfoConfig(
            project_name=parse_required_str(
                block.get("project_name"),
                key_path="project_info.project_name",
                default="",
            ),
            version=parse_required_str(
                block.get("version"),
                key_path="project_info.version",
                default="",
            ),
            default_encoding=parse_required_str(
                block.get("default_encoding"),
                key_path="project_info.default_encoding",
                default="utf-8",
            ),
            timezone=parse_required_str(
                block.get("timezone"),
                key_path="project_info.timezone",
                default="UTC",
            ),
        )
