"""ケーブル束の中間表現データクラス。

入力ファイル（シリーズ選択ファイル・``cable_series_catalog.yaml``）から
parse した結果を、engine 層 DTO に依存せずに保持する。DTO 化（単位付き
``Float*PerLengthDto`` への詰め替え、``ConductorModelType`` enum 解決等）は
``assemble_input_dto`` 層で行う。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CableSectionLoadedData:
    """ケーブル 1 区間分の中間表現。

    シリーズ選択ファイル由来の参照キー・長さと、``cable_series_catalog.yaml``
    の当該シリーズエントリから取り出した物性（``conductor`` / ``ground``）を
    1 区間分に束ねる。値・単位は文字列／プリミティブで保持し、engine 層の
    ``Float*PerLengthDto`` 等への詰め替えはアセンブラに委ねる。

    Attributes:
        name: ``cable_series_catalog.yaml`` の参照キー
            （シリーズ選択ファイルの ``cable_series_name`` 列から取得）。
        length: 区間長（シリーズ選択ファイル由来）。
        length_unit: ``length`` の単位（``"ft"`` または ``"m"``）。
        shape_type: カタログの ``shape_type``（例: ``"ROUND"`` / ``"FLAT"``）。
        conductor_resistance_per_length: 導体の単位長あたり抵抗値。
        conductor_resistance_per_length_unit: 同単位（例: ``"Ω/m"``）。
        conductor_inductance_per_length: 導体の単位長あたりインダクタンス値。
        conductor_inductance_per_length_unit: 同単位（例: ``"H/m"``）。
        ground_resistance_length: 対地抵抗・長さ積の値。
        ground_resistance_length_unit: 同単位（例: ``"Ω*m"``）。
        ground_capacitance_per_length: 対地静電容量の単位長あたり値。
        ground_capacitance_per_length_unit: 同単位（例: ``"F/m"``）。
    """

    name: str
    length: float
    shape_type: str
    length_unit: str
    conductor_resistance_per_length: float
    conductor_resistance_per_length_unit: str
    conductor_inductance_per_length: float
    conductor_inductance_per_length_unit: str
    ground_resistance_length: float
    ground_resistance_length_unit: str
    ground_capacitance_per_length: float
    ground_capacitance_per_length_unit: str


@dataclass(frozen=True)
class CableLoadedData:
    """ケーブル束（区間群 + 導体モデル）の中間表現。

    ケーブル無し（区間数 0）のシステムでは、本データクラス自体を ``None`` で
    扱う想定（呼び出し側で ``CableLoadedData | None`` として保持する）。

    Notes:
        ``conductor_model_params`` は YAML の ``params`` 配列（各要素は
        ``{"name": str, "value": float}`` の ``Mapping``）を、ロード時に
        ``{name: value}`` のフラット辞書に正規化したもの。
        ``ConductorModelType`` enum およびパラメータ DTO への変換は
        アセンブラ側に委ねる。

    Attributes:
        name: ケーブル束の名前（旧 ``cable_bundle_label`` 相当）。
        sections: 区間ごとの中間表現（区間順）。
        conductor_model: 導体モデル名（YAML の
            ``cable_conductor_models[profile_key].name``、例: ``"BASIC"``）。
        conductor_model_params: 導体モデルのパラメータ
            （``cable_conductor_models[profile_key].params`` を
            ``{パラメータ名: 値}`` の辞書に正規化したもの。
            パラメータが無いモデル（例: ``BASIC``）では ``None``）。
    """

    name: str
    sections: tuple[CableSectionLoadedData, ...]
    conductor_model: str
    conductor_model_params: dict[str, float] | None
