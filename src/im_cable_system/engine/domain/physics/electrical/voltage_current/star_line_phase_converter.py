"""スター結線における線間・相変換計算ロジック（ドメイン層）。

このモジュールは、スター結線における線間電圧・電流と相電圧・電流を
相互変換する処理を提供します。

位相規約（2 系統）:
    - rotation-aware（厳密版）: 線間/相の ±30°（π/6）位相差を厳密に扱う。
        線間電圧 = √3 × 相電圧 × e^(jπ/6)、線電流 = 相電流。
    - balanced（平衡 per-phase 規約）: 線間と相を「同位相」とみなし、大きさ
        換算のみ行う（30° を付与しない）。線間電圧 = √3 × 相電圧、
        線電流 = 相電流。Execute ステージはこちらを用いる。

    平衡正相のみを扱う限り、両規約で大きさ・三相電力・力率は一致する
    （全フェーザ共通の基準回転の差にすぎない）。規約全体の正本は
    `ItmImVoltageCurrentDto` のクラス docstring を参照。

提供する関数:
- line_to_phase_voltage_star: 線間電圧→相電圧変換（スター結線・rotation-aware）
- line_to_phase_voltage_star_balanced: 線間電圧→相電圧変換（スター結線・balanced）
- phase_to_line_voltage_star: 相電圧→線間電圧変換（スター結線・rotation-aware）
- phase_to_line_voltage_star_balanced: 相電圧→線間電圧変換（スター結線・balanced）
- line_to_phase_current_star: 線電流→相電流変換（スター結線）
- phase_to_line_current_star: 相電流→線電流変換（スター結線）
"""

from __future__ import annotations

import numpy as np

from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexCurrentDto,
    ArrayComplexVoltageDto,
)
from im_cable_system.engine.shared.numerical_stability import (
    event_codes,
    record_numerical_stability_event,
)

# √3の値（スター結線の変換係数）
_SQRT_3: float = np.sqrt(3.0)
# 30°進む位相回転係数（+30° = +π/6）
_PHASE_ROTATION: complex = np.exp(1j * np.pi / 6.0)


def line_to_phase_voltage_star(
    line_voltage_dto: ArrayComplexVoltageDto,
    *,
    eps: float,
    max_mag: float,
) -> ArrayComplexVoltageDto:
    """線間電圧を相電圧に変換する（スター結線・rotation-aware）。

    変換式: 相電圧 = 線間電圧 / √3 × e^(-jπ/6)
    位相は30°遅れます（-30°）。

    NOTE: rotation-aware（±30° 厳密）版。Execute ステージは平衡 per-phase 規約
        （`line_to_phase_voltage_star_balanced`）を使うため、本関数は現状
        Execute から呼ばれない。方向（位相）を厳密に扱う Output 出力や、
        将来の不平衡・対称座標法拡張に向けた参照実装として温存する。

    計算方法:
    1. 入力値の極大極小要素を検出
    2. 変換計算を実行
    3. 変換後の極大極小要素をクランプ（位相情報は保持）

    Args:
        line_voltage_dto: 線間電圧DTO（複素数配列、配列の次元数は任意）
        eps: 近接ゼロ判定のしきい値（Config 由来）
        max_mag: 最大の大きさ（Config 由来、通常 1/eps）

    Returns:
        ArrayComplexVoltageDto: 相電圧DTO（単位: V、複素数配列、入力と同じ次元数）

    Warns:
        RuntimeWarning: 電圧値に0または極小の要素がある場合
        RuntimeWarning: 電圧値にinf/極大の要素がある場合
    """
    line_voltage_base = line_voltage_dto.to_base_unit()
    voltage_value = line_voltage_base.value
    base_unit = line_voltage_base.unit

    voltage_magnitude = np.abs(voltage_value)
    too_small = voltage_magnitude <= eps
    too_large = ~np.isfinite(voltage_value) | (voltage_magnitude >= max_mag)

    if np.any(too_small):
        record_numerical_stability_event(event_codes.VOLTAGE_EXTREME_SMALL)
    if np.any(too_large):
        record_numerical_stability_event(event_codes.VOLTAGE_EXTREME_LARGE)

    # 変換計算を先に行う
    phase_voltage_value = voltage_value / _SQRT_3 / _PHASE_ROTATION

    # 変換後の極大極小要素をクランプ
    phase_voltage_phase = np.angle(phase_voltage_value)
    phase_voltage_value = np.where(
        too_small, eps * np.exp(1j * phase_voltage_phase), phase_voltage_value
    )
    phase_voltage_value = np.where(
        too_large,
        max_mag * np.exp(1j * phase_voltage_phase),
        phase_voltage_value,
    )

    return ArrayComplexVoltageDto(value=phase_voltage_value, unit=base_unit)


