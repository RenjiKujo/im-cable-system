"""ロード結果（中間表現）データクラスの公開窓口。

本サブパッケージは ``load_data`` 層の戻り値となる中間表現データクラスを
集約する。engine 層 DTO（``ImSeriesDto`` 等）には依存させず、入力ファイル
群を parse した結果を `np.ndarray` / プリミティブ / ``Mapping[str, Any]``
など一般的な型のみで保持する。DTO 化は ``assemble_input_dto`` 層に委ねる。

ファイル分割の方針:
    将来、各パイプライン（機能）の入力ロードで **共通して使うデータクラス**
    となることを見据え、責務単位で 1 ファイル 1 データクラスに分けて配置
    する。Forward 系トップレベル束ねは
    :class:`ForwardInputLoadedData` に統合し、評価点軸は
    :class:`AxesLoadedData` を共通部品とする。構成部品（
    :class:`CableLoadedData` / :class:`CableSectionLoadedData` /
    :class:`ImLoadedData` / :class:`ImPerformanceCurveLoadedData`）は
    パイプライン横断で再利用できるよう独立したファイルに置く。
"""

from im_cable_system.engine.algorithm.input_algorithm.load_data.data_class.axes_loaded_data import (  # noqa: E501
    AxesLoadedData,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data.data_class.cable_loaded_data import (  # noqa: E501
    CableLoadedData,
    CableSectionLoadedData,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data.data_class.estimate_params_input_loaded_data import (  # noqa: E501
    EstimateParamsInputLoadedData,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data.data_class.forward_input_loaded_data import (  # noqa: E501
    ForwardInputLoadedData,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data.data_class.im_loaded_data import (  # noqa: E501
    ImBranchLoadedData,
    ImLoadedData,
    ImNameplateLoadedData,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data.data_class.im_performance_curve_loaded_data import (  # noqa: E501
    ImPerformanceCurveLoadedData,
)

__all__ = [
    "AxesLoadedData",
    "CableLoadedData",
    "CableSectionLoadedData",
    "EstimateParamsInputLoadedData",
    "ForwardInputLoadedData",
    "ImBranchLoadedData",
    "ImLoadedData",
    "ImNameplateLoadedData",
    "ImPerformanceCurveLoadedData",
]
