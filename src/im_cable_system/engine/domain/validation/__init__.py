"""ドメイン契約検証（公開窓口）。

このパッケージは、物理法則・契約に基づく検証ロジックを提供する。
入力 DTO に対して ``ValidationResultDto`` を返し、違反箇所を詳細レポートする。

``predicate`` との違い:
    - ``validation``: 戻り値は ``ValidationResultDto``。
      契約違反の詳細（違反数・違反位置・許容範囲など）を含む。
    - ``predicate``: 戻り値は ``bool``。軽量な状態分類用。

含まれるモジュール:
    - ``im_rated_value``: 電流・電圧の定格範囲検証。
    - ``energy_conservation``: エネルギー保存則検証。

層外からの import:
    >>> from im_cable_system.engine.domain.validation import (
    ...     validate_current_range,
    ...     validate_energy_conservation,
    ...     validate_voltage_range,
    ... )
"""

from im_cable_system.engine.domain.validation.energy_conservation import (
    validate_energy_conservation,
)
from im_cable_system.engine.domain.validation.im_rated_value import (
    validate_current_range,
    validate_voltage_range,
)

__all__ = [
    "validate_current_range",
    "validate_energy_conservation",
    "validate_voltage_range",
]
