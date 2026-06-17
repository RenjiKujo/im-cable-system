"""Forward Assembler 出口で SI 基本単位に正規化されることのテスト。

``ForwardInputDtoAssembler.assemble()`` の最終段で :func:`to_si_input_dto`
を通すことで、``InputDto`` 内の各物理量 DTO が SI 基本単位に揃うことを
確認する。
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
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


def _series_forward_dir() -> Path:
    return input_files_dir() / "series_forward"


def _axes_forward_by_cartesian_grid_dir() -> Path:
    return input_files_dir() / "axes_forward_by_cartesian_grid"


def _make_spec(performance_curve_path: Path | None = None) -> ForwardJobSpec:
    return ForwardJobSpec(
        series_selection_path=(_series_forward_dir() / "basic01_nocable.tsv"),
        axes_path=(
            _axes_forward_by_cartesian_grid_dir() / "cartesian_grid_v1.tsv"
        ),
        performance_curve_path=performance_curve_path,
    )


def _build_dto(
    config: IConfig,
    logger: ILogger,
    performance_curve_path: Path | None = None,
):
    loaded = ForwardLoader.create(
        config=config,
        logger=logger,
    ).load(_make_spec(performance_curve_path))
    return ForwardInputDtoAssembler.create(
        config=config,
        logger=logger,
        reference_axes=_CARTESIAN_GRID_REFERENCE_AXES,
    ).assemble(loaded_data=loaded)


_META_BLOCK = (
    "im_performance_curve_name\tTest\n"
    "name\tvalue\tunit\n"
    "poles\t4\t-\n"
    "supply_frequency\t50\tHz\n"
    "supply_voltage\t200\tV\n"
    "\n"
)


class TestForwardAssemblerSiBaseUnitsCore:
    """ImDto / ArrayLayoutDto の SI 化を確認する。"""

    def test_im_series_floats_are_in_si_base_units(
        self,
        config: IConfig,
        logger: ILogger,
    ) -> None:
        dto = _build_dto(config, logger)
        series = dto.im.im_series
        assert series.nameplate_voltage.get_unit() == "V"
        assert series.nameplate_current.get_unit() == "A"
        assert series.nameplate_power.get_unit() == "W"
        assert series.nameplate_frequency.get_unit() == "Hz"
        assert series.primary_resistance.get_unit() == "Ω"
        assert series.primary_inductance.get_unit() == "H"
        assert series.excitation_resistance.get_unit() == "Ω"
        assert series.excitation_inductance.get_unit() == "H"
        for r in series.secondary_resistances.values():
            assert r.get_unit() == "Ω"
        for x in series.secondary_inductances.values():
            assert x.get_unit() == "H"

    def test_array_layout_arrays_are_in_si_base_units(
        self,
        config: IConfig,
        logger: ILogger,
    ) -> None:
        dto = _build_dto(config, logger)
        for key, arr in dto.array_layout.arrays.items():
            unit = arr.get_unit()
            assert unit != "", f"axis {key} has empty unit"
            if key == ArrayKey.FREQUENCY:
                assert unit == "Hz"
            if key == ArrayKey.INPUT_LINE_VOLTAGE:
                assert unit == "V"


class TestForwardAssemblerSiBaseUnitsPerformanceCurve:
    """SI 化が performance curve catalogs にも届くこと。

    ``torque`` 列だけがある TSV を読ませて、catalog 内の
    ``torque_series`` / ``rotational_speed_series`` などが SI 基本単位
    （Nm / rad/s 等）になっていることを確認する。
    """

    def test_torque_and_rpm_in_si_base_units(
        self,
        config: IConfig,
        logger: ILogger,
        tmp_path: Path,
    ) -> None:
        rpm_arr = np.array([1500.0, 1450.0, 1400.0], dtype=np.float64)
        torque_arr = np.array([0.0, 5.0, 10.0], dtype=np.float64)
        data_rows = "".join(
            f"{rpm}\t{tq}\n"
            for rpm, tq in zip(
                rpm_arr.tolist(),
                torque_arr.tolist(),
                strict=True,
            )
        )
        path = tmp_path / "pc_torque_only.tsv"
        path.write_text(
            _META_BLOCK + "rotational_speed\ttorque\n[rpm]\t[Nm]\n" + data_rows,
            encoding="utf-8",
        )
        dto = _build_dto(config, logger, path)
        cat = dto.im_pc_catalogs.get_all()[0]
        assert cat.supply_frequency.get_unit() == "Hz"
        assert cat.supply_voltage.get_unit() == "V"
        assert cat.torque_series is not None
        assert cat.torque_series.get_unit() == "Nm"
        assert cat.rotational_speed_series is not None
        assert cat.rotational_speed_series.get_unit() == "rad/s"
        assert cat.power_series is not None
        assert cat.power_series.get_unit() == "W"

        rpm_si = cat.rotational_speed_series.get_value()
        expected = rpm_arr * (2.0 * np.pi / 60.0)
        assert np.allclose(rpm_si, expected, rtol=0.0, atol=1e-12)

    def test_currentdependent03_fixture_tsv_passes_in_si_units(
        self,
        config: IConfig,
        logger: ILogger,
    ) -> None:
        """書き換え後の絶対単位 fixture TSV が Forward 経路を通る smoke。

        ``tests/input_files/im_performance_curve/
        currentdependent03_50Hz_115V.tsv`` は ``power=[W]`` / ``current=[A]``
        / ``torque=[N·m]`` の絶対単位で書かれている。Forward Assembler を
        通して各系列が SI 基本単位（``W`` / ``A`` / ``Nm`` / ``rad/s``）に
        揃うことだけを確認する（数値固定は機械変換の数値誤差を持ち込ま
        ないため別レイヤで担う）。
        """
        path = (
            input_files_dir()
            / "im_performance_curve"
            / "currentdependent03_50Hz_115V.tsv"
        )
        assert path.is_file(), f"fixture missing: {path}"
        dto = _build_dto(config, logger, path)
        cat = dto.im_pc_catalogs.get_all()[0]
        assert cat.power_series is not None
        assert cat.power_series.get_unit() == "W"
        assert cat.current_series is not None
        assert cat.current_series.get_unit() == "A"
        assert cat.torque_series is not None
        assert cat.torque_series.get_unit() == "Nm"
        assert cat.rotational_speed_series is not None
        assert cat.rotational_speed_series.get_unit() == "rad/s"
        assert cat.supply_frequency.get_unit() == "Hz"
        assert cat.supply_voltage.get_unit() == "V"


class TestForwardAssemblerSiUnitsValuePreservation:
    """SI 化前後で物理量としての値が保たれることのスポットチェック。

    `nameplate_power` を Hz / W 単位で確認する。元の TSV/YAML の値は
    そのままで、単位だけ SI に揃っていることを確認する。
    """

    def test_nameplate_power_value_in_watts(
        self,
        config: IConfig,
        logger: ILogger,
    ) -> None:
        dto = _build_dto(config, logger)
        power = dto.im.im_series.nameplate_power
        assert power.get_unit() == "W"
        assert power.get_value() > 0.0
        assert power.get_value() == pytest.approx(
            power.to_base_unit().get_value(),
            rel=1e-12,
        )
