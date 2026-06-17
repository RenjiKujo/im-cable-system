from dataclasses import dataclass

from im_cable_system.engine.shared.dto.generic.entity import (
    BaseEntityDto,
)
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    CableConductorModelDto,
    CableName,
    CableSectionName,
    CableSeriesName,
    CableShapeTypeDto,
    PieCableConductorKey,
    PieCableGroundKey,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexAdmittanceDto,
    ArrayComplexImpedanceDto,
    FloatCapacitancePerLengthDto,
    FloatInductancePerLengthDto,
    FloatLengthDto,
    FloatResistanceLengthDto,
    FloatResistancePerLengthDto,
)


# NOTE: グループ1: 基本情報DTO
@dataclass(frozen=True)
class ItmCableBasicDto:
    """ケーブルの基本情報DTO（グループ1）

    Attributes:
        name (CableSectionName): ケーブルセクション名。
        series_name (CableSeriesName): ケーブルシリーズ名。
        shape_type (CableShapeTypeDto): ケーブル形状タイプ（FLAT, ROUND）
        length (FloatLengthDto): ケーブルの長さ・距離
    """

    name: CableSectionName
    series_name: CableSeriesName
    shape_type: CableShapeTypeDto
    length: FloatLengthDto


# NOTE: グループ2: 線密度
@dataclass(frozen=True)
class ItmCableLineDensityDto:
    """ケーブルの線密度情報DTO（グループ2）

    Attributes:
        conductor_resistance_per_length (FloatResistancePerLengthDto):
            導線の抵抗線密度
        conductor_inductance_per_length (FloatInductancePerLengthDto):
            導線のインダクタンス線密度
        ground_resistance_length (FloatResistanceLengthDto):
            アース接続の抵抗長積（抵抗×長さ、Ω·m）
        ground_capacitance_per_length (FloatCapacitancePerLengthDto):
            アース接続のキャパシタンス線密度
    """

    conductor_resistance_per_length: FloatResistancePerLengthDto
    conductor_inductance_per_length: FloatInductancePerLengthDto
    ground_resistance_length: FloatResistanceLengthDto
    ground_capacitance_per_length: FloatCapacitancePerLengthDto


@dataclass(frozen=True)
class ItmCableSectionDto:
    """ケーブルセクション情報DTO

    個々のケーブルセクションの情報を保持するDTO。
    基本情報、線密度情報の2つのグループで構成される。

    Attributes:
        basic_info (ItmCableBasicDto): ケーブルセクションの基本情報（グループ1）
        line_density_info (ItmCableLineDensityDto): ケーブルセクションの線密度情報（グループ2）
    """

    basic_info: ItmCableBasicDto
    line_density_info: ItmCableLineDensityDto

    @property
    def name(self) -> CableSectionName:
        """ケーブルセクション名を取得する。

        Returns:
            CableSectionName: ケーブルセクション名（basic.name）
        """
        return self.basic_info.name


class ItmCableSectionDtos(BaseEntityDto[ItmCableSectionDto]):
    """ケーブルセクション情報DTOのコレクションDTOクラス

    複数のケーブルセクション情報DTOを管理するコレクションクラス。
    """

    def __init__(self, objects: list[ItmCableSectionDto]) -> None:
        """
        初期化

        Args:
            objects (list[ItmCableSectionDto]): 初期のItmCableSectionDtoオブジェクトリスト
        """
        super().__init__(objects=objects, attribute_name="name")


