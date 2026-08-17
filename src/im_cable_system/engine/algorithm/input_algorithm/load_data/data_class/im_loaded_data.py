"""誘導電動機（IM）シリーズの中間表現データクラス。

入力ファイル（シリーズ選択ファイル・``im_series_catalog.yaml``）から
parse した結果を、engine 層 DTO に依存せずに保持する。
``im_series_catalog.yaml`` のエントリ構造に沿って、``nameplate`` と
``primary`` / ``excitation`` / ``secondary``（または ``secondary_inner`` /
``secondary_outer``）をサブデータクラスに展開する。

DTO 化（``ImConnectionType`` / ``ImCircuitType`` / ``ImCageMultiplicityType``
/ ``ImPrimaryModelType`` 等の enum 解決、``Float*Dto`` への詰め替え）は
``assemble_input_dto`` 層で行う。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ImNameplateLoadedData:
    """名盤情報（``nameplate`` ブロックに対応）。

    Attributes:
        voltage: 名盤電圧の値。
        voltage_unit: ``voltage`` の単位（例: ``"V"``）。
        current: 名盤電流の値。
        current_unit: ``current`` の単位（例: ``"A"``）。
        power: 名盤機械出力の値。
        power_unit: ``power`` の単位（例: ``"W"``）。
        frequency: 名盤周波数の値。
        frequency_unit: ``frequency`` の単位（例: ``"Hz"``）。
    """

    voltage: float
    voltage_unit: str
    current: float
    current_unit: str
    power: float
    power_unit: str
    frequency: float
    frequency_unit: str


@dataclass(frozen=True)
class ImBranchLoadedData:
    """誘導電動機の 1 枝分（``primary`` / ``excitation`` / ``secondary``
    系のブランチ）の中間表現。

    Notes:
        ``model_params`` は YAML の ``model.params`` 配列（各要素は
        ``{"name": str, "value": float}`` の ``Mapping``）を、ロード時に
        ``{name: value}`` のフラット辞書に正規化したもの。パラメータが
        無いモデル（例: ``BASIC``）では空辞書。

    Attributes:
        model: ブランチのモデル名（例: ``"BASIC"`` /
            ``"SLIP_DEPENDENT_LEAKAGE_SATURATION_V1"``）。
        model_params: モデルパラメータの ``{パラメータ名: 値}`` 辞書。
        resistance: ブランチ抵抗の値。
        resistance_unit: ``resistance`` の単位（例: ``"Ω"``）。
        inductance: ブランチインダクタンスの値。
        inductance_unit: ``inductance`` の単位（例: ``"H"``）。
    """

    model: str
    model_params: dict[str, float]
    resistance: float
    resistance_unit: str
    inductance: float
    inductance_unit: str


@dataclass(frozen=True)
class ImLossBranchLoadedData:
    """軸出力控除（摩擦・風損／漂遊負荷損）1 枝分の中間表現。

    ``ImBranchLoadedData`` と異なり ``resistance`` / ``inductance`` を
    持たない（イミタンスを持たないサブシステムのため。
    docs/model/equations/index.md 参照）。

    Attributes:
        model: モデル名（例: ``"NONE"`` / ``"CONSTANT_V1"``）。
        model_params: モデルパラメータの ``{パラメータ名: 値}`` 辞書。
            ``NONE`` では空辞書。
    """

    model: str
    model_params: dict[str, float]


@dataclass(frozen=True)
class ImLoadedData:
    """誘導電動機 1 系列分の中間表現（``im_series`` の 1 エントリに対応）。

    Notes:
        単一かご（``cage_multiplicity = "SINGLE_CAGE"``、YAML 上は省略可）
        の場合は ``secondary`` が必須、``secondary_inner`` /
        ``secondary_outer`` は ``None``。
        二重かご（``cage_multiplicity = "DOUBLE_CAGE"``）の場合は
        ``secondary_inner`` と ``secondary_outer`` が必須、``secondary``
        は ``None``。整合チェックはローダー側で行い、アセンブラは本
        データクラスを信頼してよい。

    Attributes:
        name: シリーズ選択ファイル由来の ``im_series_name``
            （``im_series_catalog.yaml`` の参照キー、YAML 上の ``name``）。
        poles: 極数（YAML 上の ``poles``）。
        cage_multiplicity: かご段数（``"SINGLE_CAGE"`` または
            ``"DOUBLE_CAGE"``）。YAML 上で省略されている場合は
            ``"SINGLE_CAGE"`` を埋める。
        connection_type: 結線種別（``"STAR"`` または ``"DELTA"``）。
        circuit_type: 等価回路種別（``"L"`` または ``"T"``）。
        nameplate: 名盤情報の中間表現。
        primary: 一次側ブランチの中間表現。
        excitation: 励磁ブランチの中間表現。
        secondary: 単一かご時の二次側ブランチ。二重かご時は ``None``。
        secondary_inner: 二重かご時の内側二次ブランチ。単一かご時は
            ``None``。
        secondary_outer: 二重かご時の外側二次ブランチ。単一かご時は
            ``None``。
        friction_windage: 摩擦・風損の中間表現。必須（primary / excitation /
            secondary と同格の枠）。ゼロ損失は ``model="NONE"``、
            ``model_params={}`` として明示する。
        stray_load: 漂遊負荷損の中間表現。必須。規約は ``friction_windage``
            と同じ。
    """

    name: str
    poles: int
    cage_multiplicity: str
    connection_type: str
    circuit_type: str
    nameplate: ImNameplateLoadedData
    primary: ImBranchLoadedData
    excitation: ImBranchLoadedData
    secondary: ImBranchLoadedData | None
    secondary_inner: ImBranchLoadedData | None
    secondary_outer: ImBranchLoadedData | None
    friction_windage: ImLossBranchLoadedData
    stray_load: ImLossBranchLoadedData
