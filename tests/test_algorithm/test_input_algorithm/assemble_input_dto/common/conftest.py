"""assemble_input_dto/common テスト共通フィクスチャ。

``common/`` 配下の組み立てヘルパは経路非依存だが、テストで実
``InputDto`` を最小コストで用意するため Forward Orchestrator を経由する。
各テストは fixture ``build_cartesian_dto`` を介して SI 化済みの正常 DTO
を取得し、必要なフィールドだけ ``dataclasses.replace`` で差し替えて
common 関数を直接呼ぶ。
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

from im_cable_system.engine.algorithm.input_algorithm.orchestrate.forward import (  # noqa: E501
    ForwardInputOrchestrator,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ArrayKey,
)
from im_cable_system.engine.shared.dto.input import (
    InputDto,
)
from im_cable_system.engine.shared.job_spec.forward import (
    ForwardJobSpec,
)
from tests.test_algorithm.test_input_algorithm._input_algorithm_helpers import (
    input_files_dir,
)

_CARTESIAN_GRID_REFERENCE_AXES: list[ArrayKey] = [
    ArrayKey.SLIP,
    ArrayKey.INPUT_LINE_VOLTAGE,
    ArrayKey.FREQUENCY,
]


@pytest.fixture
def build_cartesian_dto(
    config: IConfig,
    logger: ILogger,
) -> Callable[..., InputDto]:
    """Forward Cartesian 経路で実 :class:`InputDto` を組み立てるファクトリ fixture。

    Args:
        config: テスト用 :class:`IConfig`。
        logger: テスト用 :class:`ILogger`。

    Returns:
        Callable[..., InputDto]: ``series_path`` / ``performance_curve_path``
        を上書きできるファクトリ関数。
    """

    def _build(
        *,
        series_path: str = "basic01_nocable.tsv",
        performance_curve_path: Path | None = None,
    ) -> InputDto:
        spec = ForwardJobSpec(
            series_selection_path=(
                input_files_dir() / "series_forward" / series_path
            ),
            axes_path=(
                input_files_dir()
                / "axes_forward_by_cartesian_grid"
                / "cartesian_grid_v1.tsv"
            ),
            performance_curve_path=performance_curve_path,
        )
        return ForwardInputOrchestrator.create(
            config=config,
            logger=logger,
            reference_axes=_CARTESIAN_GRID_REFERENCE_AXES,
        ).build_input_dto(spec)

    return _build
