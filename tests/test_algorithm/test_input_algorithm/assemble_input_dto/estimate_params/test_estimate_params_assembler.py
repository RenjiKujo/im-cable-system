"""estimate_params アセンブラの単体テスト。

Loader が返す候補組み合わせ 1 件分の中間表現から、対応する
:class:`InputDto` が組み立てられることを確認する。
"""

from __future__ import annotations

import dataclasses

import numpy as np
import pytest

from im_cable_system.engine.algorithm.input_algorithm.assemble_input_dto.estimate_params import (
    EstimateParamsAssembler,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data.data_class.cable_loaded_data import (  # noqa: E501
    CableLoadedData,
    CableSectionLoadedData,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data.estimate_params import (
    EstimateParamsLoader,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ArrayKey,
)
from tests.test_algorithm.test_input_algorithm._input_algorithm_helpers import (
    make_estimate_params_brief_job_spec,
)


def _load_one(config: IConfig, logger: ILogger):
    loaded_tuple = EstimateParamsLoader.create(
        config=config,
        logger=logger,
    ).load(make_estimate_params_brief_job_spec())
    return loaded_tuple[0]


def _cable_loaded() -> CableLoadedData:
    return CableLoadedData(
        name="estimate_params_cable",
        sections=(
            CableSectionLoadedData(
                name="dummy_section",
                length=10.0,
                length_unit="m",
                shape_type="ROUND",
                conductor_resistance_per_length=1.0e-3,
                conductor_resistance_per_length_unit="Ω/m",
                conductor_inductance_per_length=1.0e-6,
                conductor_inductance_per_length_unit="H/m",
                ground_resistance_length=1.0e3,
                ground_resistance_length_unit="Ω*m",
                ground_capacitance_per_length=1.0e-10,
                ground_capacitance_per_length_unit="F/m",
            ),
        ),
        conductor_model="BASIC",
        conductor_model_params=None,
    )


def test_assembler_builds_input_dto(
    config: IConfig,
    logger: ILogger,
) -> None:
    one_loaded = _load_one(config, logger)
    dto = EstimateParamsAssembler.create(config=config, logger=logger).assemble(
        loaded_data=one_loaded,
    )
    assert dto.name.get_value() == one_loaded.im_cable_system_name
    assert dto.im is not None
    assert dto.cable is None
    assert dto.im_pc_catalogs is not None


def test_assembler_uses_estimate_params_reference_axes(
    config: IConfig,
    logger: ILogger,
) -> None:
    """EstimateParams 固定の参照軸順序を確認する。"""
    one_loaded = _load_one(config, logger)
    dto = EstimateParamsAssembler.create(config=config, logger=logger).assemble(
        loaded_data=one_loaded,
    )
    assert dto.array_layout.reference_axes == [
        ArrayKey.SLIP,
        ArrayKey.FREQUENCY,
        ArrayKey.INPUT_LINE_VOLTAGE,
    ]


def test_assembler_sets_cable_conductor_model(
    config: IConfig,
    logger: ILogger,
) -> None:
    """cable がある場合は CableDto に導体モデルが組み込まれる。"""
    one_loaded = dataclasses.replace(
        _load_one(config, logger), cable=_cable_loaded()
    )
    dto = EstimateParamsAssembler.create(config=config, logger=logger).assemble(
        loaded_data=one_loaded,
    )
    assert dto.cable is not None
    assert dto.cable.conductor_model.get_name() == "BASIC"


def test_assembler_rejects_empty_secondary_branch(
    config: IConfig,
    logger: ILogger,
) -> None:
    """二次枝が空の候補は InputDto に組み立てられない。"""
    one_loaded = _load_one(config, logger)
    broken_im = dataclasses.replace(
        one_loaded.im,
        secondary=None,
        secondary_inner=None,
        secondary_outer=None,
    )
    broken_loaded = dataclasses.replace(one_loaded, im=broken_im)
    with pytest.raises(ValueError):
        EstimateParamsAssembler.create(config=config, logger=logger).assemble(
            loaded_data=broken_loaded,
        )


def test_assembler_propagates_nan_to_mask(
    config: IConfig,
    logger: ILogger,
) -> None:
    """LoadedData の観測列に NaN を仕込むと、組み立て後の Catalog DTO
    で対応する ``*_series_mask`` が立つ。

    EstimateParams アセンブラが共通性能曲線ビルダーを直接呼ぶ経路でも、
    NaN→0+mask 抽出が機能することを確認する。
    """
    one_loaded = _load_one(config, logger)
    pc = one_loaded.im_performance_curve
    assert pc is not None
    assert pc.power is not None
    # 0 番目の power セルを NaN に上書きする
    new_power = pc.power.copy()
    new_power[0] = np.nan
    new_pc = dataclasses.replace(pc, power=new_power)
    new_loaded = dataclasses.replace(one_loaded, im_performance_curve=new_pc)

    dto = EstimateParamsAssembler.create(config=config, logger=logger).assemble(
        loaded_data=new_loaded,
    )
    cat = dto.im_pc_catalogs.get_all()[0]
    assert cat.power_series is not None
    assert cat.power_series_mask is not None
    assert cat.power_series_mask[0] is np.bool_(False)
    assert cat.power_series_mask[1:].all()
    # value は placeholder 0
    power_w = cat.power_series.to_base_unit().get_value()
    assert power_w[0] == 0.0
    assert np.isfinite(power_w).all()


def test_assembler_converts_ratio_power_to_absolute_w(
    config: IConfig,
    logger: ILogger,
) -> None:
    """``power[-]`` 入力が Assembler を通すと ``power[W]`` に変換される。

    brief TSV は ``power_unit='[-]'`` で書かれており、名盤 ``output_power``
    は 3711 W。assembler を通した Catalog DTO の ``power_series`` が
    SI 単位 ``W`` に揃い、各値は ``ratio × 3711`` の関係で復元できる
    ことを 1 点固定する。
    """
    one_loaded = _load_one(config, logger)
    pc = one_loaded.im_performance_curve
    assert pc is not None
    assert pc.power is not None
    # brief TSV 上で power 列は比率（[-]）であることを前提にする
    assert pc.power_unit is not None
    assert pc.power_unit.strip().strip("[").strip("]") == "-"
    nameplate_power_w = float(one_loaded.im.nameplate.power)
    expected_w = pc.power * nameplate_power_w

    dto = EstimateParamsAssembler.create(config=config, logger=logger).assemble(
        loaded_data=one_loaded,
    )
    cat = dto.im_pc_catalogs.get_all()[0]
    assert cat.power_series is not None
    assert cat.power_series.get_unit() == "W"
    actual_w = cat.power_series.to_base_unit().get_value()
    np.testing.assert_allclose(actual_w, expected_w, rtol=1e-12)


def test_assembler_converts_ratio_current_percent_to_absolute_a(
    config: IConfig,
    logger: ILogger,
) -> None:
    """``current[%]`` 入力が Assembler を通すと ``current[A]`` に変換される。

    brief TSV は ``current_unit='[%]'`` で書かれており、名盤 ``input_line_current``
    は 25 A。assembler を通した Catalog DTO の ``current_series`` が
    SI 単位 ``A`` に揃い、各値は ``percent × 25 / 100`` の関係で復元
    できることを 1 点固定する。
    """
    one_loaded = _load_one(config, logger)
    pc = one_loaded.im_performance_curve
    assert pc is not None
    assert pc.current is not None
    assert pc.current_unit is not None
    assert pc.current_unit.strip().strip("[").strip("]") == "%"
    nameplate_current_a = float(one_loaded.im.nameplate.current)
    expected_a = pc.current * nameplate_current_a / 100.0

    dto = EstimateParamsAssembler.create(config=config, logger=logger).assemble(
        loaded_data=one_loaded,
    )
    cat = dto.im_pc_catalogs.get_all()[0]
    assert cat.current_series is not None
    assert cat.current_series.get_unit() == "A"
    actual_a = cat.current_series.to_base_unit().get_value()
    np.testing.assert_allclose(actual_a, expected_a, rtol=1e-12)
