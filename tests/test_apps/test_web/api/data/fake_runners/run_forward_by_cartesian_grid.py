"""API テスト用フェイク ``run_forward_by_cartesian_grid``（実 runner と同じ引数名だけ持つ）。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _fake_runner_common import run  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--series-selection", required=True, type=Path)
    parser.add_argument("--axes", required=True, type=Path)
    parser.add_argument("--performance-curve", type=Path, default=None)
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--im-catalog", type=Path, default=None)
    parser.add_argument("--cable-catalog", type=Path, default=None)
    parser.add_argument("--dump-base-dir", type=Path, default=None)
    return run(parser, "series_selection")


if __name__ == "__main__":
    raise SystemExit(main())
