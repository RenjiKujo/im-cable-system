"""カーブパラメータフィッタの実装。

ボックス正規化座標で ``scipy.optimize.least_squares`` を実行する。
可動次元は [0,1]、lb==ub の固定次元は z を一点に拘束する。
残差評価は :class:`CurveResidualEvaluator` に委譲する。
"""

from __future__ import annotations

import numpy as np
from scipy.optimize import least_squares  # type: ignore[import-untyped]

from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.apply_fitted_input import (  # noqa: E501
    FittedInputAssembler,
)
from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.collect_descriptors import (  # noqa: E501
    FitDescriptorSet,
)
from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.fit_parameters.box_interval_map import (  # noqa: E501
    BoxIntervalMap,
)
from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.fit_parameters.evaluate_residual import (  # noqa: E501
    CurveResidualEvaluator,
)
from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.fit_parameters.fit_outcome import (  # noqa: E501
    FitOutcome,
)
from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.fit_parameters.optimize.i_curve_parameter_fitter import (  # noqa: E501
    ICurveParameterFitter,
)
from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.support.curve_eval.residual_normalization import (  # noqa: E501
    ResidualNormalizationStrategyFactory,
)
from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.forward import (  # noqa: E501
    IForwardExecutionOrchestrator,
)
from im_cable_system.engine.shared.config import (
    EstimateParamsConfig,
    IConfig,
    ILogger,
)
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ImPerformanceCurveCatalogDtos,
)
from im_cable_system.engine.shared.dto.input import (
    InputDto,
)


class CurveParameterFitter(ICurveParameterFitter):
    """least_squares によるカーブパラメータフィット実装。"""

    def __init__(self, config: IConfig, logger: ILogger) -> None:
        """インスタンスを初期化する。"""
        self._config: IConfig = config
        self._logger: ILogger = logger

    @classmethod
    def create(
        cls,
        config: IConfig,
        logger: ILogger,
    ) -> ICurveParameterFitter:
        """config と logger を受け取り、自身のインスタンスを生成する。"""
        return cls(config=config, logger=logger)

    def fit(
        self,
        input_dto: InputDto,
        catalogs: ImPerformanceCurveCatalogDtos,
        descriptor_set: FitDescriptorSet,
        forward: IForwardExecutionOrchestrator,
    ) -> FitOutcome:
        """least_squares でフィットし、結果を返す。

        設計メモ（依存の生成タイミング）:
            残差評価器（:class:`CurveResidualEvaluator`）とその依存
            （``forward`` / ``assembler`` など）は、``least_squares`` の
            残差ループに入る **前にここで 1 回だけ生成して注入** する。
            ループ内（``evaluator.evaluate``）では再生成しないため、
            反復ごとの生成コストを払わない。
        """
        descriptors = descriptor_set.descriptors
        x0 = np.array([d.current_value for d in descriptors], dtype=float)
        lb = np.array([d.lb for d in descriptors], dtype=float)
        ub = np.array([d.ub for d in descriptors], dtype=float)
        box = BoxIntervalMap.create(lb, ub)
        z_lb = box.unit_lower_bounds()
        z_ub = box.unit_upper_bounds()
        z0 = np.clip(box.to_unit(x0), z_lb, z_ub)

        est_params = self._config.estimate_params_calculation_config
        evaluator = CurveResidualEvaluator.create(
            box=box,
            descriptors=descriptors,
            im_count=descriptor_set.im_count,
            forward=forward,
            catalogs=catalogs,
            weights=self._residual_weights_from_config(est_params),
            normalization_strategy=(
                ResidualNormalizationStrategyFactory.create(
                    est_params.residual.normalization
                )
            ),
            input_dto=input_dto,
            assembler=FittedInputAssembler.create(
                config=self._config,
                logger=self._logger,
            ),
        )

        ls_cfg = est_params.optimizer.least_squares
        result = least_squares(
            evaluator.evaluate,
            z0,
            bounds=(z_lb, z_ub),
            max_nfev=ls_cfg.max_nfev,
            ftol=ls_cfg.ftol,
            xtol=ls_cfg.xtol,
            gtol=ls_cfg.gtol,
            x_scale="jac",  # NOTE: ヤコビアン由来で変数を動的スケーリングし悪条件を緩和する。収束反復が減り forward 評価回数（総計算時間）の削減を狙う。
        )
        if not result.success:
            self._logger.warning(
                "パラメータフィットが収束しませんでした: %s", result.message
            )
        fitted_x = box.to_physical(result.x)
        return FitOutcome(fitted_x=fitted_x, optimize_result=result)

    @staticmethod
    def _residual_weights_from_config(
        est_params: EstimateParamsConfig,
    ) -> tuple[float, float, float, float]:
        """残差評価器へ渡す重みを設定から順序付きタプルで返す。"""
        weights = est_params.residual.weights
        return (
            weights.current,
            weights.power,
            weights.power_factor,
            weights.efficiency,
        )
