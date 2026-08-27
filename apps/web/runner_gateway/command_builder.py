"""mode + 入力パス束 → argv（3 モード分の registry）。純関数のみ。

catalog / bounds は必ず絶対パスで載せる。理由は
``config.yaml`` の相対参照がその config.yaml 自身の親ディレクトリ基準で
解決されるため（ジョブディレクトリへマテリアライズすると同梱パスとずれる罠を、
CLI 引数の明示で回避する。詳細は docs/apps/web/0_overview.md）。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from apps.web.runner_gateway.job_layout import JobLayout
from apps.web.runner_gateway.settings import RunnerGatewaySettings


class JobMode(str, Enum):
    """実行モード（store の ``jobs.mode`` と同じ語彙。engine 側に enum は無い）。"""

    ESTIMATE_PARAMS = "estimate_params"
    FORWARD_BY_CARTESIAN_GRID = "forward_by_cartesian_grid"
    FORWARD_BY_OPERATING_POINTS = "forward_by_operating_points"


_RUNNER_SCRIPT_BY_MODE: dict[JobMode, str] = {
    JobMode.ESTIMATE_PARAMS: "run_estimate_params.py",
    JobMode.FORWARD_BY_CARTESIAN_GRID: "run_forward_by_cartesian_grid.py",
    JobMode.FORWARD_BY_OPERATING_POINTS: "run_forward_by_operating_points.py",
}


@dataclass(frozen=True)
class EstimateParamsInputs:
    """``estimate_params`` の入力パス束（すべて絶対パス）。"""

    input_csv_path: Path
    im_bounds_path: Path
    cable_bounds_path: Path


@dataclass(frozen=True)
class ForwardInputs:
    """``forward_by_cartesian_grid`` / ``forward_by_operating_points`` 共通の入力パス束。"""

    series_selection_path: Path
    axes_path: Path
    im_catalog_path: Path
    cable_catalog_path: Path
    performance_curve_path: Path | None = None


JobInputs = EstimateParamsInputs | ForwardInputs


def _build_estimate_params_argv(
    layout: JobLayout, inputs: EstimateParamsInputs
) -> list[str]:
    return [
        "--input",
        str(inputs.input_csv_path),
        "--config",
        str(layout.config_path),
        "--im-bounds",
        str(inputs.im_bounds_path),
        "--cable-bounds",
        str(inputs.cable_bounds_path),
        "--dump-base-dir",
        str(layout.output_dir),
    ]


def _build_forward_argv(layout: JobLayout, inputs: ForwardInputs) -> list[str]:
    argv = [
        "--series-selection",
        str(inputs.series_selection_path),
        "--axes",
        str(inputs.axes_path),
    ]
    if inputs.performance_curve_path is not None:
        argv += ["--performance-curve", str(inputs.performance_curve_path)]
    argv += [
        "--config",
        str(layout.config_path),
        "--im-catalog",
        str(inputs.im_catalog_path),
        "--cable-catalog",
        str(inputs.cable_catalog_path),
        "--dump-base-dir",
        str(layout.output_dir),
    ]
    return argv


def build_command(
    mode: JobMode,
    layout: JobLayout,
    inputs: JobInputs,
    settings: RunnerGatewaySettings,
) -> list[str]:
    """mode に応じた runner 起動 argv を組み立てる（設定した venv の python 直指定）。

    Raises:
        ValueError: ``mode`` と ``inputs`` の型が対応しない場合、
            ``mode`` に対応する runner スクリプトが未登録の場合、
            または ``mode`` に対応する argv ビルダーが無い場合。
    """
    # 辞書引きは ``.get`` で受ける。添字だと ``JobMode`` メンバーを増やして
    # レジストリへの追加を忘れたとき KeyError が先に出て、下の ValueError
    # （＝runner の exit 2 / validation 扱い）へ到達しない。
    script_name = _RUNNER_SCRIPT_BY_MODE.get(mode)
    if script_name is None:
        raise ValueError(
            f"mode={mode.value} に対応する runner スクリプトがありません。"
        )
    script_path = settings.runner_dir / script_name
    argv = [str(settings.python_executable), str(script_path)]
    if mode is JobMode.ESTIMATE_PARAMS:
        if not isinstance(inputs, EstimateParamsInputs):
            raise ValueError(
                f"mode={mode.value} には EstimateParamsInputs が必要です。"
            )
        return [*argv, *_build_estimate_params_argv(layout, inputs)]
    if mode in (
        JobMode.FORWARD_BY_CARTESIAN_GRID,
        JobMode.FORWARD_BY_OPERATING_POINTS,
    ):
        if not isinstance(inputs, ForwardInputs):
            raise ValueError(
                f"mode={mode.value} には ForwardInputs が必要です。"
            )
        return [*argv, *_build_forward_argv(layout, inputs)]
    raise ValueError(
        f"mode={mode.value} に対応する argv ビルダーがありません。"
    )
