"""API テスト専用フェイク runner の共通処理。

主入力ファイルの中身に埋め込まれたマーカー文字列で、終了コードと待機時間を
制御する（``TRIGGER_EXIT_1`` / ``TRIGGER_EXIT_2`` / ``TRIGGER_SLEEP_<秒数>``）。
どのマーカーも無ければ正常終了し、``--dump-base-dir`` 配下にダミーの
figure ファイルを 1 つ書き出す。
"""

from __future__ import annotations

import argparse
import re
import time
from pathlib import Path

_SLEEP_PATTERN = re.compile(r"TRIGGER_SLEEP_(\d+(?:\.\d+)?)")


def run(parser: argparse.ArgumentParser, primary_input_arg: str) -> int:
    """共通の実行ロジック。呼び出し側 argparse に ``--dump-base-dir`` が必須。"""
    args = parser.parse_args()
    primary_path = Path(getattr(args, primary_input_arg))
    content = (
        primary_path.read_text(encoding="utf-8")
        if primary_path.is_file()
        else ""
    )

    sleep_match = _SLEEP_PATTERN.search(content)
    if sleep_match:
        time.sleep(float(sleep_match.group(1)))

    if "TRIGGER_EXIT_2" in content:
        return 2
    if "TRIGGER_EXIT_1" in content:
        return 1

    dump_base_dir = args.dump_base_dir
    if dump_base_dir is not None:
        figures_dir = Path(dump_base_dir) / "figures"
        figures_dir.mkdir(parents=True, exist_ok=True)
        (figures_dir / "fig_fake.png").write_bytes(b"fake-png-bytes")
    return 0
