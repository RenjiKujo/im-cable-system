"""command_builder: 3 モード分の argv を固定する。"""

from __future__ import annotations

from pathlib import Path

import pytest

from apps.web.runner_gateway import (
    EstimateParamsInputs,
    ForwardInputs,
    JobLayout,
    JobMode,
    RunnerGatewaySettings,
    build_command,
)


def _settings(tmp_path: Path) -> RunnerGatewaySettings:
    return RunnerGatewaySettings(
        repo_root=tmp_path / "repo",
        python_executable=tmp_path / "repo" / ".venv" / "bin" / "python",
        runner_dir=tmp_path / "repo" / "runner",
        jobs_root=tmp_path / "jobs",
        max_concurrent_jobs=2,
        job_timeout_seconds=1800.0,
    )


def _layout(tmp_path: Path) -> JobLayout:
    return JobLayout.create(tmp_path / "jobs", "job-1")


class TestBuildCommand:
    """mode ごとの argv 固定。"""

    def test_estimate_params_argv(self, tmp_path: Path) -> None:
        settings = _settings(tmp_path)
        layout = _layout(tmp_path)
        inputs = EstimateParamsInputs(
            input_csv_path=tmp_path / "inputs" / "input.csv",
            im_bounds_path=tmp_path / "im_bounds.yaml",
            cable_bounds_path=tmp_path / "cable_bounds.yaml",
        )

        argv = build_command(JobMode.ESTIMATE_PARAMS, layout, inputs, settings)

        assert argv[0] == str(settings.python_executable)
        assert argv[1] == str(settings.runner_dir / "run_estimate_params.py")
        assert "--input" in argv
        assert argv[argv.index("--input") + 1] == str(inputs.input_csv_path)
        assert argv[argv.index("--config") + 1] == str(layout.config_path)
        assert argv[argv.index("--im-bounds") + 1] == str(inputs.im_bounds_path)
        assert argv[argv.index("--cable-bounds") + 1] == str(
            inputs.cable_bounds_path
        )
        assert argv[argv.index("--dump-base-dir") + 1] == str(layout.output_dir)

    def test_forward_by_cartesian_grid_argv(self, tmp_path: Path) -> None:
        settings = _settings(tmp_path)
        layout = _layout(tmp_path)
        inputs = ForwardInputs(
            series_selection_path=tmp_path / "series.csv",
            axes_path=tmp_path / "axes.csv",
            im_catalog_path=tmp_path / "im_catalog.yaml",
            cable_catalog_path=tmp_path / "cable_catalog.yaml",
        )

        argv = build_command(
            JobMode.FORWARD_BY_CARTESIAN_GRID, layout, inputs, settings
        )

        assert argv[1] == str(
            settings.runner_dir / "run_forward_by_cartesian_grid.py"
        )
        assert argv[argv.index("--series-selection") + 1] == str(
            inputs.series_selection_path
        )
        assert argv[argv.index("--axes") + 1] == str(inputs.axes_path)
        assert argv[argv.index("--im-catalog") + 1] == str(
            inputs.im_catalog_path
        )
        assert argv[argv.index("--cable-catalog") + 1] == str(
            inputs.cable_catalog_path
        )
        assert "--performance-curve" not in argv
        assert argv[argv.index("--dump-base-dir") + 1] == str(layout.output_dir)

    def test_forward_by_operating_points_argv_with_performance_curve(
        self, tmp_path: Path
    ) -> None:
        settings = _settings(tmp_path)
        layout = _layout(tmp_path)
        inputs = ForwardInputs(
            series_selection_path=tmp_path / "series.csv",
            axes_path=tmp_path / "axes.csv",
            im_catalog_path=tmp_path / "im_catalog.yaml",
            cable_catalog_path=tmp_path / "cable_catalog.yaml",
            performance_curve_path=tmp_path / "performance_curve.csv",
        )

        argv = build_command(
            JobMode.FORWARD_BY_OPERATING_POINTS, layout, inputs, settings
        )

        assert argv[1] == str(
            settings.runner_dir / "run_forward_by_operating_points.py"
        )
        assert argv[argv.index("--performance-curve") + 1] == str(
            inputs.performance_curve_path
        )

    def test_mode_input_mismatch_raises(self, tmp_path: Path) -> None:
        settings = _settings(tmp_path)
        layout = _layout(tmp_path)
        forward_inputs = ForwardInputs(
            series_selection_path=tmp_path / "series.csv",
            axes_path=tmp_path / "axes.csv",
            im_catalog_path=tmp_path / "im_catalog.yaml",
            cable_catalog_path=tmp_path / "cable_catalog.yaml",
        )

        with pytest.raises(ValueError, match="EstimateParamsInputs"):
            build_command(
                JobMode.ESTIMATE_PARAMS, layout, forward_inputs, settings
            )
