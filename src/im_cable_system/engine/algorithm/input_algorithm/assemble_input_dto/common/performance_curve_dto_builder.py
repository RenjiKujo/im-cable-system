"""ImPerformanceCurveLoadedData から ImPerformanceCurveCatalogDtos を構築する（Forward / EstimateParams 共通）。

設計方針 — 絶対単位入力前提（定格非依存）:
    本ビルダーは Forward / EstimateParams 両経路から共通利用される。
    本ビルダーに渡される段階では性能曲線の従属系列は **絶対単位** で
    記録されている前提とし、次の単位だけを許容する。

    - ``power``: ``W`` / ``kW`` / ``MW`` / ``HP``
    - ``torque``: ``Nm`` / ``N·m`` / ``kgf·m``
    - ``current``: ``A`` / ``kA`` / ``mA``
    - ``power_factor`` / ``efficiency``: 無次元（角括弧 ``[-]`` を含む
      ``-`` 表記も含めて Generic DTO 側で許容される）

    定格に対する **比率単位** ``-`` （ratio）や ``%`` （percent of rated）
    は、``power`` / ``torque`` / ``current`` 列について **明示的に拒否**
    する（``_reject_ratio_unit_or_raise``）。これは：

    - 実験段階（Forward TSV）では参照する定格情報がそもそも無い、
    - Forward TSV は独立軸→従属系列の純粋な計測表である、

    というドメイン上の前提に反するため。

経路ごとの呼び出し規約:
    - **Forward 経路**: 性能曲線 TSV は「定格非依存のスペック曲線」で
      あり、絶対単位以外を入れる余地が無い。``ForwardInputDtoAssembler``
      は LoadedData をそのまま本ビルダーに渡し、比率単位が混ざっていれば
      本ビルダー内で ``ValueError`` として拒否される。
    - **EstimateParams 経路**: 統合 TSV では名盤と観測曲線が併載される
      ため、入力ファイル上は ``power[-]`` / ``current[%]`` の比率指定が
      許容される。``EstimateParamsAssembler`` が
      :func:`...estimate_params.perf_curve_unit_converter
      .convert_ratio_columns_to_absolute` で **本ビルダーに渡す前に**
      ``ratio→absolute`` 変換を行う。本ビルダー側では Forward 経路と
      同じ「絶対単位前提・比率単位拒否」契約のまま動作する。

セル単位の欠損 (``np.nan``) の扱い:
    LoadedData の観測列（``power`` / ``current`` / ``power_factor`` /
    ``efficiency`` / ``torque``）は空セルを ``np.nan`` として保持
    している。本アセンブラでは、各観測系列について

    1. 元配列を ``mask = ~np.isnan(arr)`` で valid 点 mask を抽出。
    2. NaN を 0.0 に置換した配列を ``Array*Dto`` の ``value`` に渡す
       （Generic ``Array*Dto`` は inf を禁止するため）。
    3. **常に** bool 配列 ``mask`` を ``*_series_mask`` として
       :class:`ImPerformanceCurveCatalogDto` に渡す（全点 valid のとき
       でも ``np.ones(n, dtype=bool)`` を明示的に渡す）。
       これは Catalog DTO 側で series 非 None ⇒ mask 必須としているため。

    ``torque`` 由来の ``power_series`` 逆算経路では、``torque`` の mask
    をそのまま ``power_series_mask`` に流用する（NaN 点は ``power_w=0``
    プレースホルダ）。

    ``inf`` は欠損ではなく異常値として扱い、検出時は :class:`ValueError`
    を上げる（``ArrayActivePowerDto`` 等の Generic DTO の inf 禁止契約と
    整合させる）。
"""

from __future__ import annotations

import math

import numpy as np

