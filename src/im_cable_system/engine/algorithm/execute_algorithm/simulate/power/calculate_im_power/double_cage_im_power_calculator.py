"""二重かご型IM電力計算器（im_cable_system）。"""

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
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexPowerDto,
)
from im_cable_system.engine.shared.dto.itm import (
    ItmImModelDto,
    ItmImPowerDto,
    ItmImVoltageCurrentDto,
)


class DoubleCageImPowerCalculator(IImPowerCalculator):
    """二重かご型IMの電力計算器。

    `ItmImVoltageCurrentDto` の各地点の電圧・電流から、
    二次側は枝（INNER/OUTER）ごとの dict として `ItmImPowerDto` を構築する。
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
            != ImCageMultiplicityType.DOUBLE_CAGE
        ):
            raise ValueError(
                "DoubleCageImPowerCalculator に "
                "cage_multiplicity!=DOUBLE_CAGE が渡されました: "
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

        branches = (
            ImSecondaryCageBranchType.INNER,
            ImSecondaryCageBranchType.OUTER,
        )
        secondary_base_loss_power: dict[
            ImSecondaryCageBranchType,
            ArrayComplexPowerDto,
        ] = {}
        secondary_load_power: dict[
            ImSecondaryCageBranchType,
            ArrayComplexPowerDto,
        ] = {}
        secondary_branch_total_power: dict[
            ImSecondaryCageBranchType,
            ArrayComplexPowerDto,
        ] = {}
        for branch in branches:
            base_p = three_phase_power_from_voltage_and_current_phase(
                voltage=im_voltage_current.secondary_base_voltage[branch],
                current=im_voltage_current.secondary_branch_current[branch],
            )
            load_p = three_phase_power_from_voltage_and_current_phase(
                voltage=im_voltage_current.secondary_load_voltage[branch],
                current=im_voltage_current.secondary_branch_current[branch],
            )
            secondary_base_loss_power[branch] = base_p
            secondary_load_power[branch] = load_p
            secondary_branch_total_power[branch] = add_power(
                power1=base_p, power2=load_p
            )

        # 合計（枝の和）
        secondary_base_total = add_power(
            power1=secondary_base_loss_power[ImSecondaryCageBranchType.INNER],
            power2=secondary_base_loss_power[ImSecondaryCageBranchType.OUTER],
        )
        secondary_load_total = add_power(
            power1=secondary_load_power[ImSecondaryCageBranchType.INNER],
            power2=secondary_load_power[ImSecondaryCageBranchType.OUTER],
        )

        secondary_total_power = (
            three_phase_power_from_voltage_and_current_phase(
                voltage=im_voltage_current.get_secondary_voltage(),
                current=im_voltage_current.get_secondary_total_current(),
            )
        )

        iron_loss_power = excitation_loss_power
        copper_loss_power = add_power(
            power1=primary_loss_power, power2=secondary_base_total
        )
        total_loss_power = add_power(
            power1=copper_loss_power, power2=iron_loss_power
        )

        output_power = secondary_load_total

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
