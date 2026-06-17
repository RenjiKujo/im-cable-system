"""estimate_params pipeline 用 fixture。

Pipeline（Input → Execute → Output）を通す結合テスト向けに、テスト入力資産・
最適化設定・出力先をまとめて用意する。検証内容を
``tests/test_processor/test_all_stage/estimate_params`` と揃えるため、config
上書き・fixture もそれと同一にする。
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

ESTIMATE_PARAMS_MAX_NFEV = 120

ESTIMATE_PARAMS_RESIDUAL_WEIGHT_KEYS: tuple[str, ...] = (
    "current",
    "power",
    "power_factor",
    "efficiency",
)
DEFAULT_ESTIMATE_PARAMS_RESIDUAL_WEIGHTS: dict[str, float] = {
    "current": 1.0,
    "power": 1.0,
    "power_factor": 1.0,
    "efficiency": 1.0,
}


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


def _figure_dump_override() -> dict[str, Any]:
    """Figure / Table 保存・表示とレポートデータ出力を設定する override。

    figures（保存・表示）・tables（保存）・reports（CSV / YAML 等）の各出力を、
    対応ブロック（``enabled`` / ``sub_dir`` / pattern）を直接書き換えて
    切り替える。
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
                    "filename_pattern": "tbl_{im_cable_system_name}_{timestamp}.csv",
                },
                "reports": {
                    "enabled": False,
                    "sub_dir": "reports",
                    "fit_summary_pattern": "report_fit_summary_{im_cable_system_name}_{timestamp}.csv",
                    "fitted_catalog_pattern": "report_model_{im_cable_system_name}_{timestamp}.yaml",
                    "numerical_stability_pattern": "report_numerical_stability_{im_cable_system_name}_{timestamp}.csv",
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


def _validate_residual_weights(weights: dict[str, float]) -> dict[str, float]:
    """残差重みの key を検証し、float 化した新しい辞書を返す。

    Args:
        weights: ``current`` / ``power`` / ``power_factor`` / ``efficiency`` を
            含む辞書。値は非負の数値。

    Returns:
        dict[str, float]: 正規化済みの重み辞書（key 集合は不変）。

    Raises:
        ValueError: 想定外の key が含まれる、key が不足する、値が非数値・負値の
            いずれかに該当した場合。
    """
    expected = set(ESTIMATE_PARAMS_RESIDUAL_WEIGHT_KEYS)
    actual = set(weights.keys())
    if actual != expected:
        raise ValueError(
            "estimate_params residual weights の key が想定と異なります: "
            f"expected={sorted(expected)}, actual={sorted(actual)}"
        )
    normalized: dict[str, float] = {}
    for key in ESTIMATE_PARAMS_RESIDUAL_WEIGHT_KEYS:
        value = weights[key]
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ValueError(
                f"estimate_params residual weight '{key}' は数値である必要があります: "
                f"value={value!r}"
            )
        if value < 0.0:
            raise ValueError(
                f"estimate_params residual weight '{key}' は非負である必要があります: "
                f"value={value}"
            )
        normalized[key] = float(value)
    return normalized


def _estimate_params_override(
    residual_weights: dict[str, float],
) -> dict[str, Any]:
    """estimate_params all stage 用の最適化・残差設定 override。

    リグレッション基準値（終点残差・cost・チャネル別 RMSE）に直接効くため、
    残差正規化方式と optimizer 設定をテスト側でピン留めする。上位
    ``test_base_config.yaml`` の変更でゴールデンがずれないようにする狙い。
    """
    return {
        "calculation": {
            "execute": {
                "estimate_params": {
                    "residual": {
                        "weights": _validate_residual_weights(residual_weights),
                        "normalization": {
                            "method": "by_curve_scale",
                            "by_curve_scale": {
                                "statistic": "std",
                                "eps": 1.0e-12,
                            },
                        },
                    },
                    "optimizer": {
                        "algorithm": "least_squares",
                        "least_squares": {
                            "max_nfev": ESTIMATE_PARAMS_MAX_NFEV,
                            "ftol": 1.0e-4,
                            "xtol": 1.0e-4,
                            "gtol": 1.0e-4,
                        },
                    },
                },
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
        dump_base_dir=_this_dir().resolve(),
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
def estimate_params_max_nfev() -> int:
    """estimate_params all stage で設定する max_nfev。"""
    return ESTIMATE_PARAMS_MAX_NFEV


@pytest.fixture
def estimate_params_residual_weights() -> dict[str, float]:
    """estimate_params 残差の各目的値重み。

    テスト側で重みを変えたい場合は、テストモジュール内で同名 fixture を
    定義して上書きする。key 集合
    （``current`` / ``power`` / ``power_factor`` / ``efficiency``）は維持する。
    """
    return dict(DEFAULT_ESTIMATE_PARAMS_RESIDUAL_WEIGHTS)


@pytest.fixture
def all_stage_estimate_params_config(
    tmp_path: Path,
    estimate_params_residual_weights: dict[str, float],
) -> IConfig:
    """estimate_params pipeline 用 :class:`IConfig`。"""
    override = _deep_merge(
        _figure_dump_override(),
        _estimate_params_override(estimate_params_residual_weights),
    )
    return _create_config(tmp_path=tmp_path, override=override)
