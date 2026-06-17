"""3モード共通の出力トップレベル DTO（Input 由来 × Simulation 結果）と、その
コレクション DTO。

NOTE: 図表専用属性は持たず、既存ドメイン値オブジェクトの合成で「不足のない」
    出力データを表す。属性として持つ DTO はすべて ``generic`` 由来
    （``im_cable_system`` / ``physical_quantity`` / ``reporting``）であり、
    ``itm`` ステージ DTO には依存しない。``result`` のみ本パッケージ内の
    結果生量 DTO（中身は ``generic.physical_quantity`` の合成）を用いる。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from im_cable_system.engine.shared.dto.generic.entity import (
    BaseEntityDto,
)
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ArrayLayoutDto,
    CableDto,
    ImCableSystemName,
    ImDto,
    ImPerformanceCurveCatalogDtos,
)
from im_cable_system.engine.shared.dto.generic.reporting import (
    EstimateParamsFitSummaryDto,
    NumericalStabilityReportDto,
)
from im_cable_system.engine.shared.dto.output.output_simulation_result_dto import (  # noqa: E501
    OutputSimulationResultDto,
)


def _default_im_pc_catalogs() -> ImPerformanceCurveCatalogDtos:
    """空の参照性能カーブカタログ（Output の既定値）。"""
    return ImPerformanceCurveCatalogDtos(objects=[])


@dataclass(frozen=True)
class OutputDto:
    """IM ケーブルシステム出力データのトップレベル DTO（新設計）。

    入力原値（Input 由来）とシミュレーション結果の生量を併せ持つ。
    3モード（ForwardByCartesianGrid / EstimateParams / OperatingPoints）で同型。
    図表（slip 軸グリッド / index 時系列）と表は、本 DTO の ``array_layout`` /
    ``result`` / ``im_pc_catalogs`` から派生計算して生成する（図表専用属性は持たない）。

    モード差は ``array_layout.reference_axes`` で判別する:
        - ``[SLIP]`` → index（時系列）表示
        - ``[SLIP, INPUT_LINE_VOLTAGE, FREQUENCY]`` → slip 軸グリッド表示

    Attributes:
        name: IM ケーブルシステムの一意識別子（ファイル名等の文脈に用いる）。
        array_layout: 配列レイアウト。slip / 供給条件(V,f) の軸と ``reference_axes``
            を保持し、横軸・スライス・モード判別の根拠となる。
        im: 入力原値の誘導電動機 DTO（銘板・モデル選択ラベル・基本 R/L の原典）。
        cable: 入力原値のケーブル DTO。ケーブル無し入力では ``None``。
        result: 出力に必要なシミュレーション結果の生量。
        im_pc_catalogs: 参照用性能カーブカタログ（重ね描き・推定比較に用いる）。
            既定は空カタログ（参照カーブ無し）。
        numerical_stability_report: 数値安定化イベント集計。発火が無い場合や
            集計スコープ外では ``None``。
        estimate_params_fit_summary: パラメータ推定の最適化結果要約。
            EstimateParams 以外では ``None``。
    """

    name: ImCableSystemName
    array_layout: ArrayLayoutDto
    im: ImDto
    cable: CableDto | None
    result: OutputSimulationResultDto
    im_pc_catalogs: ImPerformanceCurveCatalogDtos = field(
        default_factory=_default_im_pc_catalogs,
    )
    numerical_stability_report: NumericalStabilityReportDto | None = None
    estimate_params_fit_summary: EstimateParamsFitSummaryDto | None = None


class OutputDtos(BaseEntityDto[OutputDto]):
    """OutputDto のコレクション DTO クラス。

    複数 IM ケーブルシステムの :class:`OutputDto` をまとめて扱うための薄い
    ラッパー。``BaseEntityDto`` の機能を継承し、``name`` を識別属性とする。
    """

    def __init__(self, objects: list[OutputDto]) -> None:
        """初期化する。

        Args:
            objects: 初期の OutputDto オブジェクトリスト。
        """
        super().__init__(objects=objects, attribute_name="name")
