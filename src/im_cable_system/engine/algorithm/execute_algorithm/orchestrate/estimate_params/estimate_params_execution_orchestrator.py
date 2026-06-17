"""IM ケーブルシステム パラメータ推定オーケストレーター（パラメータフィット実装）。

モデル種別に応じてフィット対象を動的に抽出し、パフォーマンスカーブに
等価回路パラメータ（一次・励磁・二次 R/L、スリップ/電流依存係数、ケーブル R/L 等）を
フィットさせる。正規化＋重み付き残差で |I|, P, PF, η を目的関数に用いる。

本オーケストレーターは薄い調整役に徹し、各責務はサブパッケージへ委譲する:
    - 記述子収集: :mod:`collect_descriptors`
    - フィット（least_squares・残差評価）: :mod:`fit_parameters`
    - フィット結果の InputDto 反映: :mod:`apply_fitted_input`
    - 要約 DTO 組み立て: :mod:`build_summary`

Note:
    最適化ループ内の残差評価では forward の ``execute_without_validation`` を呼ぶ。
    ``execute`` は ``_validate_itm_dto`` まで含むため、残差計算のたびに検証を
    走らせると反復回数分だけ計算コストが無駄に増える。検証はフィット完了後の
    ``forward.execute``（1 回）で行う。

Memo（設定と実装の対応）:
    - ``execution.estimate_params.optimizer`` の ``max_nfev`` / ``ftol`` /
      ``xtol`` / ``gtol`` は ``scipy.optimize.least_squares`` にそのまま渡す。
    - ``execution.estimate_params.residual.weights``（current / power /
      power_factor / efficiency）は ``CurveParameterFitter`` 内で解決し、
      ``compute_residual_vector`` に渡る。目的から外すチャネルは重み 0。
    - ``config.yaml`` の ``residual.normalization``（method / statistic /
      eps）は ``CurveParameterFitter`` 内で
      ``ResidualNormalizationStrategyFactory`` により strategy 化され、
      ``CurveResidualEvaluator`` 経由で ``compute_residual_vector`` に渡る。
      fit 時はこの設定が実際に効く。
      なお :mod:`support.curve_eval.curve_residual_vector` の
      ``std(concat(target, pred)) + eps`` は strategy 未指定（``None``）時の
      フォールバック実装であり、fit 経路では用いられない。
"""

from __future__ import annotations

from dataclasses import replace

from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.apply_fitted_input import (  # noqa: E501
    FittedInputAssembler,
)
from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.build_summary import (  # noqa: E501
    EstimateParamsFitSummaryBuilder,
)
from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.collect_descriptors import (  # noqa: E501
    FitDescriptorCollector,
    FitDescriptorSet,
)
from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.fit_parameters import (  # noqa: E501
    CurveParameterFitter,
    FitOutcome,
)
from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.i_estimate_params_execution_orchestrator import (  # noqa: E501
    IEstimateParamsExecutionOrchestrator,
)
from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.forward import (  # noqa: E501
    ForwardExecutionOrchestratorFactory,
    IForwardExecutionOrchestrator,
)
from im_cable_system.engine.shared.config import (
    IConfig,
    ILogger,
    timer,
)
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    CableDto,
    ImDto,
    ImPerformanceCurveCatalogDtos,
)
from im_cable_system.engine.shared.dto.generic.reporting import (
    EstimateParamsFitSummaryDto,
)
from im_cable_system.engine.shared.dto.input import (
    InputDto,
)
from im_cable_system.engine.shared.dto.itm import (
    ItmDto,
)