from im_cable_system.engine.algorithm.input_algorithm.assemble_input_dto.common.unit_normalizer import (  # noqa: E501
    normalize_loaded_unit_cell,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data.data_class.im_performance_curve_loaded_data import (  # noqa: E501
    ImPerformanceCurveLoadedData,
)
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ImPerformanceCurveCatalogDto,
    ImPerformanceCurveCatalogDtos,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayActivePowerDto,
    ArrayCurrentMagnitudeDto,
    ArrayEfficiencyDto,
    ArrayPowerFactorDto,
    ArrayRotationalSpeedDto,
    ArraySlipDto,
    ArrayTorqueDto,
    FloatFrequencyDto,
    FloatVoltageDto,
)

# 本ビルダー（Forward / EstimateParams 共通）で拒否する比率単位（``unit_normalizer``
# で角括弧を剥がしたあとに比較する文字列集合）。``-`` （ratio）と ``%``
# （percent of rated）。EstimateParams 経路では呼び出し前に
# ``perf_curve_unit_converter`` で ratio→absolute 変換済みのため、ここに
# 到達する時点で比率単位は残っていない前提。
_RATIO_UNITS_FORBIDDEN_IN_BUILDER: frozenset[str] = frozenset({"-", "%"})


def _split_value_and_mask(
    arr: np.ndarray,
    *,
    label: str,
) -> tuple[np.ndarray, np.ndarray]:
    """``arr`` の NaN を 0 に置換し、有効点の bool mask を返す。

    ``inf`` は欠損ではなく異常値とみなし、検出したら :class:`ValueError`。
    NaN だけが mask=False の対象であり、NaN の点は値を 0.0 に置換する。
    Catalog DTO 側で「series 非 None ⇒ mask 必須」を要求しているため、
    全点 valid のときも ``np.ones(n, dtype=bool)`` 相当を返す。

    Args:
        arr: 1-D 配列。``np.nan`` は欠損点として許容するが ``inf`` は禁止。
        label: エラーメッセージで指す系列名（``power_series`` 等）。

    Returns:
        ``(placeholder_arr, mask)`` のタプル。
        ``placeholder_arr`` は ``arr`` の NaN を 0.0 に置換した配列、
        ``mask`` は ``~np.isnan(arr)`` の bool 配列で、必ず ``arr`` と
        同じ長さ・1-D・bool dtype。

    Raises:
        ValueError: ``arr`` に ``inf`` が含まれていた場合。
    """
    if np.any(np.isinf(arr)):
        raise ValueError(
            f"{label} に inf が含まれています。inf は欠損 (NaN) ではなく"
            "異常値として扱うため、loader / 上流側で除外してから本"
            "アセンブラに渡してください。"
        )
    mask = ~np.isnan(arr)
    placeholder = np.where(mask, arr, 0.0)
    return placeholder, mask


def _reject_ratio_unit_or_raise(unit_raw: str | None, label: str) -> str:
    """本ビルダー段で許容されない比率単位を拒否し、剥がし後の単位を返す。

    本ビルダーは Forward / EstimateParams 両経路から共通利用される。
    呼び出し時点での性能曲線は **絶対単位前提** であり、``power`` /
    ``torque`` / ``current`` 列の単位として ``-`` （ratio）や ``%``
    （percent of rated）を許容しない。EstimateParams 経路では、
    ``EstimateParamsAssembler`` が事前に
    :func:`...estimate_params.perf_curve_unit_converter
    .convert_ratio_columns_to_absolute` で名盤値を用いた ``ratio→absolute``
    変換を行ってから本ビルダーへ委譲する設計のため、ここに ``-`` /
    ``%`` が残るのは契約違反として ``ValueError`` を上げる。

    Args:
        unit_raw: ロード時に ``strip()`` のみ施された単位セル。
        label: エラーメッセージで指す系列名（``power`` / ``torque`` /
            ``current`` のいずれか）。

    Returns:
        外側角括弧を剥がした単位文字列。``unit_raw`` が ``None`` の場合は
        空文字列を返す（呼び出し側で「単位無し」と判定される）。

    Raises:
        ValueError: 単位が比率（``-`` または ``%``）の場合。
    """
    if unit_raw is None:
        return ""
    normalized = normalize_loaded_unit_cell(unit_raw)
    if normalized in _RATIO_UNITS_FORBIDDEN_IN_BUILDER:
        raise ValueError(
            f"性能曲線ビルダーでは {label} 列の比率単位 {unit_raw!r} を"
            "許容しません。本ビルダーは絶対単位前提のため、"
            "絶対単位 (power=W/kW/MW/HP, torque=Nm/N·m/kgf·m, "
            "current=A/kA/mA) で入力してください。比率単位での入力が"
            "必要な場合は EstimateParams 経路を使用してください "
            "（assemble_input_dto.estimate_params.perf_curve_unit_converter"
            " で名盤値を用いた ratio→absolute 変換が行われます）。"
        )
    return normalized


