"""Forward 系（CartesianGrid / OperatingPoints 共通）アセンブラの単体テスト。

``ForwardLoader`` で得た中間表現を ``ForwardInputDtoAssembler`` に通し、
InputDto が組み立つことをモードごとに確認する。

- CartesianGrid 用軸 TSV: ``reference_axes = [SLIP, INPUT_LINE_VOLTAGE,
  FREQUENCY]`` を指定し、3 軸独立の直積として ``ArrayLayoutDto`` を作る。
- OperatingPoints 用軸 TSV: ``reference_axes = [SLIP]`` を指定し、
  ``frequency`` / ``input_line_voltage`` を非参照軸として co-indexed の
  運転点列として ``ArrayLayoutDto`` を作る。
"""

from __future__ import annotations

from im_cable_system.engine.algorithm.input_algorithm.assemble_input_dto import (
    ForwardInputDtoAssembler,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data import (
    ForwardLoader,
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


def _make_spec_for_cartesian_grid() -> ForwardJobSpec:
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


def _make_spec_for_operating_points() -> ForwardJobSpec:
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


def test_assembler_builds_input_dto_from_cartesian_grid(
    config: IConfig,
    logger: ILogger,
) -> None:
    """CartesianGrid 用軸 TSV から InputDto が組み立つ（参照軸 = 3 軸）。"""
    loaded = ForwardLoader.create(
        config=config,
        logger=logger,
    ).load(_make_spec_for_cartesian_grid())
    dto = ForwardInputDtoAssembler.create(
        config=config,
        logger=logger,
        reference_axes=[
            ArrayKey.SLIP,
            ArrayKey.INPUT_LINE_VOLTAGE,
            ArrayKey.FREQUENCY,
        ],
    ).assemble(loaded_data=loaded)
    assert dto.name.get_value()
    assert dto.im is not None
    assert dto.array_layout.reference_axes == [
        ArrayKey.SLIP,
        ArrayKey.INPUT_LINE_VOLTAGE,
        ArrayKey.FREQUENCY,
    ]


def test_assembler_builds_input_dto_from_operating_points(
    config: IConfig,
    logger: ILogger,
) -> None:
    """OperatingPoints 用軸 TSV から InputDto が組み立つ（参照軸 = SLIP のみ）。"""
    loaded = ForwardLoader.create(
        config=config,
        logger=logger,
    ).load(_make_spec_for_operating_points())
    dto = ForwardInputDtoAssembler.create(
        config=config,
        logger=logger,
        reference_axes=[ArrayKey.SLIP],
    ).assemble(loaded_data=loaded)
    assert dto.name.get_value()
    assert dto.im is not None
    assert dto.array_layout.reference_axes == [ArrayKey.SLIP]
