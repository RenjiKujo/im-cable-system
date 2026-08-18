"""軸出力控除（摩擦・風損／漂遊負荷損）を軸出力に反映する共通処理。

単一かご (`single_cage_im_power_calculator.py`) ・二重かご
(`double_cage_im_power_calculator.py`) の両方から呼ばれる、かご重数に
依らない共通処理。両ファイルへのコピペを避けるためにここへ切り出す。

``calculate_im_power`` 内部の共有ヘルパーであり、層外へは公開しない
（本パッケージの公開窓口 ``__init__.py`` の ``__all__`` には載せない）。
軸出力控除そのものの公開窓口は
``calculate_im_shaft_output_deduction`` 側で、本モジュールはその 2 つの
Factory を呼び分けて電力 DTO を組み立てるだけの薄い層である。
"""

from __future__ import annotations

from im_cable_system.engine.algorithm.execute_algorithm.simulate.power.calculate_im_shaft_output_deduction import (  # noqa: E501
    FrictionWindageLossCalculatorFactory,
    StrayLoadLossCalculatorFactory,
)
from im_cable_system.engine.domain.physics.electrical import subtract_power
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexCurrentDto,
    ArrayComplexPowerDto,
)
from im_cable_system.engine.shared.dto.itm import ItmImModelDto


def apply_shaft_output_deduction(
    *,
    im_model: ItmImModelDto,
    secondary_load_total: ArrayComplexPowerDto,
    secondary_current_total: ArrayComplexCurrentDto,
    config: IConfig,
    logger: ILogger,
) -> tuple[ArrayComplexPowerDto, ArrayComplexPowerDto, ArrayComplexPowerDto]:
    """摩擦・風損／漂遊負荷損を計算し、二次負荷電力から引いた軸出力を返す。

    計算式（`docs/model/equations/im_friction_windage.md` /
    `docs/model/equations/im_stray_load.md`）:
        output_power = secondary_load_total - friction_windage_loss_power
                       - stray_load_loss_power

    両損失とも ``im_model.friction_windage_model`` / ``im_model.stray_load_model``
    が ``NONE`` のときはゼロ配列を返す計算器が選ばれるため、既定では
    ``output_power == secondary_load_total``（既存の数値挙動を変えない）。

    Args:
        im_model: IMモデルDTO。
        secondary_load_total: 二次負荷電力の合計
            （単一かごは唯一の枝、二重かごは INNER+OUTER の合計）。
        secondary_current_total: 二次側合計電流（漂遊負荷損の基準電流）。
        config: 設定オブジェクト。
        logger: ロガーオブジェクト。

    Returns:
        tuple[ArrayComplexPowerDto, ArrayComplexPowerDto, ArrayComplexPowerDto]:
            ``(output_power, friction_windage_loss_power, stray_load_loss_power)``。
    """
    reference_shape = secondary_load_total.get_shape()

    friction_windage_calculator = FrictionWindageLossCalculatorFactory.create(
        model_type=im_model.friction_windage_model.name,
        config=config,
        logger=logger,
    )
    friction_windage_loss_power = friction_windage_calculator.calculate(
        im_model=im_model,
        reference_shape=reference_shape,
    )

    stray_load_calculator = StrayLoadLossCalculatorFactory.create(
        model_type=im_model.stray_load_model.name,
        config=config,
        logger=logger,
    )
    stray_load_loss_power = stray_load_calculator.calculate(
        im_model=im_model,
        secondary_current=secondary_current_total,
    )

    output_power = subtract_power(
        power1=subtract_power(
            power1=secondary_load_total, power2=friction_windage_loss_power
        ),
        power2=stray_load_loss_power,
    )
    return output_power, friction_windage_loss_power, stray_load_loss_power
