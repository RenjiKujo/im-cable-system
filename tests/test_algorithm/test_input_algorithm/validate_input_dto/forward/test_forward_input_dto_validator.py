"""``ForwardInputDtoValidator`` の経路 E2E テスト。

経路非依存の検査（SI 単位 / cross-field / grid size など）の詳細は
``validate_input_dto/common/`` 配下の単体テストで担保するので、本ファイル
では以下の 2 点に絞る。

* CartesianGrid / OperatingPoints / cable 付き / PC 付き の代表 4 ケースで
  ``ForwardInputDtoValidator.validate`` が pass すること（HappyPath）。
* Forward Validator が ``common/`` の検査関数を実際に呼び出していることを
  確認するスモーク 1 件。
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

import numpy as np
import pytest

from im_cable_system.engine.algorithm.input_algorithm.orchestrate.forward import (  # noqa: E501
    ForwardInputOrchestrator,
)
from im_cable_system.engine.algorithm.input_algorithm.validate_input_dto import (
    ForwardInputDtoValidator,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ArrayKey,
)
from im_cable_system.engine.shared.dto.generic.interfaces import (
    IArrayWithUnitDto,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexVoltageDto,
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
_OPERATING_POINTS_REFERENCE_AXES: list[ArrayKey] = [ArrayKey.SLIP]

_META_BLOCK = (
    "im_performance_curve_name\tTest\n"
    "name\tvalue\tunit\n"
    "poles\t4\t-\n"
    "supply_frequency\t50\tHz\n"
    "supply_voltage\t200\tV\n"
    "\n"
)


def _cartesian_spec(
    *,
    series_path: str = "basic01_nocable.tsv",
    performance_curve_path: Path | None = None,
) -> ForwardJobSpec:
    return ForwardJobSpec(
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


def _operating_points_spec() -> ForwardJobSpec:
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


def _build_cartesian_dto(
    config: IConfig,
    logger: ILogger,
    *,
    series_path: str = "basic01_nocable.tsv",
    performance_curve_path: Path | None = None,
) -> InputDto:
    return ForwardInputOrchestrator.create(
        config=config,
        logger=logger,
        reference_axes=_CARTESIAN_GRID_REFERENCE_AXES,
    ).build_input_dto(
        _cartesian_spec(
            series_path=series_path,
            performance_curve_path=performance_curve_path,
        )
    )


def _build_operating_points_dto(
    config: IConfig,
    logger: ILogger,
) -> InputDto:
    return ForwardInputOrchestrator.create(
        config=config,
        logger=logger,
        reference_axes=_OPERATING_POINTS_REFERENCE_AXES,
    ).build_input_dto(_operating_points_spec())


def _validator(
    config: IConfig,
    logger: ILogger,
) -> ForwardInputDtoValidator:
    return ForwardInputDtoValidator.create(config=config, logger=logger)


def _replace_axis(
    dto: InputDto,
    key: ArrayKey,
    axis_dto: IArrayWithUnitDto,
) -> InputDto:
    new_arrays = dict(dto.array_layout.arrays)
    new_arrays[key] = axis_dto
    new_layout = dataclasses.replace(
        dto.array_layout,
        arrays=new_arrays,
    )
    return dataclasses.replace(dto, array_layout=new_layout)


class TestForwardInputDtoValidatorHappyPath:
    """経路の代表ケースを通す。"""

    def test_accepts_cartesian_grid_built_dto(
        self,
        config: IConfig,
        logger: ILogger,
    ) -> None:
        dto = _build_cartesian_dto(config, logger)
        _validator(config, logger).validate(dto)

    def test_accepts_operating_points_built_dto(
        self,
        config: IConfig,
        logger: ILogger,
    ) -> None:
        dto = _build_operating_points_dto(config, logger)
        _validator(config, logger).validate(dto)

    def test_accepts_cartesian_with_cable(
        self,
        config: IConfig,
        logger: ILogger,
    ) -> None:
        dto = _build_cartesian_dto(
            config,
            logger,
            series_path="slipdependent01_ideal_feeder30m_ideal_lead10m.tsv",
        )
        _validator(config, logger).validate(dto)

    def test_accepts_cartesian_with_performance_curve(
        self,
        config: IConfig,
        logger: ILogger,
        tmp_path: Path,
    ) -> None:
        path = tmp_path / "pc_ok.tsv"
        path.write_text(
            _META_BLOCK + "rotational_speed\tpower\n"
            "[rpm]\t[kW]\n"
            "1500\t10.0\n"
            "1490\t9.5\n",
            encoding="utf-8",
        )
        dto = _build_cartesian_dto(
            config,
            logger,
            performance_curve_path=path,
        )
        _validator(config, logger).validate(dto)


class TestForwardInputDtoValidatorWiringSmoke:
    """Forward Validator が common/ 検査を実際に呼ぶことを確認するスモーク。

    common/ 各関数の詳細な異常系は
    ``validate_input_dto/common/test_*`` 側で網羅する。
    """

    def test_invokes_line_voltage_real_check(
        self,
        config: IConfig,
        logger: ILogger,
    ) -> None:
        dto = _build_cartesian_dto(config, logger)
        volt = dto.array_layout.arrays[ArrayKey.INPUT_LINE_VOLTAGE]
        bad_volt = ArrayComplexVoltageDto(
            value=np.array([-460.0 + 0.0j], dtype=np.complex128),
            unit=volt.get_unit(),
        )
        bad_dto = _replace_axis(dto, ArrayKey.INPUT_LINE_VOLTAGE, bad_volt)
        with pytest.raises(ValueError, match="input_line_voltage.*実部"):
            _validator(config, logger).validate(bad_dto)
