"""ドメイン物理計算（公開窓口・機器特性）。

このパッケージは、IM＋ケーブル系のドメインに固有な物理計算ロジックを提供する。
入出力はすべて DTO（``physical_quantity`` DTO 等）であり、純粋計算ロジックの集約点となる。

公開窓口の分担:
    - **機器特性計算・軸出力控除**: 本ファイル（``physics`` 直下）。
      効率・力率・トルク・回転速度などの単発関数（``characteristic``）と、
      軸出力控除（摩擦・風損／漂遊負荷損）の損失計算（``shaft_output_deduction``）
      を再エクスポートする。
    - **電気計算**: ``physics.electrical`` の ``__init__.py``。
      キルヒホッフ・オーム・インピーダンス・電力等の電気計算群を再エクスポートする。

層外からの import:
    >>> from im_cable_system.engine.domain.physics import calculate_efficiency
    >>> from im_cable_system.engine.domain.physics.electrical import (
    ...     calculate_current_from_voltage_and_impedance,
    ... )
"""

from im_cable_system.engine.domain.physics.characteristic import (
    calculate_efficiency,
    calculate_power_factor,
    calculate_rotational_speed,
    calculate_torque,
)
from im_cable_system.engine.domain.physics.shaft_output_deduction import (
    calculate_constant_friction_windage_loss,
    calculate_quadratic_stray_load_loss,
)

__all__ = [
    "calculate_constant_friction_windage_loss",
    "calculate_efficiency",
    "calculate_power_factor",
    "calculate_quadratic_stray_load_loss",
    "calculate_rotational_speed",
    "calculate_torque",
]
