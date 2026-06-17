"""``OutputSimulationResultDto`` の生量保持テスト。"""

from __future__ import annotations

import numpy as np

from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexCurrentDto,
    ArrayComplexPowerDto,
    ArrayEfficiencyDto,
    ArrayRotationalSpeedDto,
    ArrayTorqueDto,
)
from im_cable_system.engine.shared.dto.output import (
    OutputSimulationResultDto,
)


def _make_result() -> OutputSimulationResultDto:
    return OutputSimulationResultDto(
        output_power=ArrayComplexPowerDto(
            value=np.array([1000.0 + 0j, 900.0 + 0j]),
            unit="VA",
        ),
        cable_input_phase_power=ArrayComplexPowerDto(
            value=np.array([1100.0 + 100j, 1000.0 + 80j]),
            unit="VA",
        ),
        input_line_current=ArrayComplexCurrentDto(
            value=np.array([10.0 + 1j, 9.0 + 0.5j]),
            unit="A",
        ),
        system_efficiency=ArrayEfficiencyDto(
            value=np.array([0.9, 0.91]),
            unit="-",
        ),
        torque=ArrayTorqueDto(
            value=np.array([5.0, 4.5]),
            unit="Nm",
        ),
        rotational_speed=ArrayRotationalSpeedDto(
            value=np.array([150.0, 148.0]),
            unit="rad/s",
        ),
    )


class TestOutputSimulationResultDto:
    def test_holds_quantities(self) -> None:
        result = _make_result()
        np.testing.assert_allclose(
            result.output_power.get_value().real,
            [1000.0, 900.0],
        )
        np.testing.assert_allclose(
            result.system_efficiency.get_value(),
            [0.9, 0.91],
        )
        assert result.torque.get_unit() == "Nm"
        assert result.rotational_speed.get_unit() == "rad/s"
        np.testing.assert_allclose(
            np.abs(result.input_line_current.get_value()),
            np.abs(np.array([10.0 + 1j, 9.0 + 0.5j])),
        )