def _poles_as_positive_int(poles: float) -> int:
    """``poles`` を正整数として受け取る（同期回転数計算の前提）。"""
    poles_int = int(round(poles))
    if poles_int <= 0 or abs(poles - poles_int) > 1e-9:
        raise ValueError(
            f"性能曲線メタの poles は正の整数である必要があります: {poles!r}"
        )
    return poles_int


def _derive_slip_from_rpm(
    rpm_arr: np.ndarray,
    poles: int,
    supply_frequency_hz: float,
) -> np.ndarray:
    """回転速度からスリップ配列を導出する。

    Args:
        rpm_arr: 回転速度配列 [rpm]。
        poles: 極数。
        supply_frequency_hz: 供給周波数 [Hz]。

    Returns:
        np.ndarray: スリップ ``(N_sync - rpm) / N_sync``。
    """
    n_sync_rpm = 120.0 * supply_frequency_hz / float(poles)
    return (n_sync_rpm - rpm_arr) / n_sync_rpm


def _omega_rad_s_from_rpm(rpm_arr: np.ndarray) -> np.ndarray:
    return 2.0 * math.pi * rpm_arr / 60.0


def _resolve_torque_series(
    curve_loaded: ImPerformanceCurveLoadedData,
) -> tuple[ArrayTorqueDto | None, np.ndarray | None]:
    """``torque_series`` と ``torque_series_mask`` を解決する。

    TSV に ``torque`` 列がある場合のみ ``ArrayTorqueDto`` として保持する。
    単位は絶対単位（``Nm`` / ``N·m`` / ``kgf·m``）に限る。
    NaN セルは 0 (Nm) プレースホルダ + mask=False。
    """
    if curve_loaded.torque is None or curve_loaded.torque_unit is None:
        return None, None
    unit = _reject_ratio_unit_or_raise(curve_loaded.torque_unit, "torque")
    torque_arr = np.asarray(curve_loaded.torque, dtype=np.float64)
    placeholder, mask = _split_value_and_mask(
        torque_arr,
        label="torque_series",
    )
    dto = ArrayTorqueDto(value=placeholder, unit=unit)
    return dto, mask


