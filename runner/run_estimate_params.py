"""EstimateParamsPipeline を CLI から実行する runner。"""

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
from im_cable_system.estimate_params import (
    EstimateParamsJobSpec,
    EstimateParamsPipeline,
)

_EXIT_OK = 0
_EXIT_UNEXPECTED_ERROR = 1
_EXIT_VALIDATION_ERROR = 2


def _parse_args(argv: list[str]) -> argparse.Namespace:
    """CLI 引数を解釈する。"""
    parser = argparse.ArgumentParser(
        description="Run EstimateParamsPipeline for a single input table.",
    )
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument(
        "--im-bounds",
        type=Path,
        default=None,
        help=(
            "IM パラメータ境界・初期値 YAML（未指定なら config の参照を使用）。"
        ),
    )
    parser.add_argument(
        "--cable-bounds",
        type=Path,
        default=None,
        help=(
            "ケーブルパラメータ境界・初期値 YAML"
            "（未指定なら config の参照を使用）。"
        ),
    )
    parser.add_argument(
        "--dump-base-dir",
        type=Path,
        default=None,
        help="dump 出力先（絶対パス。未指定なら config の dump.base_dir を使用）。",
    )
    return parser.parse_args(argv)


def _build_runtime(args: argparse.Namespace) -> tuple[IConfig, ILogger]:
    """Config と Logger を生成する。

    ``--im-bounds`` / ``--cable-bounds`` が指定された場合は、config の
    相対参照より優先してそのパスを用いる。``--dump-base-dir`` も同様に
    config の ``dump.base_dir`` より優先する。
    """
    config = Config.create(
        config_file_path=args.config,
        im_bounds_and_init_file_path=args.im_bounds,
        cable_bounds_and_init_file_path=args.cable_bounds,
        dump_base_dir=args.dump_base_dir,
    )
    logger = Logger.create(config)
    return config, logger


def _build_job_spec(args: argparse.Namespace) -> EstimateParamsJobSpec:
    """CLI 引数から EstimateParamsJobSpec を構築する。"""
    return EstimateParamsJobSpec(input_tsv_path=args.input)


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
        job_spec = _build_job_spec(args)
        pipeline = EstimateParamsPipeline.create(
            config=config,
            logger=logger,
        )
        pipeline.run(input=job_spec)
    except ValueError as exc:
        logger.error("validation failed: %s", exc)
        return _EXIT_VALIDATION_ERROR
    except Exception:
        logger.exception(
            "unexpected error while running pipeline (input=%s)",
            args.input,
        )
        return _EXIT_UNEXPECTED_ERROR

    logger.info("pipeline finished successfully (input=%s)", args.input)
    return _EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
