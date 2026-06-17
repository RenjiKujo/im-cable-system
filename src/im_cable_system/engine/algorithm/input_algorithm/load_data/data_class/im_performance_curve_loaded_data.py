"""誘導電動機性能曲線の中間表現データクラス。

性能曲線入力ファイルから parse した「メタ（供給条件・極数等）＋曲線表」を、
engine 層 DTO に依存せずに保持する。スリップはファイル列を持たず、
``assemble_input_dto`` 層で ``rotational_speed`` と ``poles`` /
``supply_frequency`` から導出する。``ImPerformanceCurveCatalogDto`` への
詰め替え（``Array*Dto`` 化と物理整合チェック）も
``assemble_input_dto`` 層で行う。

経路ごとの単位解釈:
    本データクラスは Forward / EstimateParams 両経路で共有される中間表現
    であり、観測列（``power`` / ``current`` / ``torque`` / ``power_factor``
    / ``efficiency``）の **値と単位文字列を入力ファイル上の表現のまま raw
    保持** する。比率／絶対の解釈は ``assemble_input_dto`` 層に委ねる。

    - **Forward 経路**: 性能曲線 TSV は「定格非依存のスペック曲線」を扱う
      ため、``power`` / ``current`` / ``torque`` 列は **絶対単位**
      （``W`` / ``A`` / ``Nm`` 等）のみ許容。比率単位 ``-`` / ``%`` は
      共通の ``assemble_input_dto.common.performance_curve_dto_builder``
      が明示的に ``ValueError`` で拒否する。
    - **EstimateParams 経路**: 統合 TSV では名盤と観測曲線が併載される
      ため、``power[-]`` / ``current[%]`` の比率指定が許容される。
      EstimateParams アセンブラが共通ビルダーへ委譲する直前に、
      :func:`...estimate_params.perf_curve_unit_converter
      .convert_ratio_columns_to_absolute` で名盤値を用いた
      ``ratio→absolute`` 変換を行う。
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class ImPerformanceCurveLoadedData:
    """性能曲線 1 件分の中間表現（供給条件 + 1 曲線分の表）。

    Notes:
        - 観測列（``power`` / ``current`` / ``torque`` / ``power_factor``
          / ``efficiency``）は **入力ファイル上の値と単位文字列をそのまま
          raw 保持** する（比率単位 ``[-]`` / ``[%]`` でも、絶対単位
          ``[W]`` / ``[A]`` / ``[Nm]`` でも、本データクラスの段階では
          区別しない）。比率 vs 絶対の解釈と、経路ごとの許容ポリシーは
          ``assemble_input_dto`` 層が担う（モジュール docstring 参照）。
        - ``rotational_speed`` 以外の系列は入力ファイル上で任意のため、
          列が無い場合は対応する配列と単位が ``None`` になる。
          ``power`` / ``current`` / ``power_factor`` / ``efficiency`` /
          ``torque`` のうち少なくとも 1 本があることはパーサ側で
          担保している。
        - ``poles`` はこの性能曲線を生成したモーターの極数（曲線データの
          自己記述メタ）。カタログ ``ImLoadedData.poles`` と通常一致するが、
          概念的には別フィールドである。型は ``float`` で保持し、
          正整数性は ``assemble_input_dto`` 層で検証する。
        - 単位文字列は入力ファイルの単位セルを ``strip()`` した状態の
          まま保持する（``[Hz]`` 等の角括弧除去や妥当性判定はアセンブラ
          側に任せる）。
        - **欠損セル (NaN) の扱い**: 観測列
          （``power`` / ``current`` / ``power_factor`` / ``efficiency``
          / ``torque``）の **空セルは ``np.nan`` として保持** する
          （その点は未観測、後段の fitting / residual 計算で除外する
          意図）。``rotational_speed`` は独立軸として **空セル禁止**
          （空セル行はロード時にスキップされる）。``inf`` はいかなる
          列でも禁止であり、loader 側で ``float()`` 変換時に raise
          される。NaN→0 への変換と mask 配列生成は ``assemble_input_dto``
          段で行い、``ImPerformanceCurveCatalogDto`` の
          ``*_series_mask`` に保持する（Generic ``Array*Dto`` の値は
          finite 必須を維持）。

    Attributes:
        name: 性能曲線名（``im_performance_curve_name``）。
        poles: この性能曲線を生成したモーターの極数（メタブロック由来）。
            ファイル上は整数だが、型は ``float`` で保持する。
        supply_frequency: 供給周波数（メタブロック由来）。
        supply_frequency_unit: 供給周波数の単位セル文字列。
        supply_voltage: 供給電圧。
        supply_voltage_unit: 供給電圧の単位セル文字列。
        rotational_speed: 回転速度配列（曲線テーブル由来、必須、NaN 禁止）。
        rotational_speed_unit: 回転速度の単位セル文字列（必須）。
        power: 機械出力配列（入力ファイル表現のまま、optional、空セルは
            ``np.nan``）。値が比率か絶対値かは ``power_unit`` の単位
            文字列で表現され、解釈は ``assemble_input_dto`` 層が担う。
        power_unit: ``power`` の単位セル文字列（``power`` が ``None`` の
            ときは ``None``）。Forward 経路では ``W`` / ``kW`` / ``MW``
            / ``HP`` のみ許容され、``-`` / ``%`` はアセンブラ側で
            ``ValueError``。EstimateParams 経路では ``-`` も許容され、
            アセンブラ内で名盤値と掛け合わせて ``W`` に変換される。
        current: 電流配列（入力ファイル表現のまま、optional、空セルは
            ``np.nan``）。値が比率か絶対値かは ``current_unit`` の
            単位文字列で表現される。
        current_unit: ``current`` の単位セル文字列（``current`` が
            ``None`` のときは ``None``）。Forward 経路では ``A`` /
            ``kA`` / ``mA`` のみ許容され、``-`` / ``%`` はアセンブラ側
            で ``ValueError``。EstimateParams 経路では ``%`` も許容
            され、アセンブラ内で名盤値と掛け合わせて ``A`` に変換される。
        power_factor: 力率配列（optional、空セルは ``np.nan``）。
        power_factor_unit: 力率の単位セル文字列（``power_factor`` が
            ``None`` のときは ``None``）。
        efficiency: 効率配列（optional、空セルは ``np.nan``）。
        efficiency_unit: 効率の単位セル文字列（``efficiency`` が
            ``None`` のときは ``None``）。
        torque: トルク配列（入力ファイルに列が無いときは ``None``、
            空セルは ``np.nan``）。Forward / EstimateParams いずれの経路
            でも比率単位 ``-`` / ``%`` はアセンブラ側で ``ValueError``
            （torque は名盤との比に意味付けが薄いため、両経路で絶対単位
            のみ許容する）。
        torque_unit: ``torque`` の単位セル文字列（``torque`` が ``None``
            のときは ``None``）。
    """

    name: str
    poles: float
    supply_frequency: float
    supply_frequency_unit: str
    supply_voltage: float
    supply_voltage_unit: str
    rotational_speed: np.ndarray
    rotational_speed_unit: str
    power: np.ndarray | None
    power_unit: str | None
    current: np.ndarray | None
    current_unit: str | None
    power_factor: np.ndarray | None
    power_factor_unit: str | None
    efficiency: np.ndarray | None
    efficiency_unit: str | None
    torque: np.ndarray | None
    torque_unit: str | None
