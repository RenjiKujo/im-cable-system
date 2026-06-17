"""IterationForwardExecutionOrchestrator の単体テスト（二重かご）。

input_double_im_cable_system_data 由来の InputDto を用いる。
4_test_strategy.md の「実装の単体テスト（Iteration）」に準拠。
conftest 経由で config_test_orchestrator.yaml を読み込み、本番 config.yaml と
項目を揃えたテスト用設定を使用する。
電流イテレーション（電流依存イミタンス）で収束しない場合、
current_estimation.convergence_failure_severity: "WARNING" のため例外は送出されず
警告ログで継続し execute が ItmDto を返して完了する。その挙動を確認する。
"""

from __future__ import annotations

import numpy as np
import pytest

from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.forward.factory_forward_execution_orchestrator import (  # noqa: E501
    ForwardExecutionOrchestratorFactory,
)
from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.forward.iteration_forward_execution_orchestrator import (  # noqa: E501
    IterationForwardExecutionOrchestrator,
)


class TestDoubleCageIterationForwardExecutionOrchestrator:
    """二重かご向け IterationForwardExecutionOrchestrator の単体テストクラス。"""

    def test_execute_succeeds_with_series_embedded_in_input_dto(
        self,
        config,
        logger,
        double_cage_input_im_cable_system_dtos,
    ) -> None:
        """InputDto にシリーズ詳細が埋め込まれていれば execute が成功する。"""
        iteration_input_dto = None
        for input_dto in double_cage_input_im_cable_system_dtos.get_all():
            orch = ForwardExecutionOrchestratorFactory.create(
                config=config,
                logger=logger,
                im_dto=input_dto.im,
                cable=input_dto.cable,
            )
            if isinstance(
                orch,
                IterationForwardExecutionOrchestrator,
            ):
                iteration_input_dto = input_dto
                break
        if iteration_input_dto is None:
            pytest.skip("Iteration 型の input_dto が1件もありません")
        orchestrator = IterationForwardExecutionOrchestrator.create(
            config=config,
            logger=logger,
        )
        itm = orchestrator.execute(input_dto=iteration_input_dto)
        assert itm.simulation_result is not None

    @pytest.mark.slow
    def test_execute_with_all_iteration_inputs_succeeds(
        self,
        config,
        logger,
        double_cage_input_im_cable_system_dtos,
    ) -> None:
        """全組み合わせのうち Iteration 型入力で execute が完了する。

        計算できないパターンでは ValueError を期待してスキップする。
        収束しない場合は設定（current_estimation.convergence_failure_severity: WARNING）
        により例外にならず警告ログで継続し、ItmDto が返る。それ以外は収束して完了する。
        """
        iteration_count = 0
        for input_dto in double_cage_input_im_cable_system_dtos.get_all():
            system_name = input_dto.name.get_value()
            orchestrator = ForwardExecutionOrchestratorFactory.create(
                config=config,
                logger=logger,
                im_dto=input_dto.im,
                cable=input_dto.cable,
            )
            if not isinstance(
                orchestrator,
                IterationForwardExecutionOrchestrator,
            ):
                continue
            iteration_count += 1
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
            pass  # noqa: ERA001
        assert iteration_count > 0, "Iteration 型の入力が1件もありません"


class TestDoubleCageIterationConvergenceCriterionConfig:
    """二重かごについて current_estimation.iteration の各収束基準で execute が完了する。

    config_current_estimation_convergence_criterion（conftest）により一時設定を切替え、
    同一テストが line_current / phase_current / max_over_merged_currents で3回実行される。
    """

    def test_execute_succeeds_for_each_convergence_criterion(
        self,
        config_current_estimation_convergence_criterion,
        logger,
        double_cage_input_im_cable_system_dtos,
    ) -> None:
        """各収束基準で反復が完了し simulation_result が得られる。"""
        config = config_current_estimation_convergence_criterion
        iteration_input_dto = None
        for input_dto in double_cage_input_im_cable_system_dtos.get_all():
            orch = ForwardExecutionOrchestratorFactory.create(
                config=config,
                logger=logger,
                im_dto=input_dto.im,
                cable=input_dto.cable,
            )
            if isinstance(
                orch,
                IterationForwardExecutionOrchestrator,
            ):
                iteration_input_dto = input_dto
                break
        if iteration_input_dto is None:
            pytest.skip("Iteration 型の input_dto が1件もありません")
        orchestrator = IterationForwardExecutionOrchestrator.create(
            config=config,
            logger=logger,
        )
        itm = orchestrator.execute(input_dto=iteration_input_dto)
        assert itm.simulation_result is not None
