"""CSV/TSV 読み込みの共通ユーティリティ（load_data 横断）。

YAML 以外のテキスト表形式ファイル（シリーズ選択 TSV、参照軸 CSV、
統合 estimate_params 入力など）の **区切り文字判定と素読み** のみを担う。
パイプライン固有のスキーマ検証は各 parser に委ねる。
"""

from __future__ import annotations

import csv
from pathlib import Path


def csv_delimiter_for_path(path: Path) -> str:
    """拡張子に応じた区切り文字（TSV はタブ、それ以外はカンマ）。"""
    if path.suffix.lower() == ".tsv":
        return "\t"
    return ","


def read_csv_rows(path: Path) -> list[list[str]]:
    """ファイルを読み込み、行リストを返す。"""
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.reader(handle, delimiter=csv_delimiter_for_path(path)))


def normalize_unit_cell(raw: str) -> str:
    """単位行のセルを正規化する（例: ``[Hz]`` → ``Hz``）。"""
    stripped = raw.strip()
    if len(stripped) >= 2 and stripped[0] == "[" and stripped[-1] == "]":
        return stripped[1:-1].strip()
    return stripped
