"""カーブパラメータフィッタのインターフェース。"""

from __future__ import annotations

from abc import ABC, abstractmethod

from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.collect_descriptors import (  # noqa: E501
    FitDescriptorSet,
)
from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.fit_parameters.fit_outcome import (  # noqa: E501
    FitOutcome,
)
from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.forward import (  # noqa: E501
    IForwardExecutionOrchestrator,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ImPerformanceCurveCatalogDtos,
)
from im_cable_system.engine.shared.dto.input import (
    InputDto,
)


class ICurveParameterFitter(ABC):
    """記述子集合と forward を用いてカーブにパラメータをフィットさせる。"""

    @classmethod
    @abstractmethod
    def create(
        cls,
        config: IConfig,
        logger: ILogger,
    ) -> ICurveParameterFitter:
        """config と logger を受け取り、自身のインスタンスを生成する。

        Args:
            config: 設定オブジェクト。
            logger: ロガーオブジェクト。

        Returns:
            ICurveParameterFitter: 生成されたカーブパラメータフィッタ。
        """
        pass

    @abstractmethod
    def fit(
        self,
        input_dto: InputDto,
        catalogs: ImPerformanceCurveCatalogDtos,
        descriptor_set: FitDescriptorSet,
        forward: IForwardExecutionOrchestrator,
    ) -> FitOutcome:
        """least_squares でフィットし、結果を返す。

        Args:
            input_dto: 元の入力 DTO。
            catalogs: 目標とする性能カーブカタログ。
            descriptor_set: フィット記述子集合（IM/ケーブルの区切り付き）。
            forward: 残差評価に用いる forward オーケストレーター。

        Returns:
            FitOutcome: フィット後の物理値と最適化器の生結果。
        """
        pass
