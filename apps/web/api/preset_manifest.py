"""``apps/web/presets/`` 配下マニフェストの読み込みとパス解決。

内部実装（``input_preset_loader`` / ``config_preset_loader`` が使う同一責務ツリー内の
リーフモジュール）のため、パッケージの公開窓口 ``__init__.py`` へは再エクスポートしない。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

PRESETS_DIR = Path(__file__).resolve().parents[1] / "presets"
CONFIG_MANIFEST_PATH = PRESETS_DIR / "config.yaml"
INPUT_MANIFEST_PATH = PRESETS_DIR / "input.yaml"


def load_manifest(path: Path) -> dict[str, Any]:
    """マニフェスト YAML を読み、``version`` キーを除いて返す。

    Raises:
        ValueError: トップレベルが辞書でない場合。
    """
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(
            f"preset manifest のトップレベルは辞書である必要があります: {path}"
        )
    return {key: value for key, value in raw.items() if key != "version"}


def resolve_within_repo_root(rel_path: str, *, repo_root: Path) -> Path:
    """``repo_root`` 相対パスを絶対パスへ解決し、配下であることを検証する。

    Raises:
        ValueError: 解決後のパスが ``repo_root`` の配下でない場合。
    """
    resolved_root = repo_root.resolve()
    resolved = (resolved_root / rel_path).resolve()
    if not resolved.is_relative_to(resolved_root):
        raise ValueError(
            f"preset のパスが repo_root の配下ではありません: {rel_path}"
        )
    return resolved


def read_preset_entry(
    entry: dict[str, Any], *, repo_root: Path, kind: str
) -> str:
    """1 プリセットエントリ（``{name, path, description}``）の参照先全文を読む。

    ``list_config_presets`` / ``list_input_presets`` に重複していた
    「``resolve_within_repo_root`` → ``is_file()`` 確認 → 読む」をここへ集約する。
    ``kind`` はエラーメッセージのラベル（例: ``"config preset"``）。

    Raises:
        ValueError: 参照先が存在しない場合。
    """
    path = resolve_within_repo_root(entry["path"], repo_root=repo_root)
    if not path.is_file():
        raise ValueError(f"{kind} の参照先が見つかりません: {entry['path']}")
    return path.read_text(encoding="utf-8")
