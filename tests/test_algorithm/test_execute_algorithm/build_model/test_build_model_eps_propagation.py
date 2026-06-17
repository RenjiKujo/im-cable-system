"""build_model が config.numerical_guard_config.eps をドメインへ伝播することの検証。"""

from __future__ import annotations

import copy
from pathlib import Path

import numpy as np
import pytest
import yaml

import im_cable_system.engine.shared.config.app_config as app_config_module
from im_cable_system.engine.algorithm.execute_algorithm.build_model.build_cable_model import (  # noqa: E501
    PieCableModelBuilder,
)
from im_cable_system.engine.algorithm.execute_algorithm.build_model.build_im_model import (  # noqa: E501
    SingleCageImModelBuilder,
)
from im_cable_system.engine.algorithm.execute_algorithm.build_model.build_system_model import (  # noqa: E501
    ImPieCableSystemModelBuilder,
)
from im_cable_system.engine.shared.config import (
    Config,
    IConfig,
    ILogger,
    Logger,
)
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    PieCableConductorKey,
)
from im_cable_system.engine.shared.dto.input import InputDto, InputDtos
from tests.test_algorithm.test_execute_algorithm.fixtures.textbook_single_cage import (  # noqa: E501
    find_textbook_no_cable_input,
)

_CUSTOM_EPS = 1e-3


def _default_config_yaml_path() -> Path:
    return Path(app_config_module.__file__).resolve().parent / "config.yaml"


@pytest.fixture
def config_custom_eps(tmp_path: Path) -> IConfig:
    """numerical_guard.eps を非デフォルトにした Config。"""
    base_path = _default_config_yaml_path()
    with base_path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        msg = "config.yaml のルートはマッピングである必要があります。"
        raise TypeError(msg)
    data = copy.deepcopy(data)
    execute_block = data.setdefault("calculation", {}).setdefault("execute", {})
    numerical_guard = execute_block.setdefault("numerical_guard", {})
    numerical_guard["eps"] = _CUSTOM_EPS
    out_path = tmp_path / "config_custom_eps.yaml"
    with out_path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(data, handle, allow_unicode=True, sort_keys=False)
    return Config.create(config_file_path=out_path)


@pytest.fixture
def logger_custom_eps(config_custom_eps: IConfig) -> ILogger:
    return Logger.create(config_custom_eps)


class TestBuildModelEpsPropagation:
    """algorithm 層で config.eps がクランプに反映されること。"""

    def test_pie_cable_builder_ideal_conductor_uses_config_eps(
        self,
        config_custom_eps: IConfig,
        logger_custom_eps: ILogger,
        single_cage_input_im_cable_system_dtos: InputDtos,
    ) -> None:
        """ケーブルなし（理想導体）時、導体インピーダンスが config.eps にクランプされる。"""
        input_dto = find_textbook_no_cable_input(
            single_cage_input_im_cable_system_dtos
        )
        builder = PieCableModelBuilder.create(
            config=config_custom_eps,
            logger=logger_custom_eps,
        )
        itm_cable = builder.build(
            cable_dto=input_dto.cable,
            model_array_layout=input_dto.array_layout,
        )
        conductor_z = itm_cable.cable_immittance.conductor_impedance[
            PieCableConductorKey.SINGLE
        ]
        assert np.all(
            np.abs(conductor_z.value - _CUSTOM_EPS) < _CUSTOM_EPS * 1e-6 + 1e-15
        )

    def test_system_builder_ideal_cable_matches_im_with_custom_eps(
        self,
        config_custom_eps: Config,
        logger_custom_eps: ILogger,
        single_cage_input_im_cable_system_dtos: InputDtos,
    ) -> None:
        """理想ケーブル経路でもシステム位相インピーダンスが IM と一致する。"""
        input_dto: InputDto = find_textbook_no_cable_input(
            single_cage_input_im_cable_system_dtos
        )
        array_layout = input_dto.array_layout
        im_builder = SingleCageImModelBuilder.create(
            config=config_custom_eps,
            logger=logger_custom_eps,
        )
        cable_builder = PieCableModelBuilder.create(
            config=config_custom_eps,
            logger=logger_custom_eps,
        )
        system_builder = ImPieCableSystemModelBuilder.create(
            config=config_custom_eps,
            logger=logger_custom_eps,
        )
        itm_im = im_builder.build(
            im_dto=input_dto.im,
            model_array_layout=array_layout,
        )
        itm_cable = cable_builder.build(
            cable_dto=input_dto.cable,
            model_array_layout=array_layout,
        )
        itm_system = system_builder.build(
            itm_im_model_dto=itm_im,
            itm_cable_model_dto=itm_cable,
        )
        assert config_custom_eps.numerical_guard_config.eps == pytest.approx(
            _CUSTOM_EPS
        )
        np.testing.assert_allclose(
            itm_system.system_phase_impedance.get_value(),
            itm_im.total_model.impedance.get_value(),
            rtol=1e-10,
            atol=_CUSTOM_EPS * 1e-6,
        )
