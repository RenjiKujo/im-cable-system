"""IM＋ケーブル系シミュレーション中間DTOクラス。

このモジュールは、IM＋ケーブル系シミュレーションエンジンにおける中間データの
トップレベルDTOを定義します。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from im_cable_system.engine.shared.dto.generic.entity import (
    BaseEntityDto,
)
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ArrayLayoutDto,
    ImCableSystemName,
    ImPerformanceCurveCatalogDtos,
)
from im_cable_system.engine.shared.dto.generic.reporting import (
    EstimateParamsFitSummaryDto,
    NumericalStabilityReportDto,
)
from im_cable_system.engine.shared.dto.itm.model.itm_cable_model_dto import (
    ItmCableModelDto,
)
from im_cable_system.engine.shared.dto.itm.model.itm_im_model_dto import (
    ItmImModelDto,
)
from im_cable_system.engine.shared.dto.itm.model.itm_system_model_dto import (
    ItmSystemModelDto,
)
from im_cable_system.engine.shared.dto.itm.simulation_result.itm_characteristic_dto import (  # noqa: E501
    ItmCharacteristicDto,
)
from im_cable_system.engine.shared.dto.itm.simulation_result.itm_power_dto import (
    ItmPowerDto,
)
from im_cable_system.engine.shared.dto.itm.simulation_result.itm_voltage_current_dto import (
    ItmVoltageCurrentDto,
)


def _default_itm_pc_catalogs() -> ImPerformanceCurveCatalogDtos:
    return ImPerformanceCurveCatalogDtos(objects=[])


# グループ1: 回路モデルDTO（build_modelで構築）
@dataclass(frozen=True)
class ItmModelDto:
    """誘導電動機（IM）とケーブルの統合モデルDTO（グループ1）

    Attributes:
        array_layout (ArrayLayoutDto): 配列レイアウトDTO（汎用DTO）。
            モデル構築段階で使用される配列形状を定義します。
            ``arrays`` / ``reference_axes`` は
            :class:`ArrayLayoutDto` の ``__post_init__`` で
            :class:`ArrayKey` 契約に整合すること。
            軸名をキーとして各軸の1次元配列を保持する辞書形式で、
            多次元配列の軸（次元）を定義します。
        im (ItmImModelDto): 誘導電動機（IM）モデルDTO。
        cable (ItmCableModelDto): ケーブルモデルDTO。
            InputDto.cableがNoneの場合でも、
            ICableModelBuilder.build()が完全導体かつ完全絶縁の擬似ケーブルモデルを作成するため、
            常にItmCableModelDtoが設定されます。
        system (ItmSystemModelDto): システムモデルDTO。
        im_pc_catalogs (ImPerformanceCurveCatalogDtos):
            build_model 時に入力から引き継いだ参照用性能カーブカタログ。
    """

    array_layout: ArrayLayoutDto
    im: ItmImModelDto
    cable: ItmCableModelDto
    system: ItmSystemModelDto
    im_pc_catalogs: ImPerformanceCurveCatalogDtos = field(
        default_factory=_default_itm_pc_catalogs,
    )


# グループ2: シミュレーション結果DTO（simulateで構築、オプショナル）
@dataclass(frozen=True)
class ItmSimulationDto:
    """IM＋ケーブル系シミュレーション結果DTO（グループ2）

    simulateメソッドで計算される電流電圧や特性値を保持します。

    Note:
        配列形状は`model.array_layout`で定義されます。
        `simulation_array_layout`を別途保持しない理由は、`ArrayLayoutDto`の柔軟性により、
        モデル構築段階で必要な軸（例: input_line_voltage）を含めて定義できるためです。
        これにより、シミュレーション段階での配列拡張が不要となり、設計が簡潔になります。

    Attributes:
        voltage_current (ItmVoltageCurrentDto): 電圧・電流DTO。
            シミュレーション計算で得られたIMとケーブルの各地点の電圧・電流を保持します。
        power (ItmPowerDto | None): 電力DTO。電流電圧のみ計算時は None。
        characteristic (ItmCharacteristicDto | None): 特性値DTO。電流電圧のみ計算時は None。
    """

    voltage_current: ItmVoltageCurrentDto
    power: ItmPowerDto | None = None
    characteristic: ItmCharacteristicDto | None = None


# 統合DTO
@dataclass(frozen=True)
class ItmDto:
    """IM＋ケーブル系シミュレーション中間データのトップレベルDTOクラス。

    シミュレーションエンジンの中間処理データを保持します。
    誘導電動機（IM）とケーブルの中間データをサポートしています。

    各グループごとのDTOをコンポジションで保持することで、
    段階的な構築が可能になります。

    Attributes:
        id (str): シミュレーションジョブの一意識別子。
        name (ImCableSystemName): IM ケーブルシステムの一意識別子。
            ``name.get_value()`` をファイル名・CSV 行識別子・report キーに
            使い、``name.get_base()``（表示専用の基底名。候補インデックスを
            除いた名前。forward では ``get_value()`` と同値）を図タイトル等
            の表示にのみ使う。

        model (ItmModelDto): 回路モデルDTO（グループ1）。
            build_modelメソッドで構築されます。
        simulation_result (ItmSimulationDto | None):
            シミュレーション結果DTO（グループ2）。
            simulateメソッドで構築されます。オプショナルです。
        numerical_stability_report (NumericalStabilityReportDto | None):
            記録スコープ内（forward が build_model と simulate をまとめて包む場合は両方含む）
            で集計された数値安定化イベント。
            :class:`SimulationOrchestrator` が simulate 完了時に
            集計して付与する。
        estimate_params_fit_summary (EstimateParamsFitSummaryDto | None):
            estimate_params 完了時のみ。最適化要約・フィット指標・推定パラメータ。
    """

    name: ImCableSystemName

    # 回路モデル（build_modelで構築）
    model: ItmModelDto

    # シミュレーション結果（simulateで構築、オプショナル）
    simulation_result: ItmSimulationDto | None = None

    # 数値安定化イベント集計（forward が build+simulate を同一スコープで包む場合は
    # モデル構築中のイベントも含む。レポートは simulate オーケストレータが
    # contextvar に公開し、呼び出し側が ITM トップに載せる。）
    numerical_stability_report: NumericalStabilityReportDto | None = None

    # パラメータ推定（estimate_params）完了時のみ。最適化要約・フィット指標など
    estimate_params_fit_summary: EstimateParamsFitSummaryDto | None = None


class ItmDtos(BaseEntityDto[ItmDto]):
    """誘導電動機（IM）とケーブルシステムの中間DTOのコレクションDTOクラス

    カタログ性能カーブは各 :class:`ItmDto` の
    ``model.im_pc_catalogs`` に保持する。
    """

    def __init__(self, objects: list[ItmDto]) -> None:
        """初期化する。

        Args:
            objects: 初期の ItmDto オブジェクトリスト。
        """
        super().__init__(objects=objects, attribute_name="name")
