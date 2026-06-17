"""validate_job_spec 層で共有するパス検査ヘルパ。

各パイプラインの JobSpecValidator から利用する。ファイル存在・None ガードのみを
担い、中身のスキーマ検証は load_data 層に委ねる。
"""

from __future__ import annotations

from pathlib import Path


def check_path_is_file(path: Path | None, label: str) -> None:
    """パスが指定され、通常ファイルとして存在することを検証する。

    Args:
        path: 検証対象パス。``None`` の場合は未指定として弾く。
        label: エラーメッセージ用の表示名。

    Raises:
        ValueError: 未指定、または通常ファイルとして存在しない場合。
    """
    if path is None:
        raise ValueError(f"{label} が指定されていません。")
    if not path.is_file():
        raise ValueError(f"{label} がファイルとして存在しません: {path}")
