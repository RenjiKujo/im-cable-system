"""``build_command`` が組む argv を、実 runner の argparse が実際に受け取れること。

``command_builder`` は runner のフラグ名を手写ししている。偽 runner
（``tests/test_apps/test_web/api/data/fake_runners/``）もフラグ名を手写しなので、
両者が揃って間違っていても api テストは緑のまま通る。実 runner を回す
``test_e2e_real_engine.py`` は ``slow`` で CI から外れるため、
**フラグ名の一致を CI で見ているのはこのファイルだけ**である。

計算は一切走らせない。``_parse_args`` にだけ通し、引数名と必須性の契約を固定する。
内部実装の単体テスト: runner の ``_parse_args`` を直接参照する。
"""

from __future__ import annotations

from pathlib import Path

import pytest

from apps.web.runner_gateway import (
    EstimateParamsInputs,
    ForwardInputs,
    JobInputs,
    JobLayout,
    JobMode,
    RunnerGatewaySettings,
    build_command,
)
from runner.run_estimate_params import _parse_args as parse_estimate_params_args
from runner.run_forward_by_cartesian_grid import (
    _parse_args as parse_cartesian_grid_args,
)
from runner.run_forward_by_operating_points import (
    _parse_args as parse_operating_points_args,
)

_REPO_ROOT = Path(__file__).resolve().parents[4]

_PARSER_BY_MODE = {
    JobMode.ESTIMATE_PARAMS: parse_estimate_params_args,
    JobMode.FORWARD_BY_CARTESIAN_GRID: parse_cartesian_grid_args,
    JobMode.FORWARD_BY_OPERATING_POINTS: parse_operating_points_args,
}


def _settings(tmp_path: Path) -> RunnerGatewaySettings:
    """実 runner を指す設定（起動はしないのでパスの実在だけが要る）。"""
    return RunnerGatewaySettings(
        repo_root=_REPO_ROOT,
        python_executable=Path("/usr/bin/python3"),
        runner_dir=_REPO_ROOT / "runner",
        jobs_root=tmp_path / "jobs",
        max_concurrent_jobs=1,
        job_timeout_seconds=10.0,
    )


def _inputs_for(mode: JobMode, tmp_path: Path) -> JobInputs:
    if mode is JobMode.ESTIMATE_PARAMS:
        return EstimateParamsInputs(
            input_csv_path=tmp_path / "input.csv",
            im_bounds_path=tmp_path / "im_bounds.yaml",
            cable_bounds_path=tmp_path / "cable_bounds.yaml",
        )
    return ForwardInputs(
        series_selection_path=tmp_path / "series.yaml",
        axes_path=tmp_path / "axes.yaml",
        im_catalog_path=tmp_path / "im_catalog.yaml",
        cable_catalog_path=tmp_path / "cable_catalog.yaml",
    )


class TestRunnerCliContract:
    """3 モードとも、組んだ argv が実 runner の argparse を通る。"""

    @pytest.mark.parametrize("mode", list(JobMode))
    def test_built_argv_parses_with_the_real_runner(
        self, mode: JobMode, tmp_path: Path
    ) -> None:
        """未知フラグがあれば argparse が SystemExit(2) を投げる。

        これが CI で落ちるのは「runner のフラグが変わったのに
        ``command_builder`` が追随していない」ときで、放置すると
        全ジョブが exit 2（``error_kind = "validation"``）になる。
        """
        settings = _settings(tmp_path)
        layout = JobLayout.create(settings.jobs_root, "job-cli-contract")
        argv = build_command(
            mode, layout, _inputs_for(mode, tmp_path), settings
        )

        # 先頭 2 要素は python 実行パスとスクリプトパスで、argparse の対象外。
        args = _PARSER_BY_MODE[mode](argv[2:])

        assert args.config == layout.config_path
        assert args.dump_base_dir == layout.output_dir

    def test_estimate_params_flags_map_to_the_expected_destinations(
        self, tmp_path: Path
    ) -> None:
        settings = _settings(tmp_path)
        layout = JobLayout.create(settings.jobs_root, "job-estimate")
        inputs = _inputs_for(JobMode.ESTIMATE_PARAMS, tmp_path)
        assert isinstance(inputs, EstimateParamsInputs)

        argv = build_command(JobMode.ESTIMATE_PARAMS, layout, inputs, settings)
        args = parse_estimate_params_args(argv[2:])

        assert args.input == inputs.input_csv_path
        assert args.im_bounds == inputs.im_bounds_path
        assert args.cable_bounds == inputs.cable_bounds_path

    @pytest.mark.parametrize(
        "mode",
        [
            JobMode.FORWARD_BY_CARTESIAN_GRID,
            JobMode.FORWARD_BY_OPERATING_POINTS,
        ],
    )
    def test_forward_flags_map_to_the_expected_destinations(
        self, mode: JobMode, tmp_path: Path
    ) -> None:
        settings = _settings(tmp_path)
        layout = JobLayout.create(settings.jobs_root, "job-forward")
        inputs = _inputs_for(mode, tmp_path)
        assert isinstance(inputs, ForwardInputs)

        argv = build_command(mode, layout, inputs, settings)
        args = _PARSER_BY_MODE[mode](argv[2:])

        assert args.series_selection == inputs.series_selection_path
        assert args.axes == inputs.axes_path
        assert args.im_catalog == inputs.im_catalog_path
        assert args.cable_catalog == inputs.cable_catalog_path

    @pytest.mark.parametrize(
        "mode",
        [
            JobMode.FORWARD_BY_CARTESIAN_GRID,
            JobMode.FORWARD_BY_OPERATING_POINTS,
        ],
    )
    def test_optional_performance_curve_is_accepted(
        self, mode: JobMode, tmp_path: Path
    ) -> None:
        """``performance_curve`` は省略可。載せたときも runner が受け取れる。"""
        settings = _settings(tmp_path)
        layout = JobLayout.create(settings.jobs_root, "job-curve")
        inputs = ForwardInputs(
            series_selection_path=tmp_path / "series.yaml",
            axes_path=tmp_path / "axes.yaml",
            im_catalog_path=tmp_path / "im_catalog.yaml",
            cable_catalog_path=tmp_path / "cable_catalog.yaml",
            performance_curve_path=tmp_path / "curve.csv",
        )

        argv = build_command(mode, layout, inputs, settings)
        args = _PARSER_BY_MODE[mode](argv[2:])

        assert args.performance_curve == inputs.performance_curve_path

    def test_runner_scripts_referenced_by_the_builder_exist(
        self, tmp_path: Path
    ) -> None:
        """argv が指すスクリプトが実在する（``tmp_path`` を repo_root にすると見落とす）。"""
        settings = _settings(tmp_path)
        layout = JobLayout.create(settings.jobs_root, "job-exists")
        for mode in JobMode:
            argv = build_command(
                mode, layout, _inputs_for(mode, tmp_path), settings
            )
            assert Path(argv[1]).is_file(), f"{mode.value}: {argv[1]}"
