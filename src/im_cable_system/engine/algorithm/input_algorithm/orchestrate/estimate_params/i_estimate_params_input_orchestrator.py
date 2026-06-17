"""EstimateParams 用 Input オーケストレーターのインターフェース。"""

from __future__ import annotations

from abc import abstractmethod

from im_cable_system.engine.algorithm.input_algorithm.i_input_algorithms_orchestrator import (  # noqa: E501
    IInputAlgorithmsOrchestrator,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data.data_class.estimate_params_input_loaded_data import (  # noqa: E501
    EstimateParamsInputLoadedData,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.input import (
    InputDtos,
)
from im_cable_system.engine.shared.job_spec.estimate_params import (
    EstimateParamsJobSpec,
)


class IEstimateParamsInputOrchestrator(
    IInputAlgorithmsOrchestrator[
        EstimateParamsJobSpec,
        tuple[EstimateParamsInputLoadedData, ...],
        InputDtos,
    ],
):
    """EstimateParams 用 Input オーケストレーターの契約。

    1 つの :class:`EstimateParamsJobSpec`（統合 TSV 1 つ）に対し、ファイル I/O
    を 1 回だけ行い、候補軸の直積展開済み LoadedData タプルを経由して
    :class:`InputDtos` を返す。
    """

    @classmethod
    @abstractmethod
    def create(
        cls,
        config: IConfig,
        logger: ILogger,
    ) -> IEstimateParamsInputOrchestrator:
        """オーケストレーターを生成する。

        Args:
            config: 設定。
            logger: ロガー。
        """
        raise NotImplementedError
