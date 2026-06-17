"""電力計算オーケストレーターのテスト（二重かご / Double cage）。

このモジュールは、`input_double_im_cable_system_data` が生成する二重かご向け入力DTOを用いて
`PowerCalculationOrchestrator` が例外なく `ItmPowerDto` を生成できることと、
二次側電力が枝（INNER/OUTER）dictとして構築されることを検証します。
"""

from __future__ import annotations

import numpy as np
import pytest

from im_cable_system.engine.algorithm.execute_algorithm.build_model.orchestrate import (  # noqa: E501
    ImCableModelBuildOrchestrator,
)
from im_cable_system.engine.algorithm.execute_algorithm.simulate.power import (  # noqa: E501
    IPowerCalculationOrchestrator,
    PowerCalculationOrchestrator,
)
from im_cable_system.engine.algorithm.execute_algorithm.simulate.voltage_current.orchestrate import (  # noqa: E501
    VoltageCurrentCalculationOrchestrator,
)
from im_cable_system.engine.domain.physics.electrical import (
    add_power,
)
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ImCageMultiplicityType,
    ImSecondaryCageBranchType,
    expected_branch_keys_for_cage_multiplicity,
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


class TestDoubleCagePowerCalculationOrchestrator:
    """二重かご（Double cage）向け PowerCalculationOrchestrator のテスト。"""

    def test_create_orchestrator(self, config, logger) -> None:
        """オーケストレーターの生成を確認する。"""
        orchestrator = PowerCalculationOrchestrator.create(
            config=config, logger=logger
        )
        assert orchestrator is not None
        assert isinstance(orchestrator, IPowerCalculationOrchestrator)

    def test_calculate_creates_branch_power_dicts_for_double_cage(
        self,
        config,
        logger,
        double_cage_im_series_dtos,  # noqa: ARG002
        double_cage_input_im_cable_system_dtos,
        build_model_orchestrator,
    ) -> None:
        """二重かご入力で二次側電力dict（INNER/OUTER）が構築されることを確認する。"""
        vc_orchestrator = VoltageCurrentCalculationOrchestrator.create(
            config=config, logger=logger
        )
        power_orchestrator = PowerCalculationOrchestrator.create(
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

            expected_shape = model_dto.array_layout.shape
            assert (
                power_dto.im_power.cage_multiplicity
                == ImCageMultiplicityType.DOUBLE_CAGE
            )

            expected_keys = expected_branch_keys_for_cage_multiplicity(
                ImCageMultiplicityType.DOUBLE_CAGE
            )
            assert (
                frozenset(power_dto.im_power.secondary_base_loss_power.keys())
                == expected_keys
            )
            assert (
                frozenset(power_dto.im_power.secondary_load_power.keys())
                == expected_keys
            )
            assert (
                frozenset(
                    power_dto.im_power.secondary_branch_total_power.keys()
                )
                == expected_keys
            )

            for branch in (
                ImSecondaryCageBranchType.INNER,
                ImSecondaryCageBranchType.OUTER,
            ):
                assert (
                    power_dto.im_power.secondary_base_loss_power[
                        branch
                    ].value.shape
                    == expected_shape
                )
                assert (
                    power_dto.im_power.secondary_load_power[branch].value.shape
                    == expected_shape
                )

    def test_double_cage_power_definitions(
        self,
        config,
        logger,
        double_cage_im_series_dtos,  # noqa: ARG002
        double_cage_input_im_cable_system_dtos,
        build_model_orchestrator,
    ) -> None:
        """二重かごで電力DTOが定義式・損失合算・有限値を満たすことを確認する。

        - NaN/Inf を含まないこと
        - output_power == sum(secondary_load_power)（INNER+OUTER）
        - copper_loss_power == primary_loss_power + sum(secondary_base_loss_power)
        - total_loss_power == copper_loss_power + iron_loss_power
        - iron_loss_power == excitation_loss_power
        """
        rtol = 1e-10
        atol = 1e-12

        vc_orchestrator = VoltageCurrentCalculationOrchestrator.create(
            config=config, logger=logger
        )
        power_orchestrator = PowerCalculationOrchestrator.create(
            config=config, logger=logger
        )

        for input_dto in double_cage_input_im_cable_system_dtos[:3]:
            model_dto = _build_model_dto(
                input_dto=input_dto,
                build_model_orchestrator=build_model_orchestrator,
            )
            vc_dto = vc_orchestrator.calculate(model_dto=model_dto)
            power_dto = power_orchestrator.calculate(
                model_dto=model_dto,
                voltage_current_dto=vc_dto,
            )

            system_name = input_dto.name.get_value()
            im_power = power_dto.im_power

            # ---- finite checks ----
            for name, power in (
                ("input_power", im_power.input_power),
                ("total_loss_power", im_power.total_loss_power),
                ("copper_loss_power", im_power.copper_loss_power),
                ("output_power", im_power.output_power),
            ):
                assert np.isfinite(power.value).all(), (
                    f"{system_name}:{name} に NaN/Inf が含まれます"
                )

            # ---- output_power == sum(secondary_load_power) ----
            expected_output = None
            for power in im_power.secondary_load_power.values():
                expected_output = (
                    power
                    if expected_output is None
                    else add_power(power1=expected_output, power2=power)
                )
            assert expected_output is not None, system_name
            np.testing.assert_allclose(
                im_power.output_power.value,
                expected_output.value,
                rtol=rtol,
                atol=atol,
                err_msg=system_name,
            )

            # ---- copper_loss == primary_loss + sum(secondary_base_loss) ----
            secondary_base_total = None
            for power in im_power.secondary_base_loss_power.values():
                secondary_base_total = (
                    power
                    if secondary_base_total is None
                    else add_power(power1=secondary_base_total, power2=power)
                )
            assert secondary_base_total is not None, system_name
            expected_copper_loss = add_power(
                power1=im_power.primary_loss_power,
                power2=secondary_base_total,
            )
            np.testing.assert_allclose(
                im_power.copper_loss_power.value,
                expected_copper_loss.value,
                rtol=rtol,
                atol=atol,
                err_msg=system_name,
            )

            # ---- iron_loss == excitation_loss ----
            np.testing.assert_allclose(
                im_power.iron_loss_power.value,
                im_power.excitation_loss_power.value,
                rtol=rtol,
                atol=atol,
                err_msg=system_name,
            )

            # ---- total_loss == copper_loss + iron_loss ----
            expected_total_loss = add_power(
                power1=im_power.copper_loss_power,
                power2=im_power.iron_loss_power,
            )
            np.testing.assert_allclose(
                im_power.total_loss_power.value,
                expected_total_loss.value,
                rtol=rtol,
                atol=atol,
                err_msg=system_name,
            )

            # ---- energy conservation: input == total_loss + output ----
            # VI（ノード則・電圧降下）と電力計算が整合していれば、IM入力電力は
            # 全損失と出力の複素和に厳密一致する（回路条件に依存しない不変条件）。
            expected_input_power = add_power(
                power1=im_power.total_loss_power,
                power2=im_power.output_power,
            )
            np.testing.assert_allclose(
                im_power.input_power.value,
                expected_input_power.value,
                rtol=rtol,
                atol=atol,
                err_msg=system_name,
            )