def line_to_phase_voltage_star_balanced(
    line_voltage_dto: ArrayComplexVoltageDto,
    *,
    eps: float,
    max_mag: float,
) -> ArrayComplexVoltageDto:
    """線間電圧を相電圧に変換する（スター結線・balanced 規約）。

    変換式: 相電圧 = 線間電圧 / √3（大きさのみ。30° の位相回転は付与しない）

    NOTE: 平衡正相 per-phase 等価規約用。線間と相を同位相として扱うため、
        厳密な L-L / L-N の 30° 位相差は省略する。Execute ステージはこの規約に
        統一されており、線間電圧と相電圧は位相が一致し大きさだけ √3 倍異なる。
        方向（位相）を厳密に扱う場合は `line_to_phase_voltage_star`
        （rotation-aware）を用いること。規約の正本は `ItmImVoltageCurrentDto`
        のクラス docstring を参照。

    計算方法:
    1. 入力値の極大極小要素を検出
    2. 変換計算を実行（大きさを 1/√3 にスケール、位相は保持）
    3. 変換後の極大極小要素をクランプ（位相情報は保持）

    Args:
        line_voltage_dto: 線間電圧DTO（複素数配列、配列の次元数は任意）
        eps: 近接ゼロ判定のしきい値（Config 由来）
        max_mag: 最大の大きさ（Config 由来、通常 1/eps）

    Returns:
        ArrayComplexVoltageDto: 相電圧DTO（単位: V、複素数配列、入力と同じ次元数）

    Warns:
        RuntimeWarning: 電圧値に0または極小の要素がある場合
        RuntimeWarning: 電圧値にinf/極大の要素がある場合
    """
    line_voltage_base = line_voltage_dto.to_base_unit()
    voltage_value = line_voltage_base.value
    base_unit = line_voltage_base.unit

    voltage_magnitude = np.abs(voltage_value)
    too_small = voltage_magnitude <= eps
    too_large = ~np.isfinite(voltage_value) | (voltage_magnitude >= max_mag)

    if np.any(too_small):
        record_numerical_stability_event(event_codes.VOLTAGE_EXTREME_SMALL)
    if np.any(too_large):
        record_numerical_stability_event(event_codes.VOLTAGE_EXTREME_LARGE)

    # 大きさのみ 1/√3 にスケール（位相回転は付与しない）
    phase_voltage_value = voltage_value / _SQRT_3

    # 変換後の極大極小要素をクランプ
    phase_voltage_phase = np.angle(phase_voltage_value)
    phase_voltage_value = np.where(
        too_small, eps * np.exp(1j * phase_voltage_phase), phase_voltage_value
    )
    phase_voltage_value = np.where(
        too_large,
        max_mag * np.exp(1j * phase_voltage_phase),
        phase_voltage_value,
    )

    return ArrayComplexVoltageDto(value=phase_voltage_value, unit=base_unit)