def _resolve_power_series(
    curve_loaded: ImPerformanceCurveLoadedData,
    rpm_arr: np.ndarray,
    torque_dto: ArrayTorqueDto | None,
    torque_mask: np.ndarray | None,
) -> tuple[ArrayActivePowerDto | None, np.ndarray | None]:
    """``power_series`` と ``power_series_mask`` を解決する。

    優先順:
        1. ``power`` 列が TSV にある → 単位ごと素通し。本ビルダー段では
           ``W`` / ``kW`` / ``MW`` / ``HP`` のみ許容（``-`` / ``%`` は
           :class:`ValueError`）。NaN セルは 0 W プレースホルダ + mask=False。
        2. ``power`` が無く ``torque`` だけある → ``P = T·ω`` で逆算。
           torque を SI (Nm) に揃えてから掛け算する。NaN 点は 0 W
           プレースホルダ + mask=False（torque mask をそのまま流用）。
        3. どちらも無い → ``(None, None)``。

    ``power`` と ``torque`` が両方ある場合は 1 の結果を採用する。
    両者の整合性検証は :class:`ImPerformanceCurveCatalogDto.__post_init__`
    側で行うため、ここでは判定しない。

    Args:
        curve_loaded: 性能曲線中間表現。
        rpm_arr: 回転速度配列（``ω`` 換算用）。
        torque_dto: 既に解決済みの torque DTO（``_resolve_torque_series``
            の戻り値の DTO）。``power`` 列が無いケースで逆算ソースとして
            使う。``None`` の場合は逆算経路をスキップする。
        torque_mask: ``torque_dto`` と整合する有効点 mask
            （逆算結果の ``power_series_mask`` にそのまま流用する）。
    """
    if curve_loaded.power is not None:
        unit = _reject_ratio_unit_or_raise(curve_loaded.power_unit, "power")
        power_arr = np.asarray(curve_loaded.power, dtype=np.float64)
        placeholder, mask = _split_value_and_mask(
            power_arr,
            label="power_series",
        )
        return ArrayActivePowerDto(value=placeholder, unit=unit), mask
    if torque_dto is None or torque_mask is None:
        return None, None
    torque_nm_si = np.asarray(
        torque_dto.to_base_unit().get_value(),
        dtype=np.float64,
    )
    power_w = torque_nm_si * _omega_rad_s_from_rpm(rpm_arr)
    return ArrayActivePowerDto(value=power_w, unit="W"), torque_mask


def _resolve_current_series(
    curve_loaded: ImPerformanceCurveLoadedData,
) -> tuple[ArrayCurrentMagnitudeDto | None, np.ndarray | None]:
    """``current_series`` と ``current_series_mask`` を解決する。

    本ビルダー段では ``current`` 列の単位は ``A`` / ``kA`` / ``mA``
    の絶対単位のみ許容する。``-`` / ``%`` （定格電流に対する比率）は
    :class:`ValueError` で弾く（モジュール docstring 参照）。
    NaN セルは 0 (A) プレースホルダ + mask=False。
    """
    if curve_loaded.current is None or curve_loaded.current_unit is None:
        return None, None
    unit = _reject_ratio_unit_or_raise(curve_loaded.current_unit, "current")
    current_arr = np.asarray(curve_loaded.current, dtype=np.float64)
    placeholder, mask = _split_value_and_mask(
        current_arr,
        label="current_series",
    )
    return ArrayCurrentMagnitudeDto(value=placeholder, unit=unit), mask


def _resolve_power_factor_series(
    curve_loaded: ImPerformanceCurveLoadedData,
) -> tuple[ArrayPowerFactorDto | None, np.ndarray | None]:
    if (
        curve_loaded.power_factor is None
        or curve_loaded.power_factor_unit is None
    ):
        return None, None
    pf_arr = np.asarray(curve_loaded.power_factor, dtype=np.float64)
    placeholder, mask = _split_value_and_mask(
        pf_arr,
        label="power_factor_series",
    )
    dto = ArrayPowerFactorDto(
        value=placeholder,
        unit=normalize_loaded_unit_cell(curve_loaded.power_factor_unit),
    )
    return dto, mask


def _resolve_efficiency_series(
    curve_loaded: ImPerformanceCurveLoadedData,
) -> tuple[ArrayEfficiencyDto | None, np.ndarray | None]:
    if curve_loaded.efficiency is None or curve_loaded.efficiency_unit is None:
        return None, None
    eta_arr = np.asarray(curve_loaded.efficiency, dtype=np.float64)
    placeholder, mask = _split_value_and_mask(
        eta_arr,
        label="efficiency_series",
    )
    dto = ArrayEfficiencyDto(
        value=placeholder,
        unit=normalize_loaded_unit_cell(curve_loaded.efficiency_unit),
    )
    return dto, mask


