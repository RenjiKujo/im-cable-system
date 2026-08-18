"""IM 軸出力控除（摩擦・風損／漂遊負荷損）計算器（公開窓口）。

「軸出力控除」は損失分類の総称ではなく、**二次負荷支路電力から引いて軸出力を
得る**という役割で括った名前である。規格（IEC 60034-2-1 / IEEE 112）の損失分類
では機械損は摩擦・風損のみを指し、漂遊負荷損は追加負荷損として別枠に置かれる。
両者を同じ親の下に置くのは軸出力に対する役割が同じだからであり、漂遊負荷損を
機械損と呼ぶためではない。

サブパッケージ ``friction_windage`` / ``stray_load`` はそれぞれ独立した
Strategy + Factory を持つ（`docs/model/equations/index.md` の「イミタンスを
持たない2サブシステム」を参照）。境界をまたぐ利用（同一責務ツリー外）は
本ファイルの ``__all__`` 経由に限る。

``calculate_im_power`` の ``apply_shaft_output_deduction.py`` は本窓口から
Factory を import して両損失を計算し、``apply_shaft_output_deduction``
として上位（single/double_cage_im_power_calculator）へ公開する。
"""

from im_cable_system.engine.algorithm.execute_algorithm.simulate.power.calculate_im_shaft_output_deduction.friction_windage.factory_friction_windage_loss_calculator import (  # noqa: E501
    FrictionWindageLossCalculatorFactory,
)
from im_cable_system.engine.algorithm.execute_algorithm.simulate.power.calculate_im_shaft_output_deduction.friction_windage.i_friction_windage_loss_calculator import (  # noqa: E501
    IFrictionWindageLossCalculator,
)
from im_cable_system.engine.algorithm.execute_algorithm.simulate.power.calculate_im_shaft_output_deduction.stray_load.factory_stray_load_loss_calculator import (  # noqa: E501
    StrayLoadLossCalculatorFactory,
)
from im_cable_system.engine.algorithm.execute_algorithm.simulate.power.calculate_im_shaft_output_deduction.stray_load.i_stray_load_loss_calculator import (  # noqa: E501
    IStrayLoadLossCalculator,
)

__all__ = [
    "FrictionWindageLossCalculatorFactory",
    "IFrictionWindageLossCalculator",
    "StrayLoadLossCalculatorFactory",
    "IStrayLoadLossCalculator",
]
