"""ドメイン状態判定の述語（公開窓口）。

このパッケージは、DTO の状態を分類するための **bool 述語** を提供する。
入力 DTO に対して bool を返すだけの軽量な判定関数の集約点となる。

``validation`` との違い:
    - ``predicate``: 戻り値は ``bool``。状態分類・分岐用。
    - ``validation``: 戻り値は ``ValidationResultDto``。
      契約検証・違反箇所の詳細レポート用。

含まれるモジュール:
    - ``cable``: ケーブルの状態判定。
      完全絶縁・地絡・理想導体・導体モデルの電流依存有無。
    - ``im``: 誘導電動機の状態判定。
      結線方式（DELTA/STAR）・イミタンスモデルの電流依存有無。

層外からの import:
    >>> from im_cable_system.engine.domain.predicate import (
    ...     check_all_ground_insulated,
    ...     has_current_dependent_conductor_model,
    ...     has_current_dependent_immittance_model,
    ...     is_delta,
    ... )
"""

from im_cable_system.engine.domain.predicate.cable import (
    check_all_conductor_ideal,
    check_all_ground_insulated,
    check_any_ground_shorted,
    has_current_dependent_conductor_model,
)
from im_cable_system.engine.domain.predicate.im import (
    has_current_dependent_immittance_model,
    is_delta,
    is_star,
)

__all__ = [
    "check_all_conductor_ideal",
    "check_all_ground_insulated",
    "check_any_ground_shorted",
    "has_current_dependent_conductor_model",
    "has_current_dependent_immittance_model",
    "is_delta",
    "is_star",
]
