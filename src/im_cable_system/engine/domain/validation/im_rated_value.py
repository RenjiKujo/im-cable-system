"""定格値に対する検証ロジック（ドメイン層）。

このモジュールは、電流・電圧が定格値に対して妥当であるかを検証する処理を提供します。

特徴:
    - 入力・出力にはDTO（特に`electrical` DTO）を用いる
    - アルゴリズム層から利用される純粋検証ロジックを集約する
    - 検証結果はValidationResultDtoを返す（例外を発生させない）
"""

from __future__ import annotations

import numpy as np

from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexCurrentDto,
    ArrayComplexVoltageDto,
)
from im_cable_system.engine.shared.dto.generic.validation import (
    ValidationResultDto,
)


def validate_voltage_range(
    voltage: ArrayComplexVoltageDto,
    rated_voltage: float,
    tolerance: float = 0.1,
) -> ValidationResultDto:
    """電圧レンジを検証する。

    電圧が定格値や設計上の許容範囲に収まっているかを検証する。

    検証内容:
        - 電圧の大きさ（絶対値）が rated_voltage * (1 - tolerance) 以上
        - 電圧の大きさ（絶対値）が rated_voltage * (1 + tolerance) 以下

    Args:
        voltage: 電圧DTO。
        rated_voltage: 定格電圧（基本単位: V）。
        tolerance: 電圧の許容誤差（相対誤差、デフォルト: 0.1 = 10%）。
            NEMA MG-1標準に基づく一般的な許容範囲（±10%）。

    Returns:
        ValidationResultDto: 検証結果。検証が失敗した場合、is_valid=Falseとなり、
            詳細なメッセージが含まれる。

    Notes:
        - 定格値は基本単位（V）で指定する。
        - 複素電圧の大きさ（絶対値）で比較を行う。
        - NEMA MG-1標準では、誘導電動機の電圧許容範囲は±10%と規定されている。
        - 定格電圧が0以下の場合は、is_valid=Falseを返す。
    """
    # 定格値の検証
    if rated_voltage <= 0:
        return ValidationResultDto(
            is_valid=False,
            message=f"定格電圧は正の値である必要があります: {rated_voltage}",
        )

    # 基本単位に変換
    voltage_base = voltage.to_base_unit()

    # 電圧の大きさ（絶対値）を取得
    voltage_magnitude = np.abs(voltage_base.value)

    # 許容範囲の計算（上下限を設定）
    voltage_min = rated_voltage * (1.0 - tolerance)
    voltage_max = rated_voltage * (1.0 + tolerance)

    # 電圧の範囲検証（下限）
    voltage_low_violation_mask = voltage_magnitude < voltage_min

    if np.any(voltage_low_violation_mask):
        voltage_shape = voltage_magnitude.shape
        # 全要素中の最小電圧は必ず下限を下回る（=違反要素）ため、
        # 元配列に対する argmin をそのまま元 shape の index に展開できる。
        min_voltage_idx = np.unravel_index(
            np.argmin(voltage_magnitude),
            voltage_shape,
        )
        min_voltage = voltage_magnitude[min_voltage_idx]
        violation_count = int(np.sum(voltage_low_violation_mask))
        total_count = int(voltage_magnitude.size)

        return ValidationResultDto(
            is_valid=False,
            message=(
                f"電圧が許容範囲外です（定格の{100 * (1.0 - tolerance):.0f}%未満です）。"
                f"定格電圧: {rated_voltage} V, "
                f"許容最小電圧: {voltage_min:.2f} V, "
                f"最小電圧: {min_voltage:.2f} V, "
                f"違反箇所数: {violation_count}/{total_count}, "
                f"最小電圧のインデックス: {min_voltage_idx}"
            ),
        )

    # 電圧の範囲検証（上限）
    voltage_high_violation_mask = voltage_magnitude > voltage_max

    if np.any(voltage_high_violation_mask):
        voltage_shape = voltage_magnitude.shape
        # 全要素中の最大電圧は必ず上限を超える（=違反要素）ため、
        # 元配列に対する argmax をそのまま元 shape の index に展開できる。
        max_voltage_idx = np.unravel_index(
            np.argmax(voltage_magnitude),
            voltage_shape,
        )
        max_voltage = voltage_magnitude[max_voltage_idx]
        violation_count = int(np.sum(voltage_high_violation_mask))
        total_count = int(voltage_magnitude.size)

        return ValidationResultDto(
            is_valid=False,
            message=(
                f"電圧が許容範囲外です（定格の{100 * (1.0 + tolerance):.0f}%を超えています）。"
                f"定格電圧: {rated_voltage} V, "
                f"許容最大電圧: {voltage_max:.2f} V, "
                f"最大電圧: {max_voltage:.2f} V, "
                f"違反箇所数: {violation_count}/{total_count}, "
                f"最大電圧のインデックス: {max_voltage_idx}"
            ),
        )

    # 検証成功
    return ValidationResultDto(
        is_valid=True,
        message="",
    )


