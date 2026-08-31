"""``apps/web/presets/input.yaml`` 配下の入力ファイルプリセットの一覧・読み込み。

内部実装（``routes_jobs`` / ``routes_presets`` の両方が使う同一責務ツリー内の
リーフモジュール）のため、パッケージの公開窓口 ``__init__.py`` へは再エクスポートしない。

マニフェストはリポジトリ内の既存ファイルへの参照だけを持ち、コピーは持たない。
``path`` は ``RunnerGatewaySettings.repo_root`` からの相対パスで、読み込み時に
``repo_root`` 配下であることを検証してから読む
（``apps/web/runner_gateway/artifacts.py`` の ``resolve_artifact_path`` と同じ姿勢）。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from apps.web.api.preset_manifest import (
    INPUT_MANIFEST_PATH,
    load_manifest,
    read_preset_entry,
    resolve_within_repo_root,
)


@dataclass(frozen=True)
class InputPresetInfo:
    """1 プリセットの名前・説明・ファイル全文。"""

    name: str
    description: str
    text: str


def _load_input_manifest() -> dict[str, Any]:
    return load_manifest(INPUT_MANIFEST_PATH)


def list_input_presets(
    mode: str, *, repo_root: Path
) -> dict[str, list[InputPresetInfo]]:
    """``mode`` の入力ファイルプリセットを field ごとに一覧する。

    Raises:
        ValueError: 未知の ``mode`` の場合、またはプリセットの参照先が
            存在しない場合。
    """
    manifest = _load_input_manifest()
    fields = manifest.get(mode)
    if fields is None:
        raise ValueError(f"未知の mode です: {mode}")
    result: dict[str, list[InputPresetInfo]] = {}
    for field, presets in fields.items():
        infos: list[InputPresetInfo] = []
        for preset in presets:
            text = read_preset_entry(
                preset, repo_root=repo_root, kind="input preset"
            )
            infos.append(
                InputPresetInfo(
                    name=preset["name"],
                    description=preset.get("description", ""),
                    text=text,
                )
            )
        result[field] = infos
    return result


def read_input_preset(
    mode: str, field: str, name: str, *, repo_root: Path
) -> tuple[str, bytes]:
    """1 プリセットのファイル名と中身を読む。

    Returns:
        ``(プリセットのファイル名, 中身)``。

    Raises:
        ValueError: 未知の ``mode`` / ``field`` / ``name``、または参照先が
            存在しない場合。
    """
    manifest = _load_input_manifest()
    fields = manifest.get(mode)
    if fields is None:
        raise ValueError(f"未知の mode です: {mode}")
    presets = fields.get(field)
    if presets is None:
        raise ValueError(f"mode={mode} に未知の field です: {field}")
    for preset in presets:
        if preset["name"] == name:
            path = resolve_within_repo_root(preset["path"], repo_root=repo_root)
            if not path.is_file():
                raise ValueError(
                    f"input preset の参照先が見つかりません: {preset['path']}"
                )
            return path.name, path.read_bytes()
    raise ValueError(
        f"input preset が見つかりません: mode={mode} field={field} name={name}"
    )
