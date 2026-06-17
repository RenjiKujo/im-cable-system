"""``EstimateParamsInputDtoValidator`` の経路 E2E テスト。

EstimateParams 固有の振る舞い（``im_pc_catalogs`` が必須）と、
``common/`` 配下の検査が EP Validator からも実際に呼び出されている
ことのスモークを担保する。``common/`` 各関数の詳細な異常系は
``validate_input_dto/common/test_*`` 側で網羅する。

スモーク内訳:

* ``im_checks``: ``nameplate_voltage == 0`` で raise
* ``array_layout_checks``: 線間電圧の負実部で raise
* ``grid_size_checks``: ``reference_axes`` 直積点数の上限超過で raise
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
from im_cable_system.engine.algorithm.input_algorithm.load_data.data_class.estimate_params_input_loaded_data import (  # noqa: E501
    EstimateParamsInputLoadedData,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data.estimate_params import (
    EstimateParamsLoader,
)
from im_cable_system.engine.algorithm.input_algorithm.orchestrate.estimate_params import (
    EstimateParamsInputOrchestrator,
)
from im_cable_system.engine.algorithm.input_algorithm.validate_input_dto import (
    EstimateParamsInputDtoValidator,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ArrayKey,
    CableSectionDtos,
    CableSectionName,
    ImPerformanceCurveCatalogDtos,
)
from im_cable_system.engine.shared.dto.generic.interfaces import (
    IArrayWithUnitDto,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexVoltageDto,
    ArrayFrequencyDto,
    ArraySlipDto,
    FloatVoltageDto,
)
from im_cable_system.engine.shared.dto.input import (
    InputDto,
)
from tests.test_algorithm.test_input_algorithm._input_algorithm_helpers import (
    make_estimate_params_brief_job_spec,
)


def _build_first_dto(config: IConfig, logger: ILogger) -> InputDto:
    dtos = EstimateParamsInputOrchestrator.create(
        config=config,
        logger=logger,
    ).build_input_dto(make_estimate_params_brief_job_spec())
    return dtos.get_all()[0]


def _validator(
    config: IConfig, logger: ILogger
) -> EstimateParamsInputDtoValidator:
    return EstimateParamsInputDtoValidator.create(config=config, logger=logger)


def _cable_loaded_one_section() -> CableLoadedData:
    """1 区間ケーブルの中間表現（テスト用ダミー値）。"""
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


def _load_first_loaded(
    config: IConfig, logger: ILogger
) -> EstimateParamsInputLoadedData:
    """brief 統合 TSV から先頭の中間表現を 1 件返す。"""
    loaded = EstimateParamsLoader.create(
        config=config,
        logger=logger,
    ).load(make_estimate_params_brief_job_spec())
    return loaded[0]


def _build_cable_input_dto(config: IConfig, logger: ILogger) -> InputDto:
    """cable あり（1 区間）の :class:`InputDto` を組み立てて返す。"""
    one_loaded = dataclasses.replace(
        _load_first_loaded(config, logger),
        cable=_cable_loaded_one_section(),
    )
    return EstimateParamsAssembler.create(
        config=config,
        logger=logger,
    ).assemble(loaded_data=one_loaded)


def _replace_cable_sections(
    dto: InputDto, sections: CableSectionDtos
) -> InputDto:
    """``dto.cable`` のセクション集合だけ差し替えた新 DTO を返す。"""
    assert dto.cable is not None
    new_cable = dataclasses.replace(dto.cable, sections=sections)
    return dataclasses.replace(dto, cable=new_cable)


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


class TestEstimateParamsInputDtoValidatorHappyPath:
    """EP 経路の正常系。"""

    def test_accepts_built_input_dto(
        self,
        config: IConfig,
        logger: ILogger,
    ) -> None:
        dto = _build_first_dto(config=config, logger=logger)
        _validator(config, logger).validate(dto)


class TestEstimateParamsInputDtoValidatorOwnChecks:
    """EP 固有の検査。"""

    def test_rejects_empty_im_pc_catalogs(
        self,
        config: IConfig,
        logger: ILogger,
    ) -> None:
        dto = _build_first_dto(config=config, logger=logger)
        empty_catalogs = ImPerformanceCurveCatalogDtos(objects=[])
        invalid = dataclasses.replace(dto, im_pc_catalogs=empty_catalogs)
        with pytest.raises(ValueError, match="im_pc_catalogs"):
            _validator(config, logger).validate(invalid)


class TestEstimateParamsInputDtoValidatorCableSectionCount:
    """ケーブル（存在時）のセクション数は 1 に限る、という EP 固有契約。"""

    def test_accepts_single_section_cable(
        self,
        config: IConfig,
        logger: ILogger,
    ) -> None:
        """cable あり・1 区間なら通る。"""
        dto = _build_cable_input_dto(config=config, logger=logger)
        assert dto.cable is not None
        assert len(dto.cable.sections.get_all()) == 1
        _validator(config, logger).validate(dto)

    def test_rejects_multiple_section_cable(
        self,
        config: IConfig,
        logger: ILogger,
    ) -> None:
        """cable あり・複数区間なら raise する。"""
        dto = _build_cable_input_dto(config=config, logger=logger)
        assert dto.cable is not None
        sections = dto.cable.sections.get_all()
        extra = dataclasses.replace(
            sections[0],
            name=CableSectionName(value="SECTION_1"),
        )
        invalid = _replace_cable_sections(
            dto,
            CableSectionDtos(objects=[sections[0], extra]),
        )
        with pytest.raises(ValueError, match="セクション数"):
            _validator(config, logger).validate(invalid)

    def test_rejects_zero_section_cable(
        self,
        config: IConfig,
        logger: ILogger,
    ) -> None:
        """cable あり・0 区間なら raise する。"""
        dto = _build_cable_input_dto(config=config, logger=logger)
        invalid = _replace_cable_sections(
            dto,
            CableSectionDtos(objects=[]),
        )
        with pytest.raises(ValueError, match="セクション数"):
            _validator(config, logger).validate(invalid)


class TestEstimateParamsInputDtoValidatorWiringSmoke:
    """common/ 検査が EP Validator からも実際に呼ばれることを確認するスモーク。

    common/ 各関数の詳細な異常系は
    ``validate_input_dto/common/test_*`` 側で網羅する。
    """

    def test_invokes_im_checks(
        self,
        config: IConfig,
        logger: ILogger,
    ) -> None:
        """``common/im_checks`` の名板正値契約が走ることを確認する。"""
        dto = _build_first_dto(config=config, logger=logger)
        series_with_zero = dataclasses.replace(
            dto.im.im_series,
            nameplate_voltage=FloatVoltageDto(value=0.0, unit="V"),
        )
        im_with_zero = dataclasses.replace(dto.im, im_series=series_with_zero)
        invalid = dataclasses.replace(dto, im=im_with_zero)
        with pytest.raises(ValueError, match="nameplate_voltage"):
            _validator(config, logger).validate(invalid)

    def test_invokes_line_voltage_real_check(
        self,
        config: IConfig,
        logger: ILogger,
    ) -> None:
        """``common/array_layout_checks`` の線間電圧実数制約が走ることを確認する。"""
        dto = _build_first_dto(config=config, logger=logger)
        volt = dto.array_layout.arrays[ArrayKey.INPUT_LINE_VOLTAGE]
        bad_volt = ArrayComplexVoltageDto(
            value=np.array([-460.0 + 0.0j], dtype=np.complex128),
            unit=volt.get_unit(),
        )
        invalid = _replace_axis(dto, ArrayKey.INPUT_LINE_VOLTAGE, bad_volt)
        with pytest.raises(ValueError, match="input_line_voltage.*実部"):
            _validator(config, logger).validate(invalid)

    def test_invokes_grid_size_check(
        self,
        config: IConfig,
        logger: ILogger,
    ) -> None:
        """``common/grid_size_checks`` の上限チェックが走ることを確認する。"""
        dto = _build_first_dto(config=config, logger=logger)
        big_slip = ArraySlipDto(
            value=np.linspace(0.0, 1.0, 5000, dtype=np.float64),
            unit="-",
        )
        big_freq = ArrayFrequencyDto(
            value=np.linspace(50.0, 60.0, 100, dtype=np.float64),
            unit="Hz",
        )
        big_volt = ArrayComplexVoltageDto(
            value=np.full(100, 460.0 + 0.0j, dtype=np.complex128),
            unit="V",
        )
        invalid_layout = dataclasses.replace(
            dto.array_layout,
            arrays={
                ArrayKey.SLIP: big_slip,
                ArrayKey.FREQUENCY: big_freq,
                ArrayKey.INPUT_LINE_VOLTAGE: big_volt,
            },
            reference_axes=[
                ArrayKey.SLIP,
                ArrayKey.INPUT_LINE_VOLTAGE,
                ArrayKey.FREQUENCY,
            ],
        )
        invalid = dataclasses.replace(dto, array_layout=invalid_layout)
        with pytest.raises(
            ValueError, match="reference_axes 直積グリッド点数が上限"
        ):
            _validator(config, logger).validate(invalid)
