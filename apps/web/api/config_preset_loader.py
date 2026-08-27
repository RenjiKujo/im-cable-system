"""``apps/web/presets/config.yaml`` 経由の config プリセット一覧・読み込み。

内部実装（``routes_jobs`` / ``routes_presets`` の両方が使う同一責務ツリー内の
リーフモジュール）のため、パッケージの公開窓口 ``__init__.py`` へは再エクスポートしない。

マニフェストは ``examples/config/`` の既存 YAML への参照だけを持ち、コピーは持たない。
``path`` は ``RunnerGatewaySettings.repo_root`` からの相対パスで、読み込み時に
``repo_root`` 配下であることを検証してから読む。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from apps.web.api.preset_manifest import (
    CONFIG_MANIFEST_PATH,
    load_manifest,
    read_preset_entry,
)


@dataclass(frozen=True)
class ConfigPresetInfo:
    """1 プリセットの名前・説明・YAML 全文。"""

    name: str
    description: str
    yaml_text: str


def list_config_presets(
    mode: str, *, repo_root: Path
) -> list[ConfigPresetInfo]:
    """``mode`` の config プリセットをマニフェスト順で一覧する。

    Raises:
        ValueError: 未知の ``mode`` の場合、またはプリセットの参照先が
            存在しない場合。
    """
    presets = load_manifest(CONFIG_MANIFEST_PATH).get(mode)
    if presets is None:
        raise ValueError(f"未知の mode です: {mode}")
    infos: list[ConfigPresetInfo] = []
    for preset in presets:
        yaml_text = read_preset_entry(
            preset, repo_root=repo_root, kind="config preset"
        )
        infos.append(
            ConfigPresetInfo(
                name=preset["name"],
                description=preset.get("description", ""),
                yaml_text=yaml_text,
            )
        )
    return infos


def read_config_preset(mode: str, name: str, *, repo_root: Path) -> str:
    """1 プリセットの YAML 全文を読む。

    Raises:
        ValueError: 未知の ``mode`` / ``name``、または参照先が存在しない場合。
    """
    for preset in list_config_presets(mode, repo_root=repo_root):
        if preset.name == name:
            return preset.yaml_text
    raise ValueError(f"config preset が見つかりません: mode={mode} name={name}")
