"""誘導電動機とケーブルの統合モデル中間DTOクラス。

このモジュールは、IM＋ケーブル系シミュレーションにおける誘導電動機とケーブルの
統合モデルを定義する中間DTOを定義します。
"""

from dataclasses import dataclass

from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexAdmittanceDto,
    ArrayComplexImpedanceDto,
)


@dataclass(frozen=True)
class ItmSystemModelDto:
    """誘導電動機とケーブルの統合システムモデル中間DTOクラス。

    誘導電動機（IM）とケーブルを統合したシステム全体の位相インピーダンスと
    アドミタンスを保持する。

    Attributes:
        system_phase_impedance (ArrayComplexImpedanceDto): システム位相インピーダンス [Ω]。
            誘導電動機とケーブルを統合したシステム全体の位相インピーダンス。
        system_phase_admittance (ArrayComplexAdmittanceDto): システム位相アドミタンス [S]。
            誘導電動機とケーブルを統合したシステム全体の位相アドミタンス。
    """

    system_phase_impedance: ArrayComplexImpedanceDto
    system_phase_admittance: ArrayComplexAdmittanceDto
