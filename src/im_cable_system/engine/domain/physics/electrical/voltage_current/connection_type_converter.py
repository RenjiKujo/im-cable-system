"""結線タイプ変換計算ロジック（ドメイン層）。

このモジュールは、デルタ結線とスター結線の等価変換をした場合、**相電圧・相電流**を結線方法に応じて相互変換する処理を提供します（等価変換後の結果変換）。

注意: このモジュールは**相電圧・相電流**の変換を扱います。
線間電圧・線電流の変換は `star_line_phase_converter` および `delta_line_phase_converter` を参照してください。

現状、デルタ結線はスター結線に変換して電気計算を行うため、スター結線として計算した
結果を、実際のデルタ結線の**相電圧・相電流**に変換するために使用することが主な用途となります。
ただし、逆の変換にも対応できるように実装しておきます。

等価変換後、スター結線として計算した結果をデルタ結線に変換する場合（rotation-aware）:
- 線間電圧・線間電流: 等価変換により同じ値（変換不要）
- **相電圧**: デルタの相電圧 = √3・スターの相電圧・e^(jπ/6)
- **相電流**: デルタの相電流 = スターの相電流 / √3・e^(jπ/6)

位相規約（2 系統）:
    - rotation-aware（厳密版）: 上記のとおり ±30°（π/6）位相回転を含める。
    - balanced（平衡 per-phase 規約）: 30° を付与せず、大きさ換算のみ行う
        （相電圧 = √3・スター相電圧、相電流 = スター相電流 / √3）。
        Execute はスター等価相で計算し、巻線量への変換は Output ステージで
        balanced 版を用いる。方向（位相）を厳密に扱う Output 出力が必要な場合に
        限り rotation-aware 版を用いる。規約の正本は `ItmImVoltageCurrentDto`
        のクラス docstring を参照。

提供する関数:
- convert_voltage_delta_to_star: デルタ結線の相電圧→スター結線の相電圧変換（rotation-aware）
- convert_current_delta_to_star: デルタ結線の相電流→スター結線の相電流変換（rotation-aware）
- convert_voltage_star_to_delta: スター結線の相電圧→デルタ結線の相電圧変換（rotation-aware）
- convert_current_star_to_delta: スター結線の相電流→デルタ結線の相電流変換（rotation-aware）
- convert_voltage_star_to_delta_balanced: スター→デルタ 相電圧変換（balanced・大きさのみ）
- convert_current_star_to_delta_balanced: スター→デルタ 相電流変換（balanced・大きさのみ）
- convert_voltage_delta_to_star_balanced: デルタ→スター 相電圧変換（balanced・大きさのみ）
- convert_current_delta_to_star_balanced: デルタ→スター 相電流変換（balanced・大きさのみ）
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

# √3の値（デルタ・スター変換係数）
_SQRT_3: float = np.sqrt(3.0)
# 30°遅れる位相回転係数（-30° = -π/6）
_PHASE_ROTATION_DELTA_TO_STAR: complex = np.exp(-1j * np.pi / 6.0)
# 30°進む位相回転係数（+30° = +π/6）
_PHASE_ROTATION_STAR_TO_DELTA: complex = np.exp(1j * np.pi / 6.0)


def convert_voltage_delta_to_star(
    voltage_dto: ArrayComplexVoltageDto,
    *,
    eps: float,
    max_mag: float,
) -> ArrayComplexVoltageDto:
    """デルタ結線の相電圧をスター結線の相電圧に変換する（rotation-aware）。

    変換式: V_star_phase = V_delta_phase / √3 × e^(-jπ/6)
    位相は30°遅れます（-30°）。

    NOTE: rotation-aware（±30° 厳密）版。Execute/Output の既定経路は balanced 版
        （`convert_voltage_delta_to_star_balanced`）を使うため、本関数は現状
        未使用。方向（位相）を厳密に扱う Output 出力や、将来の不平衡・
        対称座標法拡張に向けた参照実装として温存する。

    計算方法:
    1. 入力値の極大極小要素を検出してマスク
    2. マスクした要素を安全な値に置き換えて変換計算
    3. マスクした要素の位置にクランプ値を設定（位相情報は保持）

    Args:
        voltage_dto: デルタ結線の相電圧DTO（3次配列: slip × frequency × phase_voltage、複素数）
        eps: 近接ゼロ判定のしきい値（Config 由来）
        max_mag: 最大の大きさ（Config 由来、通常 1/eps）

    Returns:
        ArrayComplexVoltageDto: スター結線の相電圧DTO（単位: V、3次配列、複素数）

    Warns:
        RuntimeWarning: 電圧値に0または極小の要素がある場合
        RuntimeWarning: 電圧値にinf/極大の要素がある場合
    """
    delta_voltage_base = voltage_dto.to_base_unit()
    voltage_value = delta_voltage_base.value
    base_unit = delta_voltage_base.unit

    voltage_magnitude = np.abs(voltage_value)
    voltage_phase = np.angle(voltage_value)
    too_small = voltage_magnitude <= eps
    too_large = ~np.isfinite(voltage_value) | (voltage_magnitude >= max_mag)
    mask = too_small | too_large

    if np.any(too_small):
        record_numerical_stability_event(event_codes.VOLTAGE_EXTREME_SMALL)
    if np.any(too_large):
        record_numerical_stability_event(event_codes.VOLTAGE_EXTREME_LARGE)

    safe_magnitude = np.where(mask, eps, voltage_magnitude)
    voltage_safe = safe_magnitude * np.exp(1j * voltage_phase)
    star_voltage_value = voltage_safe / _SQRT_3 * _PHASE_ROTATION_DELTA_TO_STAR

    star_voltage_phase = np.angle(star_voltage_value)
    star_voltage_value = np.where(
        too_small, eps * np.exp(1j * star_voltage_phase), star_voltage_value
    )
    star_voltage_value = np.where(
        too_large, max_mag * np.exp(1j * star_voltage_phase), star_voltage_value
    )

    return ArrayComplexVoltageDto(value=star_voltage_value, unit=base_unit)


def convert_current_delta_to_star(
    current_dto: ArrayComplexCurrentDto,
    *,
    eps: float,
    max_mag: float,
) -> ArrayComplexCurrentDto:
    """デルタ結線の相電流をスター結線の相電流に変換する（rotation-aware）。

    変換式: I_star_phase = I_delta_phase × √3 × e^(-jπ/6)
    位相は30°遅れます（-30°）。

    NOTE: rotation-aware（±30° 厳密）版。Execute/Output の既定経路は balanced 版
        （`convert_current_delta_to_star_balanced`）を使うため、本関数は現状
        未使用。方向（位相）を厳密に扱う Output 出力や、将来の不平衡・
        対称座標法拡張に向けた参照実装として温存する。

    計算方法:
    1. 入力値の極大極小要素を検出してマスク
    2. マスクした要素を安全な値に置き換えて変換計算
    3. マスクした要素の位置にクランプ値を設定（位相情報は保持）

    Args:
        current_dto: デルタ結線の相電流DTO（3次配列: slip × frequency × phase_current、複素数）
        eps: 近接ゼロ判定のしきい値（Config 由来）
        max_mag: 最大の大きさ（Config 由来、通常 1/eps）

    Returns:
        ArrayComplexCurrentDto: スター結線の相電流DTO（単位: A、3次配列、複素数）

    Warns:
        RuntimeWarning: 電流値に0または極小の要素がある場合
        RuntimeWarning: 電流値にinf/極大の要素がある場合
    """
    delta_current_base = current_dto.to_base_unit()
    current_value = delta_current_base.value
    base_unit = delta_current_base.unit

    current_magnitude = np.abs(current_value)
    current_phase = np.angle(current_value)
    too_small = current_magnitude <= eps
    too_large = ~np.isfinite(current_value) | (current_magnitude >= max_mag)
    mask = too_small | too_large

    if np.any(too_small):
        record_numerical_stability_event(event_codes.CURRENT_EXTREME_SMALL)
    if np.any(too_large):
        record_numerical_stability_event(event_codes.CURRENT_EXTREME_LARGE)

    safe_magnitude = np.where(mask, eps, current_magnitude)
    current_safe = safe_magnitude * np.exp(1j * current_phase)
    star_current_value = current_safe * _SQRT_3 * _PHASE_ROTATION_DELTA_TO_STAR

    star_current_phase = np.angle(star_current_value)
    star_current_value = np.where(
        too_small, eps * np.exp(1j * star_current_phase), star_current_value
    )
    star_current_value = np.where(
        too_large, max_mag * np.exp(1j * star_current_phase), star_current_value
    )

    return ArrayComplexCurrentDto(value=star_current_value, unit=base_unit)


def convert_voltage_star_to_delta(
    voltage_dto: ArrayComplexVoltageDto,
    *,
    eps: float,
    max_mag: float,
) -> ArrayComplexVoltageDto:
    """スター結線の相電圧をデルタ結線の相電圧に変換する（rotation-aware）。

    変換式: V_delta_phase = √3・V_star_phase・e^(jπ/6)
    位相は30°進みます（+30°）。

    NOTE: rotation-aware（±30° 厳密）版。Execute/Output の既定経路は balanced 版
        （`convert_voltage_star_to_delta_balanced`）を使うため、本関数は現状
        未使用。方向（位相）を厳密に扱う Output 出力や、将来の不平衡・
        対称座標法拡張に向けた参照実装として温存する。

    計算方法:
    1. 入力値の極大極小要素を検出してマスク
    2. マスクした要素を安全な値に置き換えて変換計算
    3. マスクした要素の位置にクランプ値を設定（位相情報は保持）

    Args:
        voltage_dto: スター結線の相電圧DTO（3次配列: slip × frequency × phase_voltage、複素数）
        eps: 近接ゼロ判定のしきい値（Config 由来）
        max_mag: 最大の大きさ（Config 由来、通常 1/eps）

    Returns:
        ArrayComplexVoltageDto: デルタ結線の相電圧DTO（単位: V、3次配列、複素数）

    Warns:
        RuntimeWarning: 電圧値に0または極小の要素がある場合
        RuntimeWarning: 電圧値にinf/極大の要素がある場合
    """
    star_voltage_base = voltage_dto.to_base_unit()
    voltage_value = star_voltage_base.value
    base_unit = star_voltage_base.unit

    voltage_magnitude = np.abs(voltage_value)
    voltage_phase = np.angle(voltage_value)
    too_small = voltage_magnitude <= eps
    too_large = ~np.isfinite(voltage_value) | (voltage_magnitude >= max_mag)
    mask = too_small | too_large

    if np.any(too_small):
        record_numerical_stability_event(event_codes.VOLTAGE_EXTREME_SMALL)
    if np.any(too_large):
        record_numerical_stability_event(event_codes.VOLTAGE_EXTREME_LARGE)

    safe_magnitude = np.where(mask, eps, voltage_magnitude)
    voltage_safe = safe_magnitude * np.exp(1j * voltage_phase)
    delta_voltage_value = voltage_safe * _SQRT_3 * _PHASE_ROTATION_STAR_TO_DELTA

    delta_voltage_phase = np.angle(delta_voltage_value)
    delta_voltage_value = np.where(
        too_small, eps * np.exp(1j * delta_voltage_phase), delta_voltage_value
    )
    delta_voltage_value = np.where(
        too_large,
        max_mag * np.exp(1j * delta_voltage_phase),
        delta_voltage_value,
    )

    return ArrayComplexVoltageDto(value=delta_voltage_value, unit=base_unit)


def convert_current_star_to_delta(
    current_dto: ArrayComplexCurrentDto,
    *,
    eps: float,
    max_mag: float,
) -> ArrayComplexCurrentDto:
    """スター結線の相電流をデルタ結線の相電流に変換する（rotation-aware）。

    変換式: I_delta_phase = I_star_phase / √3・e^(jπ/6)
    位相は30°進みます（+30°）。

    NOTE: rotation-aware（±30° 厳密）版。Execute/Output の既定経路は balanced 版
        （`convert_current_star_to_delta_balanced`）を使うため、本関数は現状
        未使用。方向（位相）を厳密に扱う Output 出力や、将来の不平衡・
        対称座標法拡張に向けた参照実装として温存する。

    計算方法:
    1. 入力値の極大極小要素を検出してマスク
    2. マスクした要素を安全な値に置き換えて変換計算
    3. マスクした要素の位置にクランプ値を設定（位相情報は保持）

    Args:
        current_dto: スター結線の相電流DTO（3次配列: slip × frequency × phase_current、複素数）
        eps: 近接ゼロ判定のしきい値（Config 由来）
        max_mag: 最大の大きさ（Config 由来、通常 1/eps）

    Returns:
        ArrayComplexCurrentDto: デルタ結線の相電流DTO（単位: A、3次配列、複素数）

    Warns:
        RuntimeWarning: 電流値に0または極小の要素がある場合
        RuntimeWarning: 電流値にinf/極大の要素がある場合
    """
    star_current_base = current_dto.to_base_unit()
    current_value = star_current_base.value
    base_unit = star_current_base.unit

    current_magnitude = np.abs(current_value)
    current_phase = np.angle(current_value)
    too_small = current_magnitude <= eps
    too_large = ~np.isfinite(current_value) | (current_magnitude >= max_mag)
    mask = too_small | too_large

    if np.any(too_small):
        record_numerical_stability_event(event_codes.CURRENT_EXTREME_SMALL)
    if np.any(too_large):
        record_numerical_stability_event(event_codes.CURRENT_EXTREME_LARGE)

    safe_magnitude = np.where(mask, eps, current_magnitude)
    current_safe = safe_magnitude * np.exp(1j * current_phase)
    delta_current_value = current_safe / _SQRT_3 * _PHASE_ROTATION_STAR_TO_DELTA

    delta_current_phase = np.angle(delta_current_value)
    delta_current_value = np.where(
        too_small, eps * np.exp(1j * delta_current_phase), delta_current_value
    )
    delta_current_value = np.where(
        too_large,
        max_mag * np.exp(1j * delta_current_phase),
        delta_current_value,
    )

    return ArrayComplexCurrentDto(value=delta_current_value, unit=base_unit)


def convert_voltage_star_to_delta_balanced(
    voltage_dto: ArrayComplexVoltageDto,
    *,
    eps: float,
    max_mag: float,
) -> ArrayComplexVoltageDto:
    """スター相電圧をデルタ巻線相電圧に変換する（balanced・大きさのみ）。

    変換式: V_delta_phase = √3・V_star_phase（大きさのみ。30° 回転は付与しない）

    NOTE: 平衡 per-phase 規約用。デルタ巻線の相電圧は線間電圧に等しく、その
        大きさはスター等価相電圧の √3 倍となる。本リポジトリの balanced 規約では
        線間と相を同位相として扱うため、30° の位相回転は付与しない。方向
        （位相）を厳密に扱う場合は `convert_voltage_star_to_delta`
        （rotation-aware）を用いること。

    Args:
        voltage_dto: スター結線の相電圧DTO（複素数配列、配列の次元数は任意）
        eps: 近接ゼロ判定のしきい値（Config 由来）
        max_mag: 最大の大きさ（Config 由来、通常 1/eps）

    Returns:
        ArrayComplexVoltageDto: デルタ結線の相電圧DTO（単位: V、複素数配列）

    Warns:
        RuntimeWarning: 電圧値に0または極小の要素がある場合
        RuntimeWarning: 電圧値にinf/極大の要素がある場合
    """
    star_voltage_base = voltage_dto.to_base_unit()
    voltage_value = star_voltage_base.value
    base_unit = star_voltage_base.unit

    voltage_magnitude = np.abs(voltage_value)
    too_small = voltage_magnitude <= eps
    too_large = ~np.isfinite(voltage_value) | (voltage_magnitude >= max_mag)

    if np.any(too_small):
        record_numerical_stability_event(event_codes.VOLTAGE_EXTREME_SMALL)
    if np.any(too_large):
        record_numerical_stability_event(event_codes.VOLTAGE_EXTREME_LARGE)

    # 大きさのみ √3 倍（位相回転は付与しない）
    delta_voltage_value = voltage_value * _SQRT_3

    delta_voltage_phase = np.angle(delta_voltage_value)
    delta_voltage_value = np.where(
        too_small, eps * np.exp(1j * delta_voltage_phase), delta_voltage_value
    )
    delta_voltage_value = np.where(
        too_large,
        max_mag * np.exp(1j * delta_voltage_phase),
        delta_voltage_value,
    )

    return ArrayComplexVoltageDto(value=delta_voltage_value, unit=base_unit)


def convert_current_star_to_delta_balanced(
    current_dto: ArrayComplexCurrentDto,
    *,
    eps: float,
    max_mag: float,
) -> ArrayComplexCurrentDto:
    """スター相電流をデルタ巻線相電流に変換する（balanced・大きさのみ）。

    変換式: I_delta_phase = I_star_phase / √3（大きさのみ。30° 回転は付与しない）

    NOTE: 平衡 per-phase 規約用。デルタ巻線の相電流は線電流の 1/√3 となり、
        スター等価相電流（= 線電流）の 1/√3 倍に等しい。本リポジトリの balanced
        規約では 30° の位相回転は付与しない。方向（位相）を厳密に扱う場合は
        `convert_current_star_to_delta`（rotation-aware）を用いること。

    Args:
        current_dto: スター結線の相電流DTO（複素数配列、配列の次元数は任意）
        eps: 近接ゼロ判定のしきい値（Config 由来）
        max_mag: 最大の大きさ（Config 由来、通常 1/eps）

    Returns:
        ArrayComplexCurrentDto: デルタ結線の相電流DTO（単位: A、複素数配列）

    Warns:
        RuntimeWarning: 電流値に0または極小の要素がある場合
        RuntimeWarning: 電流値にinf/極大の要素がある場合
    """
    star_current_base = current_dto.to_base_unit()
    current_value = star_current_base.value
    base_unit = star_current_base.unit

    current_magnitude = np.abs(current_value)
    too_small = current_magnitude <= eps
    too_large = ~np.isfinite(current_value) | (current_magnitude >= max_mag)

    if np.any(too_small):
        record_numerical_stability_event(event_codes.CURRENT_EXTREME_SMALL)
    if np.any(too_large):
        record_numerical_stability_event(event_codes.CURRENT_EXTREME_LARGE)

    # 大きさのみ 1/√3 倍（位相回転は付与しない）
    delta_current_value = current_value / _SQRT_3

    delta_current_phase = np.angle(delta_current_value)
    delta_current_value = np.where(
        too_small, eps * np.exp(1j * delta_current_phase), delta_current_value
    )
    delta_current_value = np.where(
        too_large,
        max_mag * np.exp(1j * delta_current_phase),
        delta_current_value,
    )

    return ArrayComplexCurrentDto(value=delta_current_value, unit=base_unit)


def convert_voltage_delta_to_star_balanced(
    voltage_dto: ArrayComplexVoltageDto,
    *,
    eps: float,
    max_mag: float,
) -> ArrayComplexVoltageDto:
    """デルタ巻線相電圧をスター等価相電圧に変換する（balanced・大きさのみ）。

    変換式: V_star_phase = V_delta_phase / √3（大きさのみ。30° 回転は付与しない）

    NOTE: 平衡 per-phase 規約用。`convert_voltage_star_to_delta_balanced` の
        逆変換であり、スター等価相電圧はデルタ巻線相電圧の 1/√3 倍（同位相）。
        方向（位相）を厳密に扱う場合は `convert_voltage_delta_to_star`
        （rotation-aware）を用いること。

    Args:
        voltage_dto: デルタ結線の相電圧DTO（複素数配列、配列の次元数は任意）
        eps: 近接ゼロ判定のしきい値（Config 由来）
        max_mag: 最大の大きさ（Config 由来、通常 1/eps）

    Returns:
        ArrayComplexVoltageDto: スター結線の相電圧DTO（単位: V、複素数配列）

    Warns:
        RuntimeWarning: 電圧値に0または極小の要素がある場合
        RuntimeWarning: 電圧値にinf/極大の要素がある場合
    """
    delta_voltage_base = voltage_dto.to_base_unit()
    voltage_value = delta_voltage_base.value
    base_unit = delta_voltage_base.unit

    voltage_magnitude = np.abs(voltage_value)
    too_small = voltage_magnitude <= eps
    too_large = ~np.isfinite(voltage_value) | (voltage_magnitude >= max_mag)

    if np.any(too_small):
        record_numerical_stability_event(event_codes.VOLTAGE_EXTREME_SMALL)
    if np.any(too_large):
        record_numerical_stability_event(event_codes.VOLTAGE_EXTREME_LARGE)

    # 大きさのみ 1/√3 倍（位相回転は付与しない）
    star_voltage_value = voltage_value / _SQRT_3

    star_voltage_phase = np.angle(star_voltage_value)
    star_voltage_value = np.where(
        too_small, eps * np.exp(1j * star_voltage_phase), star_voltage_value
    )
    star_voltage_value = np.where(
        too_large,
        max_mag * np.exp(1j * star_voltage_phase),
        star_voltage_value,
    )

    return ArrayComplexVoltageDto(value=star_voltage_value, unit=base_unit)


def convert_current_delta_to_star_balanced(
    current_dto: ArrayComplexCurrentDto,
    *,
    eps: float,
    max_mag: float,
) -> ArrayComplexCurrentDto:
    """デルタ巻線相電流をスター等価相電流に変換する（balanced・大きさのみ）。

    変換式: I_star_phase = I_delta_phase × √3（大きさのみ。30° 回転は付与しない）

    NOTE: 平衡 per-phase 規約用。`convert_current_star_to_delta_balanced` の
        逆変換であり、スター等価相電流はデルタ巻線相電流の √3 倍（同位相、
        スターでは線電流に等しい）。方向（位相）を厳密に扱う場合は
        `convert_current_delta_to_star`（rotation-aware）を用いること。

    Args:
        current_dto: デルタ結線の相電流DTO（複素数配列、配列の次元数は任意）
        eps: 近接ゼロ判定のしきい値（Config 由来）
        max_mag: 最大の大きさ（Config 由来、通常 1/eps）

    Returns:
        ArrayComplexCurrentDto: スター結線の相電流DTO（単位: A、複素数配列）

    Warns:
        RuntimeWarning: 電流値に0または極小の要素がある場合
        RuntimeWarning: 電流値にinf/極大の要素がある場合
    """
    delta_current_base = current_dto.to_base_unit()
    current_value = delta_current_base.value
    base_unit = delta_current_base.unit

    current_magnitude = np.abs(current_value)
    too_small = current_magnitude <= eps
    too_large = ~np.isfinite(current_value) | (current_magnitude >= max_mag)

    if np.any(too_small):
        record_numerical_stability_event(event_codes.CURRENT_EXTREME_SMALL)
    if np.any(too_large):
        record_numerical_stability_event(event_codes.CURRENT_EXTREME_LARGE)

    # 大きさのみ √3 倍（位相回転は付与しない）
    star_current_value = current_value * _SQRT_3

    star_current_phase = np.angle(star_current_value)
    star_current_value = np.where(
        too_small, eps * np.exp(1j * star_current_phase), star_current_value
    )
    star_current_value = np.where(
        too_large,
        max_mag * np.exp(1j * star_current_phase),
        star_current_value,
    )

    return ArrayComplexCurrentDto(value=star_current_value, unit=base_unit)
