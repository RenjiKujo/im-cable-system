"""単一かご型IM電力計算器（im_cable_system）。"""

from __future__ import annotations

from im_cable_system.engine.algorithm.execute_algorithm.simulate.power.calculate_im_power.i_im_power_calculator import (  # noqa: E501
    IImPowerCalculator,
)
from im_cable_system.engine.domain.physics.electrical import (
    add_power,
    three_phase_power_from_voltage_and_current_phase,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ImCageMultiplicityType,
    ImSecondaryCageBranchType,
)
from im_cable_system.engine.shared.dto.itm import (
    ItmImModelDto,
    ItmImPowerDto,
    ItmImVoltageCurrentDto,
)


class SingleCageImPowerCalculator(IImPowerCalculator):
    """単一かご型IMの電力計算器。

    `ItmImVoltageCurrentDto` の各地点の電圧・電流から、
    `ItmImPowerDto` を構築する。
    """

    def __init__(self, config: IConfig, logger: ILogger) -> None:
        self._config: IConfig = config
        self._logger: ILogger = logger

    @classmethod
    def create(cls, config: IConfig, logger: ILogger) -> IImPowerCalculator:
        return cls(config=config, logger=logger)

    def calculate(
        self,
        im_model: ItmImModelDto,  # noqa: ARG002
        im_voltage_current: ItmImVoltageCurrentDto,
    ) -> ItmImPowerDto:
        if (
            im_voltage_current.cage_multiplicity
            != ImCageMultiplicityType.SINGLE_CAGE
        ):
            raise ValueError(
                "SingleCageImPowerCalculator に "
                "cage_multiplicity!=SINGLE_CAGE が渡されました: "
                f"{im_voltage_current.cage_multiplicity!s}"
            )

        input_power = three_phase_power_from_voltage_and_current_phase(
            voltage=im_voltage_current.im_input_voltage,
            current=im_voltage_current.im_input_current,
        )
        primary_loss_power = three_phase_power_from_voltage_and_current_phase(
            voltage=im_voltage_current.im_primary_voltage,
            current=im_voltage_current.im_primary_current,
        )
        excitation_loss_power = (
            three_phase_power_from_voltage_and_current_phase(
                voltage=im_voltage_current.im_excitation_voltage,
                current=im_voltage_current.im_excitation_current,
            )
        )

        branch = ImSecondaryCageBranchType.SINGLE
        secondary_base_loss_power = {
            branch: three_phase_power_from_voltage_and_current_phase(
                voltage=im_voltage_current.secondary_base_voltage[branch],
                current=im_voltage_current.secondary_branch_current[branch],
            )
        }
        secondary_load_power = {
            branch: three_phase_power_from_voltage_and_current_phase(
                voltage=im_voltage_current.secondary_load_voltage[branch],
                current=im_voltage_current.secondary_branch_current[branch],
            )
        }
        secondary_branch_total_power = {
            branch: add_power(
                power1=secondary_base_loss_power[branch],
                power2=secondary_load_power[branch],
            )
        }

        secondary_total_power = (
            three_phase_power_from_voltage_and_current_phase(
                voltage=im_voltage_current.get_secondary_voltage(),
                current=im_voltage_current.get_secondary_total_current(),
            )
        )

        iron_loss_power = excitation_loss_power
        copper_loss_power = add_power(
            power1=primary_loss_power,
            power2=secondary_base_loss_power[branch],
        )
        total_loss_power = add_power(
            power1=copper_loss_power, power2=iron_loss_power
        )

        output_power = secondary_load_power[branch]

        return ItmImPowerDto(
            input_power=input_power,
            primary_loss_power=primary_loss_power,
            excitation_loss_power=excitation_loss_power,
            cage_multiplicity=im_voltage_current.cage_multiplicity,
            secondary_base_loss_power=secondary_base_loss_power,
            secondary_load_power=secondary_load_power,
            secondary_branch_total_power=secondary_branch_total_power,
            secondary_total_power=secondary_total_power,
            output_power=output_power,
            total_loss_power=total_loss_power,
            copper_loss_power=copper_loss_power,
            iron_loss_power=iron_loss_power,
        )
