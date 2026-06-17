"""CurveParameterFitter の単体テスト。"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, cast

import numpy as np

import im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.fit_parameters.optimize.curve_parameter_fitter as cpf  # noqa: E501
from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.collect_descriptors import (  # noqa: E501
    FitDescriptorSet,
)
from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.fit_parameters import (  # noqa: E501
    CurveParameterFitter,
    ICurveParameterFitter,
)
from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.support.descriptor import (  # noqa: E501
    FittableParamDescriptor,
)
from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.forward import (
    IForwardExecutionOrchestrator,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.config.schema.estimate_params import (
    EstimateParamsConfigFactory,
)
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ImPerformanceCurveCatalogDtos,
)
from im_cable_system.engine.shared.dto.input import InputDto


class TestCurveParameterFitter:
    """カーブパラメータフィッタの生成を確認する。"""

    def test_create_returns_interface(
        self,
        config: IConfig,
        logger: ILogger,
    ) -> None:
        """create がインターフェース型を返す。"""
        fitter = CurveParameterFitter.create(config=config, logger=logger)
        assert isinstance(fitter, ICurveParameterFitter)


class TestCurveParameterFitterResidualWeights:
    """``CurveParameterFitter`` が残差重みを設定順に解決することを確認する。"""

    def test_defaults_when_residual_missing(self) -> None:
        """residual 未定義なら全チャネル 1.0。"""
        cfg = EstimateParamsConfigFactory.create({})
        assert CurveParameterFitter._residual_weights_from_config(cfg) == (
            1.0,
            1.0,
            1.0,
            1.0,
        )

    def test_partial_keys_use_default_for_missing(self) -> None:
        """指定したキーのみ上書き、欠損は 1.0。"""
        cfg = EstimateParamsConfigFactory.create(
            {"residual": {"weights": {"current": 2.0}}},
        )
        assert CurveParameterFitter._residual_weights_from_config(cfg) == (
            2.0,
            1.0,
            1.0,
            1.0,
        )

    def test_all_keys(self) -> None:
        """4 キーすべて反映される。"""
        cfg = EstimateParamsConfigFactory.create(
            {
                "residual": {
                    "weights": {
                        "current": 0.5,
                        "power": 1.5,
                        "power_factor": 0.0,
                        "efficiency": 2.0,
                    },
                },
            },
        )
        assert CurveParameterFitter._residual_weights_from_config(cfg) == (
            0.5,
            1.5,
            0.0,
            2.0,
        )


class TestCurveParameterFitterWiring:
    """``fit`` の box 写像・bounds・least_squares 連携を確認する。

    forward を実行せず、``least_squares`` を stub に差し替えて、最適化への
    入力（z0・bounds）と出力（``box.to_physical(result.x)``）の配線のみ検証する。
    """

    def test_fit_passes_unit_box_and_returns_physical(
        self,
        monkeypatch,
        config: IConfig,
        logger: ILogger,
    ) -> None:
        """z0 が単位区間へ写り、fitted_x が物理座標へ戻る。"""
        descriptors = [
            FittableParamDescriptor(
                path=("im", "primary_resistance"),
                current_value=1.0,
                lb=0.0,
                ub=10.0,
                unit="Ω",
            ),
        ]
        descriptor_set = FitDescriptorSet(descriptors=descriptors, im_count=1)
        captured: dict[str, Any] = {}

        def _fake_least_squares(_fun, z0, *, bounds, **_kwargs):  # noqa: ANN001
            captured["z0"] = np.asarray(z0, dtype=np.float64)
            captured["bounds"] = bounds
            return SimpleNamespace(
                x=np.asarray(z0, dtype=np.float64),
                success=True,
                message="ok",
                nfev=1,
                cost=0.0,
                fun=np.zeros(1, dtype=np.float64),
            )

        monkeypatch.setattr(cpf, "least_squares", _fake_least_squares)

        fitter = CurveParameterFitter.create(config=config, logger=logger)
        outcome = fitter.fit(
            input_dto=cast(InputDto, SimpleNamespace()),
            catalogs=ImPerformanceCurveCatalogDtos(objects=[]),
            descriptor_set=descriptor_set,
            forward=cast(IForwardExecutionOrchestrator, SimpleNamespace()),
        )

        # x=1, lb=0, ub=10 → z0 = 0.1
        assert np.isclose(captured["z0"][0], 0.1)
        # 可動次元の bounds は [0, 1]
        z_lb, z_ub = captured["bounds"]
        assert np.isclose(z_lb[0], 0.0)
        assert np.isclose(z_ub[0], 1.0)
        # fitted_x = to_physical(z0) = 1.0
        assert np.isclose(outcome.fitted_x[0], 1.0)
        assert outcome.optimize_result.success is True