def phase_to_line_voltage_star(
    phase_voltage_dto: ArrayComplexVoltageDto,
    *,
    eps: float,
    max_mag: float,
) -> ArrayComplexVoltageDto:
    """相電圧を線間電圧に変換する（スター結線・rotation-aware）。

    変換式: 線間電圧 = √3 × 相電圧 × e^(jπ/6)
    位相は30°進みます（+30°）。

    NOTE: rotation-aware（±30° 厳密）版。Execute ステージは平衡 per-phase 規約
        （`phase_to_line_voltage_star_balanced`）を使うため、本関数は現状
        Execute から呼ばれない。方向（位相）を厳密に扱う Output 出力や、
        将来の不平衡・対称座標法拡張に向けた参照実装として温存する。

    計算方法:
    1. 入力値の極大極小要素を検出
    2. 変換計算を実行
    3. 変換後の極大極小要素をクランプ（位相情報は保持）

    Args:
        phase_voltage_dto: 相電圧DTO（複素数配列、配列の次元数は任意）
        eps: 近接ゼロ判定のしきい値（Config 由来）
        max_mag: 最大の大きさ（Config 由来、通常 1/eps）

    Returns:
        ArrayComplexVoltageDto: 線間電圧DTO（単位: V、複素数配列、入力と同じ次元数）

    Warns:
        RuntimeWarning: 電圧値に0または極小の要素がある場合
        RuntimeWarning: 電圧値にinf/極大の要素がある場合
    """
    phase_voltage_base = phase_voltage_dto.to_base_unit()
    voltage_value = phase_voltage_base.value
    base_unit = phase_voltage_base.unit

    voltage_magnitude = np.abs(voltage_value)
    too_small = voltage_magnitude <= eps
    too_large = ~np.isfinite(voltage_value) | (voltage_magnitude >= max_mag)

    if np.any(too_small):
        record_numerical_stability_event(event_codes.VOLTAGE_EXTREME_SMALL)
    if np.any(too_large):
        record_numerical_stability_event(event_codes.VOLTAGE_EXTREME_LARGE)

    # 変換計算を先に行う
    line_voltage_value = voltage_value * _SQRT_3 * _PHASE_ROTATION

    # 変換後の極大極小要素をクランプ
    line_voltage_phase = np.angle(line_voltage_value)
    line_voltage_value = np.where(
        too_small, eps * np.exp(1j * line_voltage_phase), line_voltage_value
    )
    line_voltage_value = np.where(
        too_large,
        max_mag * np.exp(1j * line_voltage_phase),
        line_voltage_value,
    )

    return ArrayComplexVoltageDto(value=line_voltage_value, unit=base_unit)


def phase_to_line_voltage_star_balanced(
    phase_voltage_dto: ArrayComplexVoltageDto,
    *,
    eps: float,
    max_mag: float,
) -> ArrayComplexVoltageDto:
    """相電圧を線間電圧に変換する（スター結線・balanced 規約）。

    変換式: 線間電圧 = √3 × 相電圧（大きさのみ。30° の位相回転は付与しない）

    NOTE: 平衡正相 per-phase 等価規約用。線間と相を同位相として扱うため、
        厳密な L-L / L-N の 30° 位相差は省略する。`line_to_phase_voltage_star_balanced`
        の逆変換であり、線間電圧は相電圧と位相が一致し大きさだけ √3 倍異なる。
        方向（位相）を厳密に扱う場合は `phase_to_line_voltage_star`
        （rotation-aware）を用いること。規約の正本は `ItmImVoltageCurrentDto`
        のクラス docstring を参照。

    計算方法:
    1. 入力値の極大極小要素を検出
    2. 変換計算を実行（大きさを √3 倍にスケール、位相は保持）
    3. 変換後の極大極小要素をクランプ（位相情報は保持）

    Args:
        phase_voltage_dto: 相電圧DTO（複素数配列、配列の次元数は任意）
        eps: 近接ゼロ判定のしきい値（Config 由来）
        max_mag: 最大の大きさ（Config 由来、通常 1/eps）

    Returns:
        ArrayComplexVoltageDto: 線間電圧DTO（単位: V、複素数配列、入力と同じ次元数）

    Warns:
        RuntimeWarning: 電圧値に0または極小の要素がある場合
        RuntimeWarning: 電圧値にinf/極大の要素がある場合
    """
    phase_voltage_base = phase_voltage_dto.to_base_unit()
    voltage_value = phase_voltage_base.value
    base_unit = phase_voltage_base.unit

    voltage_magnitude = np.abs(voltage_value)
    too_small = voltage_magnitude <= eps
    too_large = ~np.isfinite(voltage_value) | (voltage_magnitude >= max_mag)

    if np.any(too_small):
        record_numerical_stability_event(event_codes.VOLTAGE_EXTREME_SMALL)
    if np.any(too_large):
        record_numerical_stability_event(event_codes.VOLTAGE_EXTREME_LARGE)

    # 大きさのみ √3 倍（位相回転は付与しない）
    line_voltage_value = voltage_value * _SQRT_3

    # 変換後の極大極小要素をクランプ
    line_voltage_phase = np.angle(line_voltage_value)
    line_voltage_value = np.where(
        too_small, eps * np.exp(1j * line_voltage_phase), line_voltage_value
    )
    line_voltage_value = np.where(
        too_large,
        max_mag * np.exp(1j * line_voltage_phase),
        line_voltage_value,
    )

    return ArrayComplexVoltageDto(value=line_voltage_value, unit=base_unit)


