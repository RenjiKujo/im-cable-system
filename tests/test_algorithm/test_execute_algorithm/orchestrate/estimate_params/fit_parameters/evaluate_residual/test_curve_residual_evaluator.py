"""``CurveResidualEvaluator.evaluate`` の配線単体テスト。"""

from __future__ import annotations

from types import SimpleNamespace

import numpy as np

import im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.fit_parameters.evaluate_residual.curve_residual_evaluator as cre  # noqa: E501
from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.fit_parameters.evaluate_residual import (  # noqa: E501
    CurveResidualEvaluator,
)
from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.support.descriptor import (  # noqa: E501
    FittableParamDescriptor,
)
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ImPerformanceCurveCatalogDtos,
)
from im_cable_system.engine.shared.dto.input import InputDto


class TestCurveResidualEvaluatorEvaluate:
    """evaluate の呼び出し順・引数・返却値を stub で検証する。"""

    def test_evaluate_calls_dependencies_in_order_and_returns_residual(
        self,
        monkeypatch,
    ) -> None:
        """to_physical → assemble → execute_without_validation → compute_residual。"""
        z = np.array([0.2, 0.8], dtype=np.float64)
        x_phys = np.array([1.5, 2.5], dtype=np.float64)
        expected_residual = np.array([0.1, -0.2, 0.3], dtype=np.float64)
        call_order: list[str] = []
        residual_kwargs: dict[str, object] = {}

        descriptor_list = [
            FittableParamDescriptor(
                path=("im", "primary_resistance"),
                current_value=1.0,
                lb=0.0,
                ub=10.0,
                unit="Ω",
            ),
        ]
        input_dto = SimpleNamespace(name="input")
        base_input = input_dto
        updated_input = SimpleNamespace(name="updated")
        itm_stub = SimpleNamespace(name="itm")
        catalogs = ImPerformanceCurveCatalogDtos(objects=[])
        normalization_strategy = SimpleNamespace(name="norm")
        weights = (1.0, 2.0, 3.0, 4.0)

        class RecordingBox:
            def to_physical(self, trial_z: np.ndarray) -> np.ndarray:
                call_order.append("to_physical")
                np.testing.assert_array_equal(trial_z, z)
                return x_phys.copy()

        class RecordingAssembler:
            def assemble(
                self,
                *,
                input_dto: InputDto,
                descriptors: list[FittableParamDescriptor],
                x: np.ndarray,
                im_count: int,
            ) -> InputDto:
                call_order.append("assemble")
                assert input_dto is base_input
                assert descriptors is descriptor_list
                np.testing.assert_array_equal(x, x_phys)
                assert im_count == 1
                return updated_input  # type: ignore[return-value]

        class RecordingForward:
            def execute_without_validation(
                self, trial_input: InputDto
            ) -> object:
                call_order.append("execute_without_validation")
                assert trial_input is updated_input
                return itm_stub

        def _fake_compute_residual_vector(
            *,
            catalogs: ImPerformanceCurveCatalogDtos,
            itm: object,
            weights: tuple[float, float, float, float],
            normalization_strategy: object,
        ) -> np.ndarray:
            call_order.append("compute_residual_vector")
            residual_kwargs["catalogs"] = catalogs
            residual_kwargs["itm"] = itm
            residual_kwargs["weights"] = weights
            residual_kwargs["normalization_strategy"] = normalization_strategy
            return expected_residual.copy()

        monkeypatch.setattr(
            cre,
            "compute_residual_vector",
            _fake_compute_residual_vector,
        )

        evaluator = CurveResidualEvaluator.create(
            box=RecordingBox(),  # type: ignore[arg-type]
            descriptors=descriptor_list,
            im_count=1,
            forward=RecordingForward(),  # type: ignore[arg-type]
            catalogs=catalogs,
            weights=weights,
            normalization_strategy=normalization_strategy,  # type: ignore[arg-type]
            input_dto=input_dto,  # type: ignore[arg-type]
            assembler=RecordingAssembler(),  # type: ignore[arg-type]
        )

        result = evaluator.evaluate(z)

        assert call_order == [
            "to_physical",
            "assemble",
            "execute_without_validation",
            "compute_residual_vector",
        ]
        assert residual_kwargs["catalogs"] is catalogs
        assert residual_kwargs["itm"] is itm_stub
        assert residual_kwargs["weights"] == weights
        assert (
            residual_kwargs["normalization_strategy"] is normalization_strategy
        )
        np.testing.assert_array_equal(result, expected_residual)
