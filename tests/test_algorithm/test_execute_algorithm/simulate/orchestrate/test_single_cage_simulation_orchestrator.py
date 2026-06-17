"""Simulation実行全体オーケストレーター（im_cable_system）のテスト。"""

from __future__ import annotations

import pytest

from im_cable_system.engine.algorithm.execute_algorithm.build_model.orchestrate import (  # noqa: E501
    ImCableModelBuildOrchestrator,
)
from im_cable_system.engine.algorithm.execute_algorithm.simulate import (  # noqa: E501
    ISimulationOrchestrator,
)
from im_cable_system.engine.algorithm.execute_algorithm.simulate.orchestrate import (  # noqa: E501
    SimulationOrchestrator,
    take_simulation_numerical_stability_report,
)
from tests.test_algorithm.test_execute_algorithm.fixtures.input_single_im_cable_system_data import (  # noqa: E501
    make_cable_series_dtos,
    make_input_im_cable_system_dtos,
    make_single_cage_im_series_dtos,
)


@pytest.fixture
def im_series_dtos():
    """テスト用のImSeriesDtos fixture."""
    return make_single_cage_im_series_dtos()


@pytest.fixture
def cable_series_dtos():
    """テスト用のCableSeriesDtos fixture."""
    return make_cable_series_dtos()


@pytest.fixture
def input_im_cable_system_dtos():
    """テスト用のInputDtos fixture."""
    return make_input_im_cable_system_dtos().get_all()


def _build_model_dto(
    *,
    input_dto,
    build_model_orchestrator: ImCableModelBuildOrchestrator,
):
    """入力DTOからモデルDTOを構築するヘルパー関数。"""
    return build_model_orchestrator.build(input_dto)


class TestSingleCageSimulationOrchestrator:
    """単一かご（Single cage）向け SimulationOrchestrator のテスト。"""

    def test_create_orchestrator(self, config, logger) -> None:
        orchestrator = SimulationOrchestrator.create(
            config=config, logger=logger
        )
        assert orchestrator is not None
        assert isinstance(orchestrator, ISimulationOrchestrator)

    def test_calculate_creates_correct_simulation_dto(
        self,
        config,
        logger,
        input_im_cable_system_dtos,
        build_model_orchestrator: ImCableModelBuildOrchestrator,
    ) -> None:
        input_dto = input_im_cable_system_dtos[0]
        model_dto = _build_model_dto(
            input_dto=input_dto,
            build_model_orchestrator=build_model_orchestrator,
        )

        orchestrator = SimulationOrchestrator.create(
            config=config, logger=logger
        )
        simulation_dto = orchestrator.calculate(model_dto=model_dto)
        _ = take_simulation_numerical_stability_report()

        expected_shape = model_dto.array_layout.shape
        assert simulation_dto.power is not None
        assert simulation_dto.characteristic is not None

        assert (
            simulation_dto.voltage_current.cable_voltage_current.input_line_voltage.get_value().shape
            == expected_shape
        )
        assert (
            simulation_dto.power.im_power.output_power.get_value().shape
            == expected_shape
        )
        assert (
            simulation_dto.characteristic.rotational_speed.rotational_speed.get_value().shape
            == expected_shape
        )
        assert (
            simulation_dto.characteristic.torque.torque.get_value().shape
            == expected_shape
        )
        assert (
            simulation_dto.characteristic.efficiency.system_efficiency.get_value().shape
            == expected_shape
        )
