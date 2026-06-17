"""カーブ残差評価器の実装。

試行点 z を物理パラメータへ写像 → フィット結果を InputDto へ反映 →
forward（検証なし）で再計算 → カタログとの残差ベクトルを返す。
最適化ループから高頻度に呼ばれるため、検証は走らせない
（``forward.execute_without_validation`` を用いる）。
"""

from __future__ import annotations

import numpy as np

from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.apply_fitted_input import (  # noqa: E501
    IFittedInputAssembler,
)
from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.fit_parameters.box_interval_map import (  # noqa: E501
    BoxIntervalMap,
)
from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.fit_parameters.evaluate_residual.i_curve_residual_evaluator import (  # noqa: E501
    ICurveResidualEvaluator,
)
from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.support.curve_eval import (  # noqa: E501
    compute_residual_vector,
)
from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.support.curve_eval.residual_normalization import (  # noqa: E501
    IResidualNormalizationStrategy,
)
from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.support.descriptor import (  # noqa: E501
    FittableParamDescriptor,
)
from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.forward import (  # noqa: E501
    IForwardExecutionOrchestrator,
)
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ImPerformanceCurveCatalogDtos,
)
from im_cable_system.engine.shared.dto.input import (
    InputDto,
)


class CurveResidualEvaluator(ICurveResidualEvaluator):
    """フィット試行点に対するカタログ残差ベクトルを返す実装。

    設計メモ（依存の生成タイミング）:
        ``evaluate`` は ``scipy.optimize.least_squares`` の残差評価として
        高頻度に呼ばれる。本クラスは ``forward`` / ``assembler`` /
        ``catalogs`` / ``box`` などの依存を **自身では生成せず、フィッタ
        （:class:`CurveParameterFitter`）がフィット開始前に 1 回だけ生成して
        注入（DI）したものを保持する**。``create`` / ``__init__`` は受け取った
        依存を属性へ代入するだけの軽量初期化に徹し、残差ループ内では
        これらを再生成しない。これにより反復ごとの生成コストを排除する。
    """

    def __init__(
        self,
        *,
        box: BoxIntervalMap,
        descriptors: list[FittableParamDescriptor],
        im_count: int,
        forward: IForwardExecutionOrchestrator,
        catalogs: ImPerformanceCurveCatalogDtos,
        weights: tuple[float, float, float, float],
        normalization_strategy: IResidualNormalizationStrategy,
        input_dto: InputDto,
        assembler: IFittedInputAssembler,
    ) -> None:
        """属性をセットするだけの軽量初期化。"""
        self._box = box
        self._descriptors = descriptors
        self._im_count = im_count
        self._forward = forward
        self._catalogs = catalogs
        self._weights = weights
        self._normalization_strategy = normalization_strategy
        self._input_dto = input_dto
        self._assembler = assembler

    @classmethod
    def create(
        cls,
        *,
        box: BoxIntervalMap,
        descriptors: list[FittableParamDescriptor],
        im_count: int,
        forward: IForwardExecutionOrchestrator,
        catalogs: ImPerformanceCurveCatalogDtos,
        weights: tuple[float, float, float, float],
        normalization_strategy: IResidualNormalizationStrategy,
        input_dto: InputDto,
        assembler: IFittedInputAssembler,
    ) -> ICurveResidualEvaluator:
        """残差評価器を生成する。"""
        return cls(
            box=box,
            descriptors=descriptors,
            im_count=im_count,
            forward=forward,
            catalogs=catalogs,
            weights=weights,
            normalization_strategy=normalization_strategy,
            input_dto=input_dto,
            assembler=assembler,
        )

    def evaluate(self, z: np.ndarray) -> np.ndarray:
        """試行点 z に対する重み付き残差ベクトルを返す。"""
        x_phys = self._box.to_physical(z)
        updated_input = self._assembler.assemble(
            input_dto=self._input_dto,
            descriptors=self._descriptors,
            x=x_phys,
            im_count=self._im_count,
        )
        itm = self._forward.execute_without_validation(updated_input)
        return compute_residual_vector(
            catalogs=self._catalogs,
            itm=itm,
            weights=self._weights,
            normalization_strategy=self._normalization_strategy,
        )
