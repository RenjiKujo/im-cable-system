"""Forward Input オーケストレーターのインターフェース。

Generic パラメータの特殊化:

- ``InputT``      = :class:`ForwardJobSpec`
    1 ジョブ分のパス束（シリーズ選択 TSV / 軸 TSV /
    optional 性能曲線 TSV）。
- ``LoadedDataT`` = :class:`ForwardInputLoadedData`
    軸 TSV / カタログ YAML / 性能曲線 TSV のロード結果を束ねた中間表現。
- ``InputDtoT``   = :class:`InputDto`

CartesianGrid と OperatingPoints の違いは ``reference_axes`` の選び方だけで、
オーケストレーター内部のフローは同一であるため、本 IF は両モード共通。
``reference_axes`` は :meth:`create` の引数として注入する。
"""

from __future__ import annotations

from abc import abstractmethod

from im_cable_system.engine.algorithm.input_algorithm.i_input_algorithms_orchestrator import (  # noqa: E501
    IInputAlgorithmsOrchestrator,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data import (
    ForwardInputLoadedData,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ArrayKey,
)
from im_cable_system.engine.shared.dto.input import (
    InputDto,
)
from im_cable_system.engine.shared.job_spec.forward import (
    ForwardJobSpec,
)


class IForwardInputOrchestrator(
    IInputAlgorithmsOrchestrator[
        ForwardJobSpec,
        ForwardInputLoadedData,
        InputDto,
    ],
):
    """Forward Input オーケストレーターの契約。

    CartesianGrid モードでは ``reference_axes = [SLIP, INPUT_LINE_VOLTAGE,
    FREQUENCY]``、OperatingPoints モードでは ``reference_axes = [SLIP]`` を
    呼び出し側（InputStage）が選んで :meth:`create` に渡す。
    """

    @classmethod
    @abstractmethod
    def create(
        cls,
        config: IConfig,
        logger: ILogger,
        reference_axes: list[ArrayKey],
    ) -> IForwardInputOrchestrator:
        """オーケストレーターを生成する。

        Args:
            config: 設定。
            logger: ロガー。
            reference_axes: ``ArrayLayoutDto.reference_axes`` に渡す軸の
                順序付きリスト。CartesianGrid モードなら
                ``[SLIP, INPUT_LINE_VOLTAGE, FREQUENCY]``、
                OperatingPoints モードなら ``[SLIP]``。
        """
        raise NotImplementedError