def line_to_phase_current_star(
    line_current_dto: ArrayComplexCurrentDto,
    *,
    eps: float,
    max_mag: float,
) -> ArrayComplexCurrentDto:
    """線電流を相電流に変換する（スター結線）。

    変換式: 相電流 = 線電流（スター結線では等しい）

    計算方法:
    1. 入力値の極大極小要素を検出
    2. 変換計算を実行
    3. 変換後の極大極小要素をクランプ（位相情報は保持）

    Args:
        line_current_dto: 線電流DTO（複素数配列、配列の次元数は任意）
        eps: 近接ゼロ判定のしきい値（Config 由来）
        max_mag: 最大の大きさ（Config 由来、通常 1/eps）

    Returns:
        ArrayComplexCurrentDto: 相電流DTO（単位: A、複素数配列、入力と同じ次元数）

    Warns:
        RuntimeWarning: 電流値に0または極小の要素がある場合
        RuntimeWarning: 電流値にinf/極大の要素がある場合
    """
    line_current_base = line_current_dto.to_base_unit()
    current_value = line_current_base.value
    base_unit = line_current_base.unit

    current_magnitude = np.abs(current_value)
    too_small = current_magnitude <= eps
    too_large = ~np.isfinite(current_value) | (current_magnitude >= max_mag)

    if np.any(too_small):
        record_numerical_stability_event(event_codes.CURRENT_EXTREME_SMALL)
    if np.any(too_large):
        record_numerical_stability_event(event_codes.CURRENT_EXTREME_LARGE)

    # 変換計算を先に行う（スター結線では線電流 = 相電流）
    phase_current_value = current_value

    # 変換後の極大極小要素をクランプ
    phase_current_phase = np.angle(phase_current_value)
    phase_current_value = np.where(
        too_small, eps * np.exp(1j * phase_current_phase), phase_current_value
    )
    phase_current_value = np.where(
        too_large,
        max_mag * np.exp(1j * phase_current_phase),
        phase_current_value,
    )

    return ArrayComplexCurrentDto(value=phase_current_value, unit=base_unit)


def phase_to_line_current_star(
    phase_current_dto: ArrayComplexCurrentDto,
    *,
    eps: float,
    max_mag: float,
) -> ArrayComplexCurrentDto:
    """相電流を線電流に変換する（スター結線）。

    変換式: 線電流 = 相電流（スター結線では等しい）

    計算方法:
    1. 入力値の極大極小要素を検出
    2. 変換計算を実行
    3. 変換後の極大極小要素をクランプ（位相情報は保持）

    Args:
        phase_current_dto: 相電流DTO（複素数配列、配列の次元数は任意）
        eps: 近接ゼロ判定のしきい値（Config 由来）
        max_mag: 最大の大きさ（Config 由来、通常 1/eps）

    Returns:
        ArrayComplexCurrentDto: 線電流DTO（単位: A、複素数配列、入力と同じ次元数）

    Warns:
        RuntimeWarning: 電流値に0または極小の要素がある場合
        RuntimeWarning: 電流値にinf/極大の要素がある場合
    """
    phase_current_base = phase_current_dto.to_base_unit()
    current_value = phase_current_base.value
    base_unit = phase_current_base.unit

    current_magnitude = np.abs(current_value)
    too_small = current_magnitude <= eps
    too_large = ~np.isfinite(current_value) | (current_magnitude >= max_mag)

    if np.any(too_small):
        record_numerical_stability_event(event_codes.CURRENT_EXTREME_SMALL)
    if np.any(too_large):
        record_numerical_stability_event(event_codes.CURRENT_EXTREME_LARGE)

    # 変換計算を先に行う（スター結線では線電流 = 相電流）
    line_current_value = current_value

    # 変換後の極大極小要素をクランプ
    line_current_phase = np.angle(line_current_value)
    line_current_value = np.where(
        too_small, eps * np.exp(1j * line_current_phase), line_current_value
    )
    line_current_value = np.where(
        too_large,
        max_mag * np.exp(1j * line_current_phase),
        line_current_value,
    )

    return ArrayComplexCurrentDto(value=line_current_value, unit=base_unit)
