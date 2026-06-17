"""Forward 系（CartesianGrid / OperatingPoints 共通）ローダの単体テスト。

``ForwardLoader.load()`` が ``ForwardInputLoadedData`` を期待形で返すこと、
両モード用の軸 TSV のいずれでも 1 次元・有限値の軸データを得られることを
確認する。CartesianGrid / OperatingPoints の意味づけ（直積 / co-indexed）は
ローダの責務ではないため、本テストではセマンティクスは確認しない。
"""

from __future__ import annotations

import numpy as np

from im_cable_system.engine.algorithm.input_algorithm.load_data import (
    ForwardLoader,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.job_spec.forward import (
    ForwardJobSpec,
)
from tests.test_algorithm.test_input_algorithm._input_algorithm_helpers import (
    input_files_dir,
)


def _make_spec_for_cartesian_grid_axes() -> ForwardJobSpec:
    return ForwardJobSpec(
        series_selection_path=(
            input_files_dir() / "series_forward" / "basic01_nocable.tsv"
        ),
        axes_path=(
            input_files_dir()
            / "axes_forward_by_cartesian_grid"
            / "cartesian_grid_v1.tsv"
        ),
    )


def _make_spec_for_operating_points_axes() -> ForwardJobSpec:
    return ForwardJobSpec(
        series_selection_path=(
            input_files_dir() / "series_forward" / "basic01_nocable.tsv"
        ),
        axes_path=(
            input_files_dir()
            / "axes_forward_by_operating_points"
            / "operating_points_v1.tsv"
        ),
    )


def test_forward_loader_reads_cartesian_grid_axes(
    config: IConfig,
    logger: ILogger,
) -> None:
    """CartesianGrid 用軸 TSV を ``ForwardLoader`` が読み込む。"""
    loader = ForwardLoader.create(config=config, logger=logger)
    loaded = loader.load(_make_spec_for_cartesian_grid_axes())
    assert loaded.im_cable_system_name
    assert loaded.im is not None
    axes = loaded.axes
    assert axes.slip.size > 0
    assert axes.frequency.size > 0
    assert axes.input_line_voltage.size > 0
    assert np.all(np.isfinite(axes.slip))


def test_forward_loader_reads_operating_points_axes(
    config: IConfig,
    logger: ILogger,
) -> None:
    """OperatingPoints 用軸 TSV を ``ForwardLoader`` が行ごとに読み込む。"""
    loader = ForwardLoader.create(config=config, logger=logger)
    loaded = loader.load(_make_spec_for_operating_points_axes())
    points = loaded.axes
    n_points = int(points.slip.size)
    assert n_points > 0
    assert points.frequency.size == n_points
    assert points.input_line_voltage.size == n_points
    assert np.all(np.isfinite(points.slip))
