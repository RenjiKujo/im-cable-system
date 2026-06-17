"""Forward Loader → Assembler の単位責務 pair を契約として固定する。

責務分離の意図:
    - **Forward Loader**: 単位文字列を ``strip()`` のみ施した raw な値で
      保持する。``[%]`` / ``[-]`` のような比率単位の TSV も読み込み自体
      は拒否しない（``ImPerformanceCurveLoadedData`` の docstring 参照）。
    - **Forward Assembler**: 性能曲線 ``power`` / ``current`` / ``torque``
      列が比率単位（``-`` / ``%``）だった場合は ``ValueError`` で拒否する。

本テストは「同じ TSV を Loader に通すと成功し、Assembler に通すと
``ValueError`` になる」という Loader/Assembler 責務 pair を、
TSV 1 件に対して 1 ペアの assertion で固定する。
"""

from __future__ import annotations

from pathlib import Path

import pytest

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

_CARTESIAN_GRID_REFERENCE_AXES = [
    ArrayKey.SLIP,
    ArrayKey.INPUT_LINE_VOLTAGE,
    ArrayKey.FREQUENCY,
]

_META_BLOCK = (
    "im_performance_curve_name\tTest\n"
    "name\tvalue\tunit\n"
    "poles\t4\t-\n"
    "supply_frequency\t50\tHz\n"
    "supply_voltage\t200\tV\n"
    "\n"
)


def _series_forward_dir() -> Path:
    return input_files_dir() / "series_forward"


def _axes_forward_by_cartesian_grid_dir() -> Path:
    return input_files_dir() / "axes_forward_by_cartesian_grid"


def _make_spec(performance_curve_path: Path) -> ForwardJobSpec:
    return ForwardJobSpec(
        series_selection_path=(_series_forward_dir() / "basic01_nocable.tsv"),
        axes_path=(
            _axes_forward_by_cartesian_grid_dir() / "cartesian_grid_v1.tsv"
        ),
        performance_curve_path=performance_curve_path,
    )


def _write_tsv(path: Path, body: str) -> None:
    path.write_text(_META_BLOCK + body, encoding="utf-8")


class TestForwardLoaderAcceptsRatioUnitButAssemblerRejects:
    """同一 TSV について、Loader は通り Assembler は raise する pair。"""

    def test_power_dash_unit_pair(
        self,
        config: IConfig,
        logger: ILogger,
        tmp_path: Path,
    ) -> None:
        """``power=[-]`` の TSV は Loader 通過、Assembler で ``ValueError``。"""
        path = tmp_path / "pc_power_dash.tsv"
        _write_tsv(
            path,
            "rotational_speed\tpower\n[rpm]\t[-]\n1500\t0.1\n1490\t0.2\n",
        )
        loader = ForwardLoader.create(config=config, logger=logger)
        loaded = loader.load(_make_spec(path))
        pc = loaded.im_performance_curve
        assert pc is not None
        assert pc.power_unit == "[-]"
        assert pc.power is not None

        assembler = ForwardInputDtoAssembler.create(
            config=config,
            logger=logger,
            reference_axes=_CARTESIAN_GRID_REFERENCE_AXES,
        )
        with pytest.raises(
            ValueError,
            match=r"性能曲線ビルダーでは power 列の比率単位",
        ):
            assembler.assemble(loaded_data=loaded)

    def test_current_percent_unit_pair(
        self,
        config: IConfig,
        logger: ILogger,
        tmp_path: Path,
    ) -> None:
        """``current=[%]`` の TSV は Loader 通過、Assembler で ``ValueError``。"""
        path = tmp_path / "pc_current_percent.tsv"
        _write_tsv(
            path,
            "rotational_speed\tcurrent\n[rpm]\t[%]\n1500\t12.0\n1490\t15.0\n",
        )
        loader = ForwardLoader.create(config=config, logger=logger)
        loaded = loader.load(_make_spec(path))
        pc = loaded.im_performance_curve
        assert pc is not None
        assert pc.current_unit == "[%]"
        assert pc.current is not None

        assembler = ForwardInputDtoAssembler.create(
            config=config,
            logger=logger,
            reference_axes=_CARTESIAN_GRID_REFERENCE_AXES,
        )
        with pytest.raises(
            ValueError,
            match=r"性能曲線ビルダーでは current 列の比率単位",
        ):
            assembler.assemble(loaded_data=loaded)

    def test_torque_percent_unit_pair(
        self,
        config: IConfig,
        logger: ILogger,
        tmp_path: Path,
    ) -> None:
        """``torque=[%]`` の TSV は Loader 通過、Assembler で ``ValueError``。"""
        path = tmp_path / "pc_torque_percent.tsv"
        _write_tsv(
            path,
            "rotational_speed\ttorque\n[rpm]\t[%]\n1500\t10.0\n1490\t20.0\n",
        )
        loader = ForwardLoader.create(config=config, logger=logger)
        loaded = loader.load(_make_spec(path))
        pc = loaded.im_performance_curve
        assert pc is not None
        assert pc.torque_unit == "[%]"
        assert pc.torque is not None

        assembler = ForwardInputDtoAssembler.create(
            config=config,
            logger=logger,
            reference_axes=_CARTESIAN_GRID_REFERENCE_AXES,
        )
        with pytest.raises(
            ValueError,
            match=r"性能曲線ビルダーでは torque 列の比率単位",
        ):
            assembler.assemble(loaded_data=loaded)
