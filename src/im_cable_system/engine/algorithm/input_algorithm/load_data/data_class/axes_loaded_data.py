"""評価点軸（slip / frequency / input_line_voltage）の中間表現データクラス。

Forward 系パイプライン（CartesianGrid / OperatingPoints 共通）で用いる
3 軸の 1 次元配列と単位を、engine 層 DTO に依存せずに保持する。
``ArrayLayoutDto`` への詰め替えは ``assemble_input_dto`` 層で行う。

Notes:
    - 3 軸（``slip`` / ``frequency`` / ``input_line_voltage``）は本データ
      クラスの段階では **独立な 1 次元配列** として保持され、長さは異なって
      よい。直積か co-indexed かの意味づけは ``assemble_input_dto`` 段の
      ``reference_axes`` 指定で行う（本データクラスは関与しない）。
    - 値レベルの検証（空配列・有限性・値域）は ``assemble_input_dto`` 段の
      DTO ``__post_init__`` および ``_validate_input_dto`` に寄せる。
      本データクラス自身は ``__post_init__`` を持たない。
    - 単位文字列はファイルから ``strip`` した生値を保持する。単位の
      正規化・検証は ``assemble_input_dto`` 段で行う。
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class AxesLoadedData:
    """評価点軸（スリップ・周波数・入力線間電圧）の中間表現。

    Attributes:
        slip: スリップ配列（``float()`` 変換後の 1 次元 ndarray）。
        frequency: 周波数配列。
        input_line_voltage: 入力線間電圧配列（実数値、複素化はアセンブラ）。
        slip_unit: スリップ列の単位セル文字列。
        frequency_unit: 周波数列の単位セル文字列。
        voltage_unit: 電圧列の単位セル文字列。
    """

    slip: np.ndarray
    frequency: np.ndarray
    input_line_voltage: np.ndarray
    slip_unit: str
    frequency_unit: str
    voltage_unit: str
