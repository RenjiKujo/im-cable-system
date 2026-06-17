"""IterationForwardExecutionOrchestrator の単体テスト（単カゴ）。

4_test_strategy.md の「実装の単体テスト（Iteration）」に準拠。
conftest 経由で config_test_orchestrator.yaml を読み込み、本番 config.yaml と
項目を揃えたテスト用設定を使用する。
電流イテレーション（電流依存イミタンス）で収束しない場合、
current_estimation.convergence_failure_severity: "WARNING" のため例外は送出されず
警告ログで継続し execute が ItmDto を返して完了する。その挙動を確認する。
"""

from __future__ import annotations

from typing import cast

import numpy as np
import pytest

from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.forward.factory_forward_execution_orchestrator import (  # noqa: E501
    ForwardExecutionOrchestratorFactory,
)
from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.forward.iteration_forward_execution_orchestrator import (  # noqa: E501
    IterationForwardExecutionOrchestrator,
)


class TestSingleCageIterationForwardExecutionOrchestrator:
    """単カゴ向け IterationForwardExecutionOrchestrator の単体テストクラス。"""

    def test_execute_succeeds_with_series_embedded_in_input_dto(
        self,
        config,
        logger,
        single_cage_input_im_cable_system_dtos,
    ) -> None:
        """InputDto にシリーズ詳細が埋め込まれていれば execute が成功する。"""
        iteration_input_dto = None
        for input_dto in single_cage_input_im_cable_system_dtos.get_all():
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

    def test_execute_without_validation_sets_full_simulation_result(
        self,
        config,
        logger,
        single_cage_input_im_cable_system_dtos,
    ) -> None:
        """execute_without_validation は検証を除きフル simulate 結果を返す。"""
        iteration_input_dto = None
        for input_dto in single_cage_input_im_cable_system_dtos.get_all():
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
        itm = orchestrator.execute_without_validation(
            input_dto=iteration_input_dto
        )
        simulation_result = itm.simulation_result
        assert simulation_result is not None
        assert simulation_result.power is not None
        assert simulation_result.characteristic is not None

    @pytest.mark.slow
    def test_execute_with_all_iteration_inputs_succeeds(
        self,
        config,
        logger,
        single_cage_input_im_cable_system_dtos,
    ) -> None:
        """全組み合わせのうち Iteration 型入力で execute が完了する。

        計算できないパターンでは ValueError を期待してスキップする。
        収束しない場合は設定（current_estimation.convergence_failure_severity: WARNING）
        により例外にならず警告ログで継続し、ItmDto が返る。それ以外は収束して完了する。
        """
        iteration_count = 0
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


class TestIterationLineCurrentConvergence:
    """線電流収束判定（_arrays_converged）の境界条件。"""

    def test_converged_empty_arrays_returns_true(
        self,
        config,
        logger,
    ) -> None:
        """要素数 0 のとき比較なしで True（収束扱い）。"""
        orch = cast(
            IterationForwardExecutionOrchestrator,
            IterationForwardExecutionOrchestrator.create(
                config=config,
                logger=logger,
            ),
        )
        tol = config.current_estimation_config.iteration.convergence_tolerance
        assert orch._arrays_converged(
            np.array([], dtype=np.complex128),
            np.array([], dtype=np.complex128),
            tol,
        )
        assert orch._arrays_converged(
            np.array([1.0 + 0.0j]),
            np.array([], dtype=np.complex128),
            tol,
        )

    def test_converged_finite_arrays_below_tolerance(
        self,
        config,
        logger,
    ) -> None:
        """相対変化が閾値未満なら True。"""
        orch = cast(
            IterationForwardExecutionOrchestrator,
            IterationForwardExecutionOrchestrator.create(
                config=config,
                logger=logger,
            ),
        )
        tol = config.current_estimation_config.iteration.convergence_tolerance
        prev = np.array([1.0 + 0.0j, 2.0 + 0.0j], dtype=np.complex128)
        curr = prev * (1.0 + 1.0e-7)
        assert orch._arrays_converged(curr, prev, tol)


class TestIterationConvergenceStates:
    """辞書（マージ電流）基準の収束判定の境界条件。"""

    def test_convergence_states_merged_dicts_below_tolerance(
        self,
        config,
        logger,
    ) -> None:
        """全キーで相対変化が閾値未満なら True。"""
        orch = cast(
            IterationForwardExecutionOrchestrator,
            IterationForwardExecutionOrchestrator.create(
                config=config,
                logger=logger,
            ),
        )
        tol = 1.0e-6
        prev = {
            "a": np.array([1.0 + 0.0j], dtype=np.complex128),
            "b": np.array([2.0 + 0.0j, 3.0 + 0.0j], dtype=np.complex128),
        }
        curr = {
            "b": prev["b"] * (1.0 + 1.0e-7),
            "a": np.array([1.0 + 1.0e-7j], dtype=np.complex128),
        }
        assert orch._convergence_states_converged(
            curr,
            prev,
            tol,
        )

    def test_convergence_states_merged_dicts_key_mismatch_returns_false(
        self,
        config,
        logger,
    ) -> None:
        """キー集合が一致しなければ False。"""
        orch = cast(
            IterationForwardExecutionOrchestrator,
            IterationForwardExecutionOrchestrator.create(
                config=config,
                logger=logger,
            ),
        )
        prev = {"a": np.array([1.0], dtype=np.complex128)}
        curr = {"b": np.array([1.0], dtype=np.complex128)}
        assert not orch._convergence_states_converged(
            curr,
            prev,
            1.0e-6,
        )


class TestSingleCageIterationConvergenceCriterionConfig:
    """current_estimation.iteration.convergence_criterion の各パターンで execute が完了する。

    config_current_estimation_convergence_criterion（conftest）が一時 YAML で
    基準を切り替え、同一テストが3回走る。
    """

    def test_execute_succeeds_for_each_convergence_criterion(
        self,
        config_current_estimation_convergence_criterion,
        logger,
        single_cage_input_im_cable_system_dtos,
    ) -> None:
        """設定どおりの基準でも反復が収束し execute が完了する。"""
        config = config_current_estimation_convergence_criterion
        iteration_input_dto = None
        for input_dto in single_cage_input_im_cable_system_dtos.get_all():
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
