"""設定YAML読み込みの共通ユーティリティ。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_config(file_path: Path) -> dict[str, Any]:
    """設定ファイル（YAML）を読み込む。

    Args:
        file_path: 設定ファイルのパス。

    Returns:
        dict[str, Any]: 設定データの辞書。

    Raises:
        FileNotFoundError: 設定ファイルが存在しない場合。
        yaml.YAMLError: YAMLのパースエラー。
    """
    resolved_path = file_path.resolve()

    if not resolved_path.exists():
        raise FileNotFoundError(
            f"設定ファイルが見つかりません: {resolved_path}"
        )

    with resolved_path.open(encoding="utf-8") as file_handle:
        config_data = yaml.safe_load(file_handle)

    if config_data is None:
        config_data = {}

    return config_data


def load_yaml_root_dict(file_path: Path) -> dict[str, Any]:
    """YAML ファイルをルート dict として読み込む。

    Args:
        file_path: YAML ファイルのパス。

    Returns:
        dict[str, Any]: ルートマッピング。

    Raises:
        FileNotFoundError: YAML ファイルが存在しない場合。
        ValueError: YAML ルートがマッピングでない場合。
        yaml.YAMLError: YAML のパースエラー。
    """
    resolved_path = file_path.resolve()
    if not resolved_path.exists():
        raise FileNotFoundError(
            f"YAML ファイルが見つかりません: {resolved_path}"
        )

    with resolved_path.open(encoding="utf-8") as file_handle:
        loaded = yaml.safe_load(file_handle)

    if not isinstance(loaded, dict):
        raise ValueError(
            f"YAML のルートはマッピングである必要があります: {resolved_path}"
        )
    return loaded
