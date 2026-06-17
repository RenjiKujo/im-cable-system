"""Forward 系パイプライン用ロード結果のトップレベルデータクラス。

CartesianGrid / OperatingPoints のいずれも、シリーズ選択・カタログ・
評価点軸・任意の性能曲線を束ねた中間表現として共通利用する。
engine 層 DTO への変換は ``assemble_input_dto.forward`` 側で行う。
"""

from __future__ import annotations

from dataclasses import dataclass

from im_cable_system.engine.algorithm.input_algorithm.load_data.data_class.axes_loaded_data import (  # noqa: E501
    AxesLoadedData,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data.data_class.cable_loaded_data import (  # noqa: E501
    CableLoadedData,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data.data_class.im_loaded_data import (  # noqa: E501
    ImLoadedData,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data.data_class.im_performance_curve_loaded_data import (  # noqa: E501
    ImPerformanceCurveLoadedData,
)


@dataclass(frozen=True)
class ForwardInputLoadedData:
    """Forward 系ローダーの戻り値（CartesianGrid / OperatingPoints 共通）。

    Attributes:
        im_cable_system_name: システム名。
        im: 誘導電動機の中間表現。
        cable: ケーブル束。無しのとき ``None``。
        axes: 評価点軸（スリップ・周波数・入力線間電圧）。
        im_performance_curve: 性能曲線の中間表現。未指定時 ``None``。
    """

    im_cable_system_name: str
    im: ImLoadedData
    cable: CableLoadedData | None
    axes: AxesLoadedData
    im_performance_curve: ImPerformanceCurveLoadedData | None
