"""``ForwardInputOrchestrator`` 結合テスト（CartesianGrid / OperatingPoints 共通）。

両モードの違いは ``create`` に渡す ``reference_axes`` のみ。同じ
オーケストレーター実装で両モードの ``InputDto`` が組み立てられることを
契約として固定する。
"""

from __future__ import annotations

from im_cable_system.engine.algorithm.input_algorithm.orchestrate.forward import (  # noqa: E501
    ForwardInputOrchestrator,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ArrayKey,
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
_OPERATING_POINTS_REFERENCE_AXES: list[ArrayKey] = [ArrayKey.SLIP]


def _make_cartesian_grid_spec() -> ForwardJobSpec:
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


def _make_operating_points_spec() -> ForwardJobSpec:
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


def test_build_input_dto_cartesian_grid(
    config: IConfig,
    logger: ILogger,
) -> None:
    """CartesianGrid モードは reference_axes = [SLIP, VOLT, FREQ] を使う。"""
    orch = ForwardInputOrchestrator.create(
        config=config,
        logger=logger,
        reference_axes=_CARTESIAN_GRID_REFERENCE_AXES,
    )
    dto = orch.build_input_dto(_make_cartesian_grid_spec())
    assert dto.name.get_value()
    assert dto.im is not None
    assert dto.array_layout.reference_axes == _CARTESIAN_GRID_REFERENCE_AXES


def test_build_input_dto_operating_points(
    config: IConfig,
    logger: ILogger,
) -> None:
    """OperatingPoints モードは reference_axes = [SLIP] のみを使う。"""
    orch = ForwardInputOrchestrator.create(
        config=config,
        logger=logger,
        reference_axes=_OPERATING_POINTS_REFERENCE_AXES,
    )
    dto = orch.build_input_dto(_make_operating_points_spec())
    assert dto.name.get_value()
    assert dto.im is not None
    assert dto.array_layout.reference_axes == _OPERATING_POINTS_REFERENCE_AXES
