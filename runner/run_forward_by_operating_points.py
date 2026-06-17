"""ForwardByOperatingPointsPipeline を CLI から実行する runner。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from im_cable_system.engine.shared.config import (
    Config,
    IConfig,
    ILogger,
    Logger,
)
from im_cable_system.forward_by_operating_points import (
    ForwardByOperatingPointsPipeline,
    ForwardJobSpec,
    ForwardJobSpecs,
)

_EXIT_OK = 0
_EXIT_UNEXPECTED_ERROR = 1
_EXIT_VALIDATION_ERROR = 2


def _parse_args(argv: list[str]) -> argparse.Namespace:
    """CLI 引数を解釈する。"""
    parser = argparse.ArgumentParser(
        description="Run ForwardByOperatingPointsPipeline for a single job.",
    )
    parser.add_argument("--series-selection", required=True, type=Path)
    parser.add_argument("--axes", required=True, type=Path)
    parser.add_argument("--performance-curve", type=Path, default=None)
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument(
        "--im-catalog",
        type=Path,
        default=None,
        help="IM シリーズカタログ YAML（未指定なら config の参照を使用）。",
    )
    parser.add_argument(
        "--cable-catalog",
        type=Path,
        default=None,
        help="ケーブルシリーズカタログ YAML（未指定なら config の参照を使用）。",
    )
    return parser.parse_args(argv)


def _build_runtime(args: argparse.Namespace) -> tuple[IConfig, ILogger]:
    """Config と Logger を生成する。

    ``--im-catalog`` / ``--cable-catalog`` が指定された場合は、config の
    相対参照より優先してそのパスを用いる。
    """
    config = Config.create(
        config_file_path=args.config,
        im_series_catalog_file_path=args.im_catalog,
        cable_series_catalog_file_path=args.cable_catalog,
    )
    logger = Logger.create(config)
    return config, logger


def _build_job_specs(args: argparse.Namespace) -> ForwardJobSpecs:
    """CLI 引数から 1 ジョブ分の ForwardJobSpecs を構築する。"""
    spec = ForwardJobSpec(
        series_selection_path=args.series_selection,
        axes_path=args.axes,
        performance_curve_path=args.performance_curve,
    )
    return ForwardJobSpecs(specs=(spec,))


def main(argv: list[str] | None = None) -> int:
    """エントリポイント。終了コードを返す。"""
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    try:
        config, logger = _build_runtime(args)
    except ValueError as exc:
        sys.stderr.write(f"[CONFIG ERROR] {exc}\n")
        return _EXIT_VALIDATION_ERROR
    except Exception as exc:
        sys.stderr.write(
            f"[UNEXPECTED ERROR] failed to build runtime: {exc}\n",
        )
        return _EXIT_UNEXPECTED_ERROR

    try:
        job_specs = _build_job_specs(args)
        pipeline = ForwardByOperatingPointsPipeline.create(
            config=config,
            logger=logger,
        )
        pipeline.run(input=job_specs)
    except ValueError as exc:
        logger.error("validation failed: %s", exc)
        return _EXIT_VALIDATION_ERROR
    except Exception:
        logger.exception(
            "unexpected error while running pipeline (series=%s)",
            args.series_selection,
        )
        return _EXIT_UNEXPECTED_ERROR

    logger.info(
        "pipeline finished successfully (series=%s)",
        args.series_selection,
    )
    return _EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
