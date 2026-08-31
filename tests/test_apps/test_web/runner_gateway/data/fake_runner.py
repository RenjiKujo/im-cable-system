"""``executor`` のテスト専用フェイク runner。

終了コード・stdout/stderr・待機時間を引数で制御できる。実 runner
（``runner/run_*.py``）と同じく標準ライブラリのみに依存する。
"""

from __future__ import annotations

import argparse
import sys
import time


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exit-code", type=int, default=0)
    parser.add_argument("--sleep-seconds", type=float, default=0.0)
    parser.add_argument("--stdout-message", type=str, default="")
    parser.add_argument("--stderr-message", type=str, default="")
    args = parser.parse_args()

    if args.stdout_message:
        sys.stdout.write(f"{args.stdout_message}\n")
        sys.stdout.flush()
    if args.stderr_message:
        sys.stderr.write(f"{args.stderr_message}\n")
        sys.stderr.flush()
    if args.sleep_seconds > 0:
        time.sleep(args.sleep_seconds)
    return args.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