def build_im_performance_curve_catalogs(
    curve_loaded: ImPerformanceCurveLoadedData | None,
) -> ImPerformanceCurveCatalogDtos:
    """性能曲線中間表現からカタログ DTO 群を構築する。

    曲線 TSV に欠落していた列は対応する DTO 系列を作らず ``None`` の
    まま残す。``torque`` 列があれば ``torque_series`` として
    そのまま catalog DTO に保持する。``power`` が無く ``torque`` 列だけ
    あるケースでは ``power_w = T·ω`` を逆算して ``power_series`` も併せて
    埋める（下流が ``power_series`` を必要とするため）。

    観測列の **空セル (NaN)** は assembler 側で 0 プレースホルダに置換し、
    元の有効点 mask を ``*_series_mask`` として Catalog DTO に保存する
    （Generic ``Array*Dto`` の NaN/inf 禁止契約は維持する。``inf`` は
    検出時点で :class:`ValueError`）。

    ``power`` と ``torque`` の整合性検証
    （``P = T·ω`` の要素ごと比較、mask=False 点はスキップ）は
    :class:`ImPerformanceCurveCatalogDto.__post_init__` 側で行う。

    Args:
        curve_loaded: 性能曲線中間表現。``None`` のときは空コレクション。

    Returns:
        ImPerformanceCurveCatalogDtos: カタログ DTO 群。
    """
    if curve_loaded is None:
        return ImPerformanceCurveCatalogDtos(objects=[])

    rpm_arr = np.asarray(curve_loaded.rotational_speed, dtype=np.float64)
    poles_int = _poles_as_positive_int(curve_loaded.poles)
    slip_arr = _derive_slip_from_rpm(
        rpm_arr=rpm_arr,
        poles=poles_int,
        supply_frequency_hz=curve_loaded.supply_frequency,
    )

    supply_f = curve_loaded.supply_frequency
    supply_v = curve_loaded.supply_voltage
    dto_name = (
        f"{curve_loaded.name}_{int(round(supply_f))}Hz_{int(round(supply_v))}V"
    )

    torque_dto, torque_mask = _resolve_torque_series(curve_loaded)
    power_dto, power_mask = _resolve_power_series(
        curve_loaded=curve_loaded,
        rpm_arr=rpm_arr,
        torque_dto=torque_dto,
        torque_mask=torque_mask,
    )
    current_dto, current_mask = _resolve_current_series(curve_loaded)
    pf_dto, pf_mask = _resolve_power_factor_series(curve_loaded)
    eta_dto, eta_mask = _resolve_efficiency_series(curve_loaded)

    catalog_dto = ImPerformanceCurveCatalogDto(
        name=dto_name,
        supply_frequency=FloatFrequencyDto(
            value=supply_f,
            unit=normalize_loaded_unit_cell(curve_loaded.supply_frequency_unit),
        ),
        supply_voltage=FloatVoltageDto(
            value=supply_v,
            unit=normalize_loaded_unit_cell(curve_loaded.supply_voltage_unit),
        ),
        slip_series=ArraySlipDto(value=slip_arr, unit="-"),
        power_series=power_dto,
        torque_series=torque_dto,
        current_series=current_dto,
        power_factor_series=pf_dto,
        efficiency_series=eta_dto,
        rotational_speed_series=ArrayRotationalSpeedDto(
            value=rpm_arr,
            unit=normalize_loaded_unit_cell(curve_loaded.rotational_speed_unit),
        ),
        power_series_mask=power_mask,
        torque_series_mask=torque_mask,
        current_series_mask=current_mask,
        power_factor_series_mask=pf_mask,
        efficiency_series_mask=eta_mask,
    )
    return ImPerformanceCurveCatalogDtos(objects=[catalog_dto])