@dataclass(frozen=True)
class ItmCableImmittanceDto:
    """ケーブル回路のインピーダンス・アドミタンス情報DTO

    π型ケーブル等価回路における導線およびアース接続の
    インピーダンス・アドミタンスを表現するDTO。
    各辞書のキーは π 型（shunt 2 点・直列導体 1 本）の構成を表す。

    Attributes:
        conductor_model (CableConductorModelDto): 導線回路モデルタイプ。
        conductor_impedance (dict[PieCableConductorKey, ArrayComplexImpedanceDto]):
            導線のインピーダンスの辞書。
            現在の実装では、π型回路の場合に以下のキーを持つことを前提とする:
                - PieCableConductorKey.SINGLE: 上流と下流の間の導線（電流が流れる導体）の
                    インピーダンス [Ω]。抵抗とインダクタの直列接続として表現される。
        conductor_admittance (dict[PieCableConductorKey, ArrayComplexAdmittanceDto]):
            導線のアドミタンスの辞書。
            現在の実装では、π型回路の場合に以下のキーを持つことを前提とする:
                - PieCableConductorKey.SINGLE: 導線のアドミタンス [S]
        ground_impedance (dict[PieCableGroundKey, ArrayComplexImpedanceDto]):
            アース接続のインピーダンスの辞書。
            現在の実装では、π型回路の場合に以下のキーを持つことを前提とする:
                - PieCableGroundKey.UPSTREAM: 上流側アースインピーダンス [Ω]。
                    上流側のアース接続における抵抗とキャパシタンスの並列接続の
                    インピーダンスを表す。
                - PieCableGroundKey.DOWNSTREAM: 下流側アースインピーダンス [Ω]。
                    下流側のアース接続における抵抗とキャパシタンスの並列接続の
                    インピーダンスを表す。
        ground_admittance (dict[PieCableGroundKey, ArrayComplexAdmittanceDto]):
            アース接続のアドミタンスの辞書。
            現在の実装では、π型回路の場合に以下のキーを持つことを前提とする:
                - PieCableGroundKey.UPSTREAM: 上流側アースアドミタンス [S]。
                    上流側のアース接続における抵抗とキャパシタンスの並列接続の
                    アドミタンスを表す。
                - PieCableGroundKey.DOWNSTREAM: 下流側アースアドミタンス [S]。
                    下流側のアース接続における抵抗とキャパシタンスの並列接続の
                    アドミタンスを表す。
        is_ground_insulated (bool): 完全絶縁フラグ。
            True: 全てのケーブルで ground_resistance_length = inf かつ
            ground_capacitance_per_length = 0
        is_ground_shorted (bool): 地絡フラグ。
            True: 1つ以上のケーブルで ground_resistance_length = 0 または
            ground_capacitance_per_length = inf
        is_conductor_ideal (bool): 理想導体フラグ。
            True: 全てのケーブルで conductor_inductance_per_length = 0 かつ
            conductor_resistance_per_length = 0
    """

    conductor_model: CableConductorModelDto
    conductor_impedance: dict[PieCableConductorKey, ArrayComplexImpedanceDto]
    conductor_admittance: dict[PieCableConductorKey, ArrayComplexAdmittanceDto]
    ground_impedance: dict[PieCableGroundKey, ArrayComplexImpedanceDto]
    ground_admittance: dict[PieCableGroundKey, ArrayComplexAdmittanceDto]
    is_ground_insulated: bool  # 完全絶縁（全ケーブルがR=inf, C=0）
    is_ground_shorted: bool  # 地絡（1つでもR=0 or C=inf）
    is_conductor_ideal: bool  # 導体が理想的（全ケーブルがL=0, R=0）

    def __post_init__(self) -> None:
        """π型ケーブルとして辞書キーの整合性をバリデーションする。

        以下のキー構成を前提とする:

        - conductor_impedance / conductor_admittance:
            keys == {PieCableConductorKey.SINGLE}
        - ground_impedance / ground_admittance:
            keys == {PieCableGroundKey.UPSTREAM, PieCableGroundKey.DOWNSTREAM}
        """
        expected_conductor_keys = frozenset({PieCableConductorKey.SINGLE})
        expected_ground_keys = frozenset(
            {PieCableGroundKey.UPSTREAM, PieCableGroundKey.DOWNSTREAM}
        )

        actual_conductor_imp = frozenset(self.conductor_impedance.keys())
        actual_conductor_adm = frozenset(self.conductor_admittance.keys())
        actual_ground_imp = frozenset(self.ground_impedance.keys())
        actual_ground_adm = frozenset(self.ground_admittance.keys())

        if actual_conductor_imp != expected_conductor_keys:
            raise ValueError(
                "ケーブル（π型）の conductor_impedance のキーが不正です: "
                f"{sorted(k.value for k in actual_conductor_imp)}. "
                f"期待値: {sorted(k.value for k in expected_conductor_keys)}"
            )
        if actual_conductor_adm != expected_conductor_keys:
            raise ValueError(
                "ケーブル（π型）の conductor_admittance のキーが不正です: "
                f"{sorted(k.value for k in actual_conductor_adm)}. "
                f"期待値: {sorted(k.value for k in expected_conductor_keys)}"
            )
        if actual_ground_imp != expected_ground_keys:
            raise ValueError(
                "ケーブル（π型）の ground_impedance のキーが不正です: "
                f"{sorted(k.value for k in actual_ground_imp)}. "
                f"期待値: {sorted(k.value for k in expected_ground_keys)}"
            )
        if actual_ground_adm != expected_ground_keys:
            raise ValueError(
                "ケーブル（π型）の ground_admittance のキーが不正です: "
                f"{sorted(k.value for k in actual_ground_adm)}. "
                f"期待値: {sorted(k.value for k in expected_ground_keys)}"
            )


@dataclass(frozen=True)
class ItmCableModelDto:
    """ケーブルの中間DTOクラス

    π型回路モデルを想定し、相モデルを表現する。
    個々のケーブルの情報と、実計算で使用するインピーダンス・アドミタンス情報を保持する。

    Attributes:
        name (CableName | None): InputDto 由来の個体名（SINGLE/TOP/BOTTOM 等）。
            build_model が CableDto.name をそのまま保持する。
            None は擬似ケーブル（cable=None、完全導体かつ完全絶縁）の場合のみ。
            擬似ケーブルは個体としての名前を持たないため、ここだけ None を許容する。
        cable_info (ItmCableSectionDtos | None): 個々のケーブルセクションの情報DTOのコレクション。
            各ケーブルセクションの基本情報、線密度情報を含む。
            オプショナルな理由:
            - ケーブルが存在しない場合（cable=None）、完全導体かつ完全絶縁の擬似ケーブルモデルが
              作成される。この場合、ケーブル情報は存在しないため、cable_infoはNoneとなる。
            - 擬似ケーブルモデルは、ケーブルがない状態を物理的に表現するために使用され、
              システムモデル構築時にケーブルの影響が無視され、システムイミタンスは
              誘導電動機のイミタンスそのものになる。
        cable_immittance (ItmCableImmittanceDto): 実計算で使用する
            インピーダンス・アドミタンス情報DTO。
            π型回路モデルにおける導線とアース接続のインピーダンス・アドミタンスを表す。
    """

    name: CableName | None
    cable_info: ItmCableSectionDtos | None
    cable_immittance: ItmCableImmittanceDto
