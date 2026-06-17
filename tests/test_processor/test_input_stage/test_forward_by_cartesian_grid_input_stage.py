"""ForwardByCartesianGridInputStage の疎通テスト（最小構成）。

algorithm 層で詳細をカバーしているため、本ステージでは IStage 契約
（``process``）の疎通と、CartesianGrid モード固有の
``reference_axes = [SLIP, INPUT_LINE_VOLTAGE, FREQUENCY]`` が
``ArrayLayoutDto`` に伝播することのみを確認する。
"""

from __future__ import annotations

from pathlib import Path

from im_cable_system.engine.processor.input_stage import (
    ForwardByCartesianGridInputStage,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ArrayKey,
)
from im_cable_system.engine.shared.dto.input import InputDto
from im_cable_system.engine.shared.job_spec.forward import (
    ForwardJobSpec,
    ForwardJobSpecs,
)

_CARTESIAN_GRID_REFERENCE_AXES: list[ArrayKey] = [
    ArrayKey.SLIP,
    ArrayKey.INPUT_LINE_VOLTAGE,
    ArrayKey.FREQUENCY,
]


def _make_job_spec(input_files_dir: Path) -> ForwardJobSpec:
    """CartesianGrid 用の 1 ジョブ spec を作る（ケーブル無しの簡易ケース）。"""
    return ForwardJobSpec(
        series_selection_path=(
            input_files_dir / "series_forward" / "basic01_nocable.tsv"
        ),
        axes_path=(
            input_files_dir
            / "axes_forward_by_cartesian_grid"
            / "cartesian_grid_v1.tsv"
        ),
    )


def test_process_returns_one_input_dto_per_spec_with_cartesian_reference_axes(
    config: IConfig,
    logger: ILogger,
    input_files_dir: Path,
) -> None:
    """1 spec → 1 InputDto、CartesianGrid の reference_axes が伝播する。"""
    job_specs = ForwardJobSpecs(specs=(_make_job_spec(input_files_dir),))

    stage = ForwardByCartesianGridInputStage.create(
        config=config,
        logger=logger,
    )
    inputs = stage.process(job_specs)

    dtos = inputs.get_all()
    assert len(dtos) == len(job_specs.specs)
    dto = dtos[0]
    assert isinstance(dto, InputDto)
    assert dto.array_layout.reference_axes == _CARTESIAN_GRID_REFERENCE_AXES


def test_process_returns_empty_for_empty_specs(
    config: IConfig,
    logger: ILogger,
) -> None:
    """空 specs では空 InputDtos を返す（ガード分岐の確認）。"""
    stage = ForwardByCartesianGridInputStage.create(
        config=config,
        logger=logger,
    )
    inputs = stage.process(ForwardJobSpecs(specs=()))
    assert inputs.get_all() == []
