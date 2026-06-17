"""フィット要約ビルダーのインターフェース。"""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np
from scipy.optimize import (  # type: ignore[import-untyped]
    OptimizeResult,
)

from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.support.descriptor import (  # noqa: E501
    FittableParamDescriptor,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
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


class IEstimateParamsFitSummaryBuilder(ABC):
    """最適化結果とカーブ誤差から estimate_params 要約 DTO を組み立てる。"""

    @classmethod
    @abstractmethod
    def create(
        cls,
        config: IConfig,
        logger: ILogger,
    ) -> IEstimateParamsFitSummaryBuilder:
        """config と logger を受け取り、自身のインスタンスを生成する。

        Args:
            config: 設定オブジェクト。
            logger: ロガーオブジェクト。

        Returns:
            IEstimateParamsFitSummaryBuilder: 生成された要約ビルダー。
        """
        pass

    @abstractmethod
    def build(
        self,
        input_dto: InputDto,
        descriptors: list[FittableParamDescriptor],
        fitted_x: np.ndarray,
        optimize_result: OptimizeResult,
        pc_catalogs: ImPerformanceCurveCatalogDtos,
        itm_done: ItmDto,
    ) -> EstimateParamsFitSummaryDto:
        """要約 DTO を組み立てる。

        Args:
            input_dto: 元の入力 DTO（出力ラベル用のモデル名抽出に用いる）。
            descriptors: フィット記述子（path / unit の出力に用いる）。
            fitted_x: フィット後の物理パラメータ値。
            optimize_result: 最適化器の生結果。
            pc_catalogs: 目標カタログ。
            itm_done: フィット・検証済みの中間 DTO。

        Returns:
            EstimateParamsFitSummaryDto: 推定要約 DTO。
        """
        pass