class EstimateParamsOrchestrator(IEstimateParamsExecutionOrchestrator):
    """IM ケーブルシステム パラメータ推定オーケストレーター（パラメータフィット実装）。

    入力解決・記述子収集・フィット・要約組み立てを各サブパッケージへ委譲し、
    本クラスは手順の調整のみを担う。フィット後に forward の ``execute``
    （build_model → simulate → validate）で ItmDto を確定させる。

    Note:
        フィット中の残差評価では forward の ``execute_without_validation`` を呼ぶ
        （理由は本モジュール先頭のモジュールドックストリング参照）。
    """

    def __init__(self, config: IConfig, logger: ILogger) -> None:
        """オーケストレーターを初期化する。"""
        self._config: IConfig = config
        self._logger: ILogger = logger

    @classmethod
    def create(
        cls,
        config: IConfig,
        logger: ILogger,
    ) -> IEstimateParamsExecutionOrchestrator:
        """config と logger を受け取り、自身のインスタンスを生成する。"""
        return cls(config=config, logger=logger)

    @timer(logger=None, line="#", min_duration=0.01)
    def execute(self, input_dto: InputDto) -> ItmDto:
        """1 本の InputDto に対しパラメータフィット後に build → simulate → validate する。"""
        descriptor_set = self._collect_descriptors(
            input_dto.im, input_dto.cable
        )
        forward = self._create_forward(input_dto)

        outcome = self._fit_parameters(
            input_dto=input_dto,
            catalogs=input_dto.im_pc_catalogs,
            descriptor_set=descriptor_set,
            forward=forward,
        )

        fitted_input = self._apply_fitted_params(
            input_dto=input_dto,
            descriptor_set=descriptor_set,
            outcome=outcome,
        )
        itm_done = forward.execute(fitted_input)
        summary = self._build_summary(
            input_dto=input_dto,
            descriptor_set=descriptor_set,
            outcome=outcome,
            catalogs=input_dto.im_pc_catalogs,
            itm_done=itm_done,
        )
        return replace(itm_done, estimate_params_fit_summary=summary)

    def _collect_descriptors(
        self,
        im_dto: ImDto,
        cable_dto: CableDto | None,
    ) -> FitDescriptorSet:
        """フィット記述子集合を収集する（bounds 読み込みはコレクタが担う）。"""
        collector = FitDescriptorCollector.create(
            config=self._config,
            logger=self._logger,
        )
        return collector.collect(
            im_dto,
            cable_dto,
        )

    def _create_forward(
        self,
        input_dto: InputDto,
    ) -> IForwardExecutionOrchestrator:
        """残差評価・最終確定に用いる forward オーケストレーターを生成する。"""
        return ForwardExecutionOrchestratorFactory.create(
            config=self._config,
            logger=self._logger,
            im_dto=input_dto.im,
            cable=input_dto.cable,
        )

    def _fit_parameters(
        self,
        *,
        input_dto: InputDto,
        catalogs: ImPerformanceCurveCatalogDtos,
        descriptor_set: FitDescriptorSet,
        forward: IForwardExecutionOrchestrator,
    ) -> FitOutcome:
        """least_squares でパラメータをフィットさせる。"""
        fitter = CurveParameterFitter.create(
            config=self._config,
            logger=self._logger,
        )
        return fitter.fit(
            input_dto=input_dto,
            catalogs=catalogs,
            descriptor_set=descriptor_set,
            forward=forward,
        )

    def _apply_fitted_params(
        self,
        *,
        input_dto: InputDto,
        descriptor_set: FitDescriptorSet,
        outcome: FitOutcome,
    ) -> InputDto:
        """フィット結果を反映した最終 InputDto を組み立てる。"""
        assembler = FittedInputAssembler.create(
            config=self._config,
            logger=self._logger,
        )
        return assembler.assemble(
            input_dto=input_dto,
            descriptors=descriptor_set.descriptors,
            x=outcome.fitted_x,
            im_count=descriptor_set.im_count,
        )

    def _build_summary(
        self,
        *,
        input_dto: InputDto,
        descriptor_set: FitDescriptorSet,
        outcome: FitOutcome,
        catalogs: ImPerformanceCurveCatalogDtos,
        itm_done: ItmDto,
    ) -> EstimateParamsFitSummaryDto:
        """estimate_params 要約 DTO を組み立てる。"""
        builder = EstimateParamsFitSummaryBuilder.create(
            config=self._config,
            logger=self._logger,
        )
        return builder.build(
            input_dto=input_dto,
            descriptors=descriptor_set.descriptors,
            fitted_x=outcome.fitted_x,
            optimize_result=outcome.optimize_result,
            pc_catalogs=catalogs,
            itm_done=itm_done,
        )
