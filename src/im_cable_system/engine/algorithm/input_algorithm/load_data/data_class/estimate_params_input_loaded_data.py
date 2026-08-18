"""EstimateParams 系パイプライン用ロード結果のトップレベルデータクラス。

統合 TSV と探索境界 YAML（Config 経由）から、候補モデル組み合わせの
1 件分（``InputDto`` の初期値 1 件分）を表す中間表現。直積展開後の
1 要素として ``Loader`` が tuple で返す前提。

:class:`ForwardInputLoadedData` と同じフィールド構成を取り、
``im_performance_curve`` のみ **必須** にする（EstimateParams では
推定の参照曲線が必須のため）。
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
class EstimateParamsInputLoadedData:
    """EstimateParams ローダーの戻り値（候補組み合わせ 1 件分）。

    Attributes:
        im_cable_system_name: システム名。直積で展開した各組み合わせを一意に
            する完全な文字列ラベル（``f"{perf_curve_name}_{discriminator}"``。
            典型: ``f"{perf_curve_name}_{combo_idx}"``）。
            ``assemble_input_dto`` はこのフィールドを ``InputDto.name`` の
            組み立てには使わない（``im_performance_curve.name`` と
            ``name_discriminator`` から直接組み立てる）。このフィールドは
            ローダー内での人間可読な完全名、および両者が一致することを
            固定するテスト不変条件（`dto.name.get_value() ==
            loaded_data.im_cable_system_name`）用に残している。
        name_discriminator: 候補一意化接尾辞（``ImCableSystemName.discriminator``
            用）。``im_cable_system_name`` の文字列分解（プレフィックス除去）で
            はなく、``im_cable_system_name`` と同じ ``combo`` から独立に
            並行して組み立てる（採用軸の増減でフォーマットが変わっても
            文字列分解側が壊れないようにするため）。
        im: 誘導電動機の中間表現（R/L はモデル候補と bounds 中点で初期化済み）。
        cable: ケーブル束。``cable_length == 0`` のとき ``None``。
        axes: 評価点軸（性能曲線由来の slip と供給条件で構成）。
        im_performance_curve: 性能曲線の中間表現。EstimateParams では必須。
    """

    im_cable_system_name: str
    name_discriminator: str
    im: ImLoadedData
    cable: CableLoadedData | None
    axes: AxesLoadedData
    im_performance_curve: ImPerformanceCurveLoadedData
