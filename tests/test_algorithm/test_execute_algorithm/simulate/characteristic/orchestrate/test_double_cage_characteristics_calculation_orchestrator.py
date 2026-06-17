"""特性値計算オーケストレーターのテスト（二重かご / Double cage）。

`input_double_im_cable_system_data` が生成する二重かご向け入力DTOを用いて
`CharacteristicsCalculationOrchestrator` の最小限の動作を検証する。

検証フローは build_model → voltage_current → power → characteristic とし、
`ItmCharacteristicDto` の各配列形状がモデル布局と一致すること、および
効率・回転速度の有限性とトルクの角速度ゼロ近傍での NaN 挙動を確認する。
"""

from __future__ import annotations

import numpy as np
import pytest

from im_cable_system.engine.algorithm.execute_algorithm.build_model.orchestrate import (  # noqa: E501
    ImCableModelBuildOrchestrator,
)
from im_cable_system.engine.algorithm.execute_algorithm.simulate.characteristic import (  # noqa: E501
    ICharacteristicsCalculationOrchestrator,
)
from im_cable_system.engine.algorithm.execute_algorithm.simulate.characteristic.orchestrate import (  # noqa: E501
    CharacteristicsCalculationOrchestrator,
)
from im_cable_system.engine.algorithm.execute_algorithm.simulate.power.orchestrate import (  # noqa: E501
    PowerCalculationOrchestrator,
)
from im_cable_system.engine.algorithm.execute_algorithm.simulate.voltage_current.orchestrate import (  # noqa: E501
    VoltageCurrentCalculationOrchestrator,
)
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ImCageMultiplicityType,
)
from tests.test_algorithm.test_execute_algorithm.fixtures.input_double_im_cable_system_data import (  # noqa: E501
    make_double_cage_im_series_dtos,
    make_input_im_cable_system_dtos,
)


@pytest.fixture
def double_cage_im_series_dtos():
    """テスト用の二重かご ImSeriesDtos fixture."""
    return make_double_cage_im_series_dtos()


@pytest.fixture
def double_cage_input_im_cable_system_dtos():
    """テスト用の二重かご InputDtos fixture."""
    return make_input_im_cable_system_dtos().get_all()


def _build_model_dto(
    *,
    input_dto,
    build_model_orchestrator: ImCableModelBuildOrchestrator,
):
    """入力DTOからモデルDTOを構築するヘルパー関数。"""
    return build_model_orchestrator.build(input_dto)


class TestDoubleCageCharacteristicsCalculationOrchestrator:
    """二重かご（Double cage）向け CharacteristicsCalculationOrchestrator のテスト。"""

    def test_create_orchestrator(self, config, logger) -> None:
        """オーケストレーターの生成を確認する。"""
        orchestrator = CharacteristicsCalculationOrchestrator.create(
            config=config, logger=logger
        )
        assert orchestrator is not None
        assert isinstance(orchestrator, ICharacteristicsCalculationOrchestrator)

    def test_calculate_produces_characteristic_dto_for_double_cage(
        self,
        config,
        logger,
        double_cage_im_series_dtos,  # noqa: ARG002
        double_cage_input_im_cable_system_dtos,
        build_model_orchestrator,
    ) -> None:
        """二重かご入力で特性値DTOが生成され、形状・有限性が整合すること。"""
        eps = 1e-12

        vc_orchestrator = VoltageCurrentCalculationOrchestrator.create(
            config=config, logger=logger
        )
        power_orchestrator = PowerCalculationOrchestrator.create(
            config=config, logger=logger
        )
        char_orchestrator = CharacteristicsCalculationOrchestrator.create(
            config=config, logger=logger
        )

        for input_dto in double_cage_input_im_cable_system_dtos[:3]:
            model_dto = _build_model_dto(
                input_dto=input_dto,
                build_model_orchestrator=build_model_orchestrator,
            )
            assert (
                model_dto.im.secondary_model.cage_multiplicity
                == ImCageMultiplicityType.DOUBLE_CAGE
            )

            vc_dto = vc_orchestrator.calculate(model_dto=model_dto)

            power_dto = power_orchestrator.calculate(
                model_dto=model_dto,
                voltage_current_dto=vc_dto,
            )

            characteristic_dto = char_orchestrator.calculate(
                model_dto=model_dto,
                power_dto=power_dto,
            )

            expected_shape = model_dto.array_layout.shape
            system_name = input_dto.name.get_value()

            rotational_speed = characteristic_dto.rotational_speed.rotational_speed.to_base_unit().get_value()
            torque = characteristic_dto.torque.torque.to_base_unit().get_value()

            assert rotational_speed.shape == expected_shape, system_name
            assert torque.shape == expected_shape, system_name
            assert (
                characteristic_dto.efficiency.system_efficiency.get_value().shape
                == expected_shape
            ), system_name
            assert (
                characteristic_dto.efficiency.im_efficiency.get_value().shape
                == expected_shape
            ), system_name
            assert (
                characteristic_dto.efficiency.cable_efficiency.get_value().shape
                == expected_shape
            ), system_name

            assert np.isfinite(rotational_speed).all(), system_name

            omega_zero_or_small = np.abs(rotational_speed) <= eps
            assert np.isnan(torque[omega_zero_or_small]).all(), system_name
            assert np.isfinite(torque[~omega_zero_or_small]).all(), system_name

            assert np.isfinite(
                characteristic_dto.efficiency.system_efficiency.get_value()
            ).all(), system_name
            assert np.isfinite(
                characteristic_dto.efficiency.im_efficiency.get_value()
            ).all(), system_name
            assert np.isfinite(
                characteristic_dto.efficiency.cable_efficiency.get_value()
            ).all(), system_name