def validate_current_range(
    current: ArrayComplexCurrentDto,
    rated_current: float,
    tolerance: float = 6.0,
) -> ValidationResultDto:
    """電流レンジを検証する。

    電流が定格値や設計上の許容範囲に収まっているかを検証する。

    検証内容:
        - 電流の大きさ（絶対値）が rated_current * (1 + tolerance) 以下
        - 定格より低い値は許容される（下限チェックなし）

    Args:
        current: 電流DTO。
        rated_current: 定格電流（基本単位: A）。
        tolerance: 電流の許容誤差（相対誤差、デフォルト: 6.0 = 600% = 7倍）。
            誘導電動機の始動電流（inrush current）は一般的に定格電流の4-8倍であるため、
            安全マージンを考慮して7倍（tolerance=6.0）をデフォルトとする。

    Returns:
        ValidationResultDto: 検証結果。検証が失敗した場合、is_valid=Falseとなり、
            詳細なメッセージが含まれる。

    Notes:
        - 定格値は基本単位（A）で指定する。
        - 複素電流の大きさ（絶対値）で比較を行う。
        - 定格より低い値は問題ないため、下限チェックは行わない。
        - 誘導電動機の始動電流は一般的に定格電流の4-8倍（ロックドローター時）である。
          直接始動の場合、8-10倍が典型的な値となる。
        - 定格電流が0以下の場合は、is_valid=Falseを返す。
    """
    # 定格値の検証
    if rated_current <= 0:
        return ValidationResultDto(
            is_valid=False,
            message=f"定格電流は正の値である必要があります: {rated_current}",
        )

    # 基本単位に変換
    current_base = current.to_base_unit()

    # 電流の大きさ（絶対値）を取得
    current_magnitude = np.abs(current_base.value)

    # 許容範囲の計算（上限のみ、定格より低い値は許容される）
    current_max = rated_current * (1.0 + tolerance)

    # 電流の範囲検証
    current_violation_mask = current_magnitude > current_max

    if np.any(current_violation_mask):
        current_shape = current_magnitude.shape
        # 全要素中の最大電流は必ず上限を超える（=違反要素）ため、
        # 元配列に対する argmax をそのまま元 shape の index に展開できる。
        max_current_idx = np.unravel_index(
            np.argmax(current_magnitude),
            current_shape,
        )
        max_current = current_magnitude[max_current_idx]
        current_multiple = max_current / rated_current
        violation_count = int(np.sum(current_violation_mask))
        total_count = int(current_magnitude.size)

        return ValidationResultDto(
            is_valid=False,
            message=(
                f"電流が許容範囲外です（定格の{100 * (1.0 + tolerance):.0f}% = {1.0 + tolerance:.1f}倍を超えています）。"
                f"定格電流: {rated_current} A, "
                f"許容最大電流: {current_max:.2f} A ({1.0 + tolerance:.1f}倍), "
                f"最大電流: {max_current:.2f} A ({current_multiple:.1f}倍), "
                f"違反箇所数: {violation_count}/{total_count}, "
                f"最大電流のインデックス: {max_current_idx}"
            ),
        )

    # 検証成功
    return ValidationResultDto(
        is_valid=True,
        message="",
    )
