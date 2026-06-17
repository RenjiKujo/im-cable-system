"""input_algorithm テスト共通ヘルパー。"""

from __future__ import annotations

from pathlib import Path

from im_cable_system.engine.shared.job_spec.estimate_params import (
    EstimateParamsJobSpec,
)


def repo_root() -> Path:
    """リポジトリルート（``tests/`` の親）。"""
    return Path(__file__).resolve().parents[3]


def input_files_dir() -> Path:
    """テスト入力ファイル群のルート（``tests/input_files``）。"""
    return repo_root() / "tests" / "input_files"


def catalog_dir() -> Path:
    """テストローカルのカタログ YAML 置き場。"""
    return input_files_dir() / "catalog"


def bounds_and_init_dir() -> Path:
    """テストローカルの境界・初期値 YAML 置き場。"""
    return input_files_dir() / "bounds_and_init"


def test_base_config_path() -> Path:
    """テスト用ベース設定 YAML のパス。"""
    return input_files_dir() / "config" / "test_base_config.yaml"


def make_estimate_params_brief_job_spec() -> EstimateParamsJobSpec:
    """brief 統合 TSV を指す JobSpec。"""
    return EstimateParamsJobSpec(
        input_tsv_path=(
            input_files_dir()
            / "estimate_params"
            / "input_for_estimate_params_brief.tsv"
        ),
    )
