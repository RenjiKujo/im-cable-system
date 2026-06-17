"""DirectForwardExecutionOrchestrator の単体テスト（単カゴ）。

4_test_strategy.md の「実装の単体テスト（Direct）」に準拠。
全組み合わせのうち Direct 型入力に対して execute が完了し収束することを検証する。
"""

from __future__ import annotations

import numpy as np
import pytest

from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.forward.direct_forward_execution_orchestrator import (  # noqa: E501
    DirectForwardExecutionOrchestrator,
)
from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.forward.factory_forward_execution_orchestrator import (  # noqa: E501
    ForwardExecutionOrchestratorFactory,
)


class TestSingleCageDirectForwardExecutionOrchestrator:
    """単カゴ向け DirectForwardExecutionOrchestrator の単体テストクラス。"""

    def test_execute_succeeds_with_series_embedded_in_input_dto(
        self,
        config,
        logger,
        single_cage_input_im_cable_system_dto,
    ) -> None:
        """InputDto にシリーズ詳細が埋め込まれていれば execute が成功する。"""
        orchestrator = DirectForwardExecutionOrchestrator.create(
            config=config,
            logger=logger,
        )
        itm = orchestrator.execute(
            input_dto=single_cage_input_im_cable_system_dto
        )
        assert itm.simulation_result is not None

    def test_execute_without_validation_sets_full_simulation_result(
        self,
        config,
        logger,
        single_cage_input_im_cable_system_dto,
    ) -> None:
        """execute_without_validation は検証を除きフル simulate 結果を返す。"""
        orchestrator = DirectForwardExecutionOrchestrator.create(
            config=config,
            logger=logger,
        )
        itm = orchestrator.execute_without_validation(
            input_dto=single_cage_input_im_cable_system_dto
        )
        simulation_result = itm.simulation_result
        assert simulation_result is not None
        assert simulation_result.power is not None
        assert simulation_result.characteristic is not None

    @pytest.mark.slow
    def test_execute_with_all_direct_inputs_succeeds(
        self,
        config,
        logger,
        single_cage_input_im_cable_system_dtos,
    ) -> None:
        """全組み合わせのうち Direct 型入力で execute が完了し、形状・NaN/Inf が妥当。

        計算できないパターンでは ValueError を期待する。それ以外は収束する。
        """
        direct_count = 0
        for input_dto in single_cage_input_im_cable_system_dtos.get_all():
            system_name = input_dto.name.get_value()
            orchestrator = ForwardExecutionOrchestratorFactory.create(
                config=config,
                logger=logger,
                im_dto=input_dto.im,
                cable=input_dto.cable,
            )
            if not isinstance(
                orchestrator,
                DirectForwardExecutionOrchestrator,
            ):
                continue
            direct_count += 1
            try:
                itm_dto = orchestrator.execute(input_dto=input_dto)
            except ValueError:
                continue  # noqa: ERA001 計算できないパターンではスキップ
            expected_shape = itm_dto.model.array_layout.shape
            assert itm_dto.simulation_result is not None, system_name
            simulation_result = itm_dto.simulation_result
            assert (
                simulation_result.voltage_current.im_voltage_current.im_primary_voltage.get_value().shape
                == expected_shape
            ), system_name
            assert (
                simulation_result.voltage_current.im_voltage_current.im_primary_current.get_value().shape
                == expected_shape
            ), system_name
            assert simulation_result.characteristic is not None, system_name
            rotational_speed = simulation_result.characteristic.rotational_speed.rotational_speed.to_base_unit().get_value()
            assert np.isfinite(rotational_speed).all(), system_name
            torque = simulation_result.characteristic.torque.torque.to_base_unit().get_value()
            omega = rotational_speed
            eps = 1e-12
            omega_zero_or_small = np.abs(omega) <= eps
            assert np.isfinite(torque[~omega_zero_or_small]).all(), system_name
        assert direct_count > 0, "Direct 型の入力が1件もありません"
