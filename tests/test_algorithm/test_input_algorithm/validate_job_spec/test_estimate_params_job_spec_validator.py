"""estimate_params ジョブ spec バリデータの単体テスト。

4 段フロー 1 段目 ``_validate_job_spec`` の契約を確認する。
JobSpec が ``input_tsv_path`` のみに削減されているため、本テストでは
ファイル存在のみを検証する。
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from im_cable_system.engine.algorithm.input_algorithm.validate_job_spec import (
    EstimateParamsJobSpecValidator,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.job_spec.estimate_params import (
    EstimateParamsJobSpec,
)
from tests.test_algorithm.test_input_algorithm._input_algorithm_helpers import (
    make_estimate_params_brief_job_spec,
)


def _make_spec() -> EstimateParamsJobSpec:
    return make_estimate_params_brief_job_spec()


def _make_validator(
    config: IConfig,
    logger: ILogger,
) -> EstimateParamsJobSpecValidator:
    return EstimateParamsJobSpecValidator.create(
        config=config,
        logger=logger,
    )


def test_validator_accepts_valid_spec(
    config: IConfig,
    logger: ILogger,
) -> None:
    """統合 TSV が存在すれば通る。"""
    _make_validator(config, logger).validate(_make_spec())


def test_rejects_missing_input_tsv_path(
    config: IConfig,
    logger: ILogger,
    tmp_path: Path,
) -> None:
    """input_tsv_path が不在なら ValueError。"""
    spec = replace(_make_spec(), input_tsv_path=tmp_path / "no_such_input.tsv")
    with pytest.raises(
        ValueError,
        match="統合入力 TSV がファイルとして存在しません",
    ):
        _make_validator(config, logger).validate(spec)


def test_rejects_none_input_tsv_path(
    config: IConfig,
    logger: ILogger,
) -> None:
    """input_tsv_path が未指定なら ValueError。"""
    spec = replace(_make_spec(), input_tsv_path=None)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="統合入力 TSV が指定されていません"):
        _make_validator(config, logger).validate(spec)
