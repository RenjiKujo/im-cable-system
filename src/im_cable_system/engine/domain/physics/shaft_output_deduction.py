"""軸出力控除（摩擦・風損／漂遊負荷損）計算ロジック（ドメイン層）。

このモジュールは、IM の軸出力を計算するために二次負荷支路電力から差し引く
軸出力控除の純粋計算ロジックを提供する。

対応するモデルの数式・記号の定義（正）は
``docs/model_equations/im_friction_windage.md`` /
``docs/model_equations/im_stray_load.md``。

特徴:
    - 入力・出力はすべて DTO（``physical_quantity`` DTO）。
    - 両損失とも**有効電力のみ**（虚部は持たない）。虚部を含む
      ``ArrayComplexPowerDto`` への変換は呼び出し側（algorithm 層の
      計算器）が行う。
    - ``ImSeriesDto.nameplate_power`` は 3 相合計であるため、ここで計算する
      損失も 3 相合計になる（「1 相で計算して 3 相へ変換」の経路を通らない）。
    - 分母ガード（``eps``）は Config 由来の値をアルゴリズム層が注入する。
      Domain 側で既定値・共通定数を持たない（他の domain/physics 関数と同じ方針）。
"""

from __future__ import annotations

import numpy as np

from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayActivePowerDto,
    ArrayComplexCurrentDto,
    FloatActivePowerDto,
    FloatCurrentDto,
)
from im_cable_system.engine.shared.numerical_stability import (
    event_codes,
    record_numerical_stability_event,
)


def calculate_constant_friction_windage_loss(
    *,
    nameplate_power: FloatActivePowerDto,
    k_friction_windage: float,
    reference_shape: tuple[int, ...],
) -> ArrayActivePowerDto:
    """一定の摩擦・風損を計算する（``CONSTANT_V1``）。

    計算式:
        P_FW = k_fw * P_N

    負荷・スリップに依存せず一定なので、``reference_shape`` へブロードキャスト
    した定数配列を返す。

    Args:
        nameplate_power: 銘牌電力 [W]（3相合計、``ImSeriesDto.nameplate_power``）。
        k_friction_windage: 摩擦・風損係数（無次元、定格入力に対する比率）。
        reference_shape: 出力配列の形状（``ArrayLayoutDto.get_reference_shape()``）。

    Returns:
        ArrayActivePowerDto: 摩擦・風損配列 [W]（``reference_shape`` と同じ形状）。
    """
    nameplate_power_w = nameplate_power.to_base_unit().get_value()
    loss_value = np.full(
        reference_shape,
        k_friction_windage * nameplate_power_w,
        dtype=np.float64,
    )
    return ArrayActivePowerDto(value=loss_value, unit="W")


def calculate_quadratic_stray_load_loss(
    *,
    nameplate_power: FloatActivePowerDto,
    nameplate_current: FloatCurrentDto,
    secondary_current: ArrayComplexCurrentDto,
    k_stray_load: float,
    eps: float,
) -> ArrayActivePowerDto:
    """二次電流比の2乗に比例する漂遊負荷損を計算する（``CURRENT_DEPENDENT_QUADRATIC_V1``）。

    計算式:
        P_stray = k_str * P_N * r_I2^2,  r_I2 = |I2| / I_N

    基準電流には二次側合計電流（``get_secondary_total_current()`` で得た値）を
    使う。無負荷（s=0）で二次電流が 0 になるため、この損失も無負荷で 0 になる
    「負荷」損として振る舞う。

    Args:
        nameplate_power: 銘牌電力 [W]（3相合計、``ImSeriesDto.nameplate_power``）。
        nameplate_current: 銘牌電流 [A]（``ImSeriesDto.nameplate_current``）。
        secondary_current: 二次側合計電流配列 [A]。
        k_stray_load: 漂遊負荷損係数（無次元、定格入力に対する比率）。
        eps: 近接ゼロ判定のしきい値（Config 由来）。``abs(I_N) <= eps`` の
            ときは正規化せず ``r_I2 = |I2|`` にフォールバックする
            （``docs/conventions/4_numerical_robustness.md`` の極小ガード規約）。

    Returns:
        ArrayActivePowerDto: 漂遊負荷損配列 [W]（``secondary_current`` と同じ形状）。

    Raises:
        ValueError: ``secondary_current`` の各要素の値が不正な場合
            （DTO の ``__post_init__`` が担保するためここでは追加検証しない）。

    Note:
        銘牌電流が近接ゼロの要素がある場合、数値安定化イベント
        ``NAMEPLATE_CURRENT_NEAR_ZERO_STRAY_LOAD_NORMALIZATION`` を記録する。
    """
    nameplate_power_w = nameplate_power.to_base_unit().get_value()
    nameplate_current_a = nameplate_current.to_base_unit().get_value()
    secondary_current_magnitude = (
        secondary_current.to_base_unit().get_magnitude()
    )

    # NOTE: eps は他層（Ω 等）と共通の数値ガード閾値を [A] へ暫定流用している
    #     （docs/conventions/4_numerical_robustness.md「単位への注意」）。
    #     極小容量機で銘牌電流が eps と同オーダーになる場合は、専用の eps 分離を
    #     検討すること。
    if abs(nameplate_current_a) <= eps:
        record_numerical_stability_event(
            event_codes.NAMEPLATE_CURRENT_NEAR_ZERO_STRAY_LOAD_NORMALIZATION,
        )
        current_ratio = secondary_current_magnitude
    else:
        current_ratio = secondary_current_magnitude / nameplate_current_a

    loss_value = k_stray_load * nameplate_power_w * current_ratio**2
    return ArrayActivePowerDto(value=loss_value, unit="W")
