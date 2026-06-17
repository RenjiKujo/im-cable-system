"""Forward アセンブラの導体モデル組み立てテスト。

シリーズ TSV → カタログ YAML 引き当て → ``CableDto.conductor_model`` の
組み立てパスを CartesianGrid 用軸 TSV で代表検証する。導体モデル組み立ては
両モードで同一の ``ForwardInputDtoAssembler`` が担う。
"""

from __future__ import annotations

from pathlib import Path

from im_cable_system.engine.algorithm.input_algorithm.assemble_input_dto import (
    ForwardInputDtoAssembler,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data import (
    ForwardLoader,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ArrayKey,
    ConductorModelType,
)
from im_cable_system.engine.shared.job_spec.forward import (
    ForwardJobSpec,
)
from tests.test_algorithm.test_input_algorithm._input_algorithm_helpers import (
    input_files_dir,
)

_CARTESIAN_GRID_REFERENCE_AXES = [
    ArrayKey.SLIP,
    ArrayKey.INPUT_LINE_VOLTAGE,
    ArrayKey.FREQUENCY,
]


def _series_forward_dir() -> Path:
    return input_files_dir() / "series_forward"


def _axes_forward_by_cartesian_grid_dir() -> Path:
    return input_files_dir() / "axes_forward_by_cartesian_grid"


def _make_spec(
    *,
    series_csv_path: Path,
    axes_csv_path: Path,
) -> ForwardJobSpec:
    return ForwardJobSpec(
        series_selection_path=series_csv_path,
        axes_path=axes_csv_path,
    )


class TestForwardAssemblerConductorModel:
    """カタログプロファイルから CableDto.conductor_model を組み立てる。"""

    def test_assemble_current_dependent_skin_cable(
        self,
        config: IConfig,
        logger: ILogger,
    ) -> None:
        """CurrentDependentSkin01 が InputDto に載ること。"""
        spec = _make_spec(
            series_csv_path=(
                _series_forward_dir()
                / "currentdependent01_real_feeder30m_real_lead10m.tsv"
            ),
            axes_csv_path=(
                _axes_forward_by_cartesian_grid_dir() / "cartesian_grid_v1.tsv"
            ),
        )
        loaded = ForwardLoader.create(
            config=config,
            logger=logger,
        ).load(spec)
        dto = ForwardInputDtoAssembler.create(
            config=config,
            logger=logger,
            reference_axes=_CARTESIAN_GRID_REFERENCE_AXES,
        ).assemble(loaded_data=loaded)
        assert dto.cable is not None
        assert (
            dto.cable.conductor_model.name
            == ConductorModelType.CURRENT_DEPENDENT_SKIN_EFFECT_V1
        )
        assert dto.cable.conductor_model.params is not None

    def test_assemble_nocable_has_no_cable(
        self,
        config: IConfig,
        logger: ILogger,
    ) -> None:
        """nocable は cable None。"""
        spec = _make_spec(
            series_csv_path=_series_forward_dir() / "basic01_nocable.tsv",
            axes_csv_path=(
                _axes_forward_by_cartesian_grid_dir() / "cartesian_grid_v1.tsv"
            ),
        )
        loaded = ForwardLoader.create(
            config=config,
            logger=logger,
        ).load(spec)
        dto = ForwardInputDtoAssembler.create(
            config=config,
            logger=logger,
            reference_axes=_CARTESIAN_GRID_REFERENCE_AXES,
        ).assemble(loaded_data=loaded)
        assert dto.cable is None
