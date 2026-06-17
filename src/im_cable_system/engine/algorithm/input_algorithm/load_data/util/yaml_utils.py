"""YAML テキスト読込の共通ユーティリティ（load_data 横断）。

責務は YAML ファイルを ``yaml.safe_load`` で読み、ルートが
マッピング（dict）であることを保証することに限定する。スキーマ解釈
（必須キーの取り出し、``{value, unit}`` の解釈、``model: {name, params}``
の解釈など）は各 parser 配下の個別ヘルパに委ねる。

``forward`` 系の :mod:`yaml_utils` がスキーマ解釈ヘルパ群を抱えて
いるが、本モジュールにはそれらを引き上げない（YAGNI: 現状
``estimate_params`` 側の境界 YAML は ``from_estimation_document`` 経由で
独自スキーマを解釈するため、共通化メリットが薄い）。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_yaml_root_map(path: Path) -> dict[str, Any]:
    """YAML ファイルのルートマッピングを ``dict`` として読み込む。

    Args:
        path: YAML ファイルパス。

    Returns:
        ルート dict。

    Raises:
        ValueError: ルートがマッピングでない場合。
    """
    with path.open(encoding="utf-8") as handle:
        root = yaml.safe_load(handle)
    if not isinstance(root, dict):
        raise ValueError(
            f"YAML のルートはマッピングである必要があります: {path}"
        )
    return root
