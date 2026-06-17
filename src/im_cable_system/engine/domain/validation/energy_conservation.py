"""エネルギー保存則の検証ロジック（ドメイン層）。

このモジュールは、エネルギー保存則を満たしているかの検証処理を提供します。

特徴:
    - 入力・出力にはDTO（特に`electrical` DTO）を用いる
    - アルゴリズム層から利用される純粋検証ロジックを集約する
    - 検証結果はValidationResultDtoを返す（例外を発生させない）
"""

from __future__ import annotations

import numpy as np

from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexPowerDto,
)
from im_cable_system.engine.shared.dto.generic.validation import (
    ValidationResultDto,
)


def validate_energy_conservation(
    input_power: ArrayComplexPowerDto,
    output_power: ArrayComplexPowerDto,
    loss_power: ArrayComplexPowerDto,
    *,
    tolerance: float = 1e-6,
    eps: float,
) -> ValidationResultDto:
    """エネルギー保存則を検証する。

    入力電力 = 出力電力 + 損失電力 が許容誤差内で成り立つことを検証する。
    検証結果はValidationResultDtoを返す（例外を発生させない）。

    検証式: |input_power - (output_power + loss_power)| <= tolerance * |input_power|

    複素電力の実部（有効電力）と虚部（無効電力）の両方が保存されることを検証します。

    Args:
        input_power: 入力電力DTO。
        output_power: 出力電力DTO。
        loss_power: 損失電力DTO。
        tolerance: 許容誤差（相対誤差、デフォルト: 1e-6）。これは数値ガードの
            ``eps`` とは別契約の「判定しきい値」であり、Domain 内で既定値を
            持ってよい。
        eps: 極小ガードのしきい値（キーワード必須）。アルゴリズム層が Config の
            ``numerical_guard_config.eps`` から注入する。Domain 側で既定値を
            持たない。入力電力が ``abs(x) <= eps`` のとき絶対誤差で検証する。

    Returns:
        ValidationResultDto: 検証結果。検証が失敗した場合、is_valid=Falseとなり、
            詳細なメッセージが含まれる。

    Notes:
        - 入力電力が非常に小さい場合（eps以下）は、絶対誤差で検証する。
        - 複素電力のまま比較を行い、実部（有効電力）と虚部（無効電力）の両方が保存されることを検証する。
        - 配列形状が一致しない場合は、is_valid=Falseを返す。
    """
    # 基本単位に変換
    input_base = input_power.to_base_unit()
    output_base = output_power.to_base_unit()
    loss_base = loss_power.to_base_unit()

    # 配列形状の確認
    input_shape = input_base.value.shape
    output_shape = output_base.value.shape
    loss_shape = loss_base.value.shape

    if input_shape != output_shape or input_shape != loss_shape:
        return ValidationResultDto(
            is_valid=False,
            message=(
                "電力配列の形状が一致しません: "
                f"input shape={input_shape}, "
                f"output shape={output_shape}, "
                f"loss shape={loss_shape}"
            ),
        )

    # エネルギー保存則の検証
    # 複素電力のまま比較し、実部（有効電力）と虚部（無効電力）の両方が保存されることを検証
    right_side = output_base.value + loss_base.value
    diff = input_base.value - right_side

    # 複素数の差分の大きさ（絶対値）を計算
    diff_magnitude = np.abs(diff)
    input_magnitude = np.abs(input_base.value)

    # 入力電力が非常に小さい場合は絶対誤差で検証
    is_small_input = input_magnitude <= eps

    # 相対誤差の計算（入力が小さい場合は0として扱う）
    relative_error = np.where(
        is_small_input,
        diff_magnitude,  # 絶対誤差
        diff_magnitude / np.maximum(input_magnitude, eps),  # 相対誤差
    )

    # 許容誤差を超える要素を検出
    violation_mask = relative_error > tolerance

    if np.any(violation_mask):
        # 違反箇所の詳細情報を取得。
        # 全要素中の最大誤差は必ず tolerance を超える（=違反要素）ため、
        # 元配列に対する argmax をそのまま元 shape の index に展開できる。
        # （`relative_error[violation_mask]` の圧縮後 index を元 shape に渡すと
        #   ずれるため、圧縮せずに argmax を取る。）
        max_error_idx = np.unravel_index(np.argmax(relative_error), input_shape)
        max_error = relative_error[max_error_idx]
        violation_count = int(np.sum(violation_mask))
        total_count = int(input_magnitude.size)

        return ValidationResultDto(
            is_valid=False,
            message=(
                f"エネルギー保存則の検証に失敗しました。"
                f"許容誤差: {tolerance}, 最大誤差: {max_error:.2e}, "
                f"違反箇所数: {violation_count}/{total_count}, "
                f"最大誤差のインデックス: {max_error_idx}"
            ),
        )

    # 検証成功
    return ValidationResultDto(
        is_valid=True,
        message="",
    )
