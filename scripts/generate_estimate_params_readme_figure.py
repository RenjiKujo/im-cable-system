"""README 図2（推定フィット）を CartesianGrid 軸で再生成する。

EstimateParams の図は教師曲線由来の slip 格子（例: 41 点）で描かれる。
README 図1（Basic03 フォワード）と横軸レンジを揃えるため、正解系列
``SlipAndCurrentDependent03`` を ``axes_cartesian_grid.csv`` で
ForwardByCartesianGrid し、教師 ``performance_curve.csv`` を重ねた
slip 軸・出力比軸図を合成する。

推定 RMSE が十分小さいデモでは、フィット済みモデルとカタログ真値の
フォワード曲線は実質一致する。
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from im_cable_system.engine.shared.config import Config, Logger

_REPO_ROOT = Path(__file__).resolve().parents[1]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate README estimate_params fit figure on cartesian grid axes."
        ),
    )
    parser.add_argument(
        "--series-selection",
        type=Path,
        default=(
            _REPO_ROOT
            / "examples/input/series_cartesian_grid_slipandcurrentdependent03.csv"
        ),
    )
    parser.add_argument(
        "--axes",
        type=Path,
        default=_REPO_ROOT / "examples/input/axes_cartesian_grid.csv",
    )
    parser.add_argument(
        "--performance-curve",
        type=Path,
        default=_REPO_ROOT / "examples/input/performance_curve.csv",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=_REPO_ROOT / "examples/config/forward_by_cartesian_grid.yaml",
    )
    parser.add_argument(
        "--im-catalog",
        type=Path,
        default=_REPO_ROOT
        / "src/im_cable_system/catalog/im_series_catalog.yaml",
    )
    parser.add_argument(
        "--cable-catalog",
        type=Path,
        default=_REPO_ROOT
        / "src/im_cable_system/catalog/cable_series_catalog.yaml",
    )
    parser.add_argument(
        "--figures-dir",
        type=Path,
        default=_REPO_ROOT
        / "examples/outputs/forward_by_cartesian_grid/figures",
    )
    parser.add_argument(
        "--name-contains",
        default="SlipAndCurrentDependent03",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=(
            _REPO_ROOT
            / "docs/assets/estimate_params_slipandcurrentdependent03_fit.png"
        ),
    )
    return parser.parse_args()


def main() -> int:
    """エントリポイント。"""
    args = _parse_args()
    logger = Logger.create(Config.create(config_file_path=None))
    python = _REPO_ROOT / ".venv/bin/python"
    if not python.is_file():
        python = Path(sys.executable)

    forward_cmd = [
        str(python),
        str(_REPO_ROOT / "runner/run_forward_by_cartesian_grid.py"),
        "--series-selection",
        str(args.series_selection),
        "--axes",
        str(args.axes),
        "--performance-curve",
        str(args.performance_curve),
        "--config",
        str(args.config),
        "--im-catalog",
        str(args.im_catalog),
        "--cable-catalog",
        str(args.cable_catalog),
    ]
    combine_cmd = [
        str(python),
        str(_REPO_ROOT / "scripts/combine_axis_figures.py"),
        "--figures-dir",
        str(args.figures_dir),
        "--name-contains",
        args.name_contains,
        "--output",
        str(args.output),
    ]
    env = dict(**__import__("os").environ)
    env.setdefault("MPLBACKEND", "Agg")

    for cmd in (forward_cmd, combine_cmd):
        logger.info("running: %s", " ".join(cmd))
        subprocess.run(cmd, check=True, cwd=_REPO_ROOT, env=env)

    logger.info("README estimate_params fit figure saved: %s", args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
