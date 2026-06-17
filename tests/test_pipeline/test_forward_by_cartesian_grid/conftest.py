"""forward_by_cartesian_grid pipeline 用 fixture。

Pipeline（Input → Execute → Output）を通す結合テスト向けに、テスト入力資産・
同梱カタログ参照・PNG 出力先をまとめて用意する。検証内容を
``tests/test_processor/test_all_stage/forward_by_cartesian_grid`` と揃えるため、
config 上書き・fixture もそれと同一にする。
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import pytest
import yaml

from im_cable_system.engine.shared.config import (
    Config,
    IConfig,
    ILogger,
    Logger,
    load_config,
)


def _repo_root() -> Path:
    """リポジトリルート（``tests/`` の親）。"""
    return Path(__file__).resolve().parents[3]


def _this_dir() -> Path:
    """この conftest.py が属するテストディレクトリ。

    図・表・レポートは目視確認しやすいよう、本テストパッケージ直下
    （``figures/`` / ``tables/`` / ``reports/``）に出力する。生成物は
    ``.gitignore`` で追跡対象外にしている。
    """
    return Path(__file__).resolve().parent


def _input_files_dir() -> Path:
    """テスト入力ファイル群のルート（``tests/input_files``）。"""
    return _repo_root() / "tests" / "input_files"


def _package_catalog_dir() -> Path:
    """同梱の IM / ケーブルシリーズカタログディレクトリ。"""
    return _repo_root() / "src" / "im_cable_system" / "catalog"


def _test_base_config_path() -> Path:
    """テスト用ベース設定 YAML のパス。"""
    return _input_files_dir() / "config" / "test_base_config.yaml"


def _deep_merge(
    base: dict[str, Any],
    override: dict[str, Any],
) -> dict[str, Any]:
    """override の値を base に再帰的にマージした新たな辞書を返す。"""
    result = copy.deepcopy(base)
    for key, value in override.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def _absolutize_yaml_relative_paths(data: dict[str, Any]) -> None:
    """``test_base_config.yaml`` 内の相対パスを元の場所基準で絶対化する。"""
    base_dir = _test_base_config_path().parent
    for top_key in (
        "series_catalog_for_forward_simulation",
        "bounds_and_init_for_estimation_parameters",
    ):
        sub = data.get(top_key)
        if not isinstance(sub, dict):
            continue
        for path_key in ("im_file_path", "cable_file_path"):
            rel_path = sub.get(path_key)
            if isinstance(rel_path, str) and not Path(rel_path).is_absolute():
                sub[path_key] = str((base_dir / rel_path).resolve())


def _output_dump_override() -> dict[str, Any]:
    """Figure / Table の出力（保存・表示）を制御する config override。

    Figure は保存（``dump.output.figures``）と表示
    （``calculation.output.figures.show``）を個別に指定する。
    Table は表示概念がなく保存のみのため、``dump.output.tables`` で
    保存可否・出力先を指定する。
    """
    return {
        "dump": {
            "output": {
                "figures": {
                    "enabled": False,
                    "sub_dir": "figures",
                    "filename_pattern": "fig_{kind}_{im_cable_system_name}_{timestamp}.png",
                },
                "tables": {
                    "enabled": False,
                    "sub_dir": "tables",
                    "filename_pattern": "tbl_{kind}_{timestamp}.csv",
                },
            },
        },
        "calculation": {
            "output": {
                "figures": {
                    "show": False,
                    "show_duration_seconds": 60,
                },
            },
        },
    }


def _forward_catalog_override() -> dict[str, Any]:
    """forward all stage 用に同梱カタログを見る override。"""
    catalog_dir = _package_catalog_dir()
    return {
        "series_catalog_for_forward_simulation": {
            "im_file_path": str(catalog_dir / "im_series_catalog.yaml"),
            "cable_file_path": str(catalog_dir / "cable_series_catalog.yaml"),
        },
    }


def _numerical_determinism_override() -> dict[str, Any]:
    """ゴールデン値に効く数値設定を固定する config override。

    上位の ``test_base_config.yaml`` が変わってもリグレッションの基準値が
    ずれないよう、計算結果へ直接効くキー（数値ガード eps・電流反復解法）を
    テスト側で明示的にピン留めする。値はゴールデン採取時点の設定と一致させる。
    """
    return {
        "calculation": {
            "execute": {
                "numerical_guard": {"eps": 1.0e-12},
                "current_estimation": {
                    "iteration": {
                        "max_iterations": 20,
                        "convergence_tolerance": 1.0e-6,
                        "convergence_criterion": "line_current",
                    },
                },
            },
        },
    }


def _create_config(
    tmp_path: Path,
    override: dict[str, Any],
) -> IConfig:
    """テスト用上書き YAML を tmp_path に作り Config を返す。"""
    base_data = copy.deepcopy(load_config(_test_base_config_path()))
    _absolutize_yaml_relative_paths(base_data)
    merged = _deep_merge(base_data, override)
    out_path = tmp_path / "config_all_stage.yaml"
    out_path.write_text(
        yaml.dump(merged, allow_unicode=True, default_flow_style=False),
        encoding="utf-8",
    )
    return Config.create(
        config_file_path=out_path,
        dump_base_dir=tmp_path,
    )


@pytest.fixture
def logger() -> ILogger:
    """テスト用 :class:`ILogger`。"""
    return Logger.create(
        Config.create(config_file_path=_test_base_config_path())
    )


@pytest.fixture
def input_files_dir() -> Path:
    """テスト入力ファイル群のルート（``tests/input_files``）。"""
    return _input_files_dir()


@pytest.fixture
def all_stage_cartesian_grid_config(tmp_path: Path) -> IConfig:
    """forward_by_cartesian_grid pipeline 用 :class:`IConfig`。"""
    override = _deep_merge(
        _output_dump_override(),
        _forward_catalog_override(),
    )
    override = _deep_merge(override, _numerical_determinism_override())
    return _create_config(
        tmp_path=tmp_path,
        override=override,
    )
