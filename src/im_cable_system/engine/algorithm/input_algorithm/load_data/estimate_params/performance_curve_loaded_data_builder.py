"""統合 TSV のメタ + 曲線表から ImPerformanceCurveLoadedData を構築する。

Forward 系の :func:`build_im_performance_curve_catalogs` がカタログ DTO 化を
担うのに合わせ、本モジュールでは中間表現の構築だけを行う。

曲線表は ``rotational_speed`` を必須とし、観測列（``power`` / ``current`` /
``power_factor`` / ``efficiency`` / ``torque``）は少なくとも 1 本あればよい。
欠落している観測列は ``None`` として保持し、どの系列を推定・比較に使うかは
DTO 化以降の層に委ねる。

観測列のセル単位欠損は **NaN として保持** する（未観測点。空セル → NaN）。
``rotational_speed`` セルだけは独立軸として空禁止（空セル行はスキップ）。
NaN→0 変換と mask 抽出は ``assemble_input_dto`` 段に委ねる。

TODO:
    現状の統合 TSV は ``supply`` セクションを **1 組（単一の周波数・電圧）**
    しか持てないため、本ビルダーが返すのも単一供給条件の性能曲線であり、
    最終的に ``ImPerformanceCurveCatalogDtos`` は 1 件のカタログになる。
    一方 Execute 側（``estimate_params`` の ``curve_grid_sampling``）は
    **複数の (frequency, voltage) カタログ**を grid 上で突き合わせて
    同時フィットできる設計になっている。複数供給条件の性能カーブを
    入力できるよう、TSV フォーマット／パーサ／本ビルダーを将来拡張する
    （例: supply ブロックと曲線表を供給条件ごとに複数持てる形式）。
"""

from __future__ import annotations

import numpy as np

from im_cable_system.engine.algorithm.input_algorithm.load_data.data_class.im_performance_curve_loaded_data import (  # noqa: E501
    ImPerformanceCurveLoadedData,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data.estimate_params.unified_input_parser import (  # noqa: E501
    EstimateParamsParsedTables,
)

_PRIMARY_COLUMN = "rotational_speed"
_OBSERVED_COLUMNS = (
    "power",
    "current",
    "power_factor",
    "efficiency",
    "torque",
)


def _strip_cells(row: list[str]) -> list[str]:
    return [cell.strip() for cell in row]


def _column_indices(header: list[str]) -> dict[str, int]:
    """ヘッダ行から列名 → インデックスの辞書を作る。"""
    stripped = _strip_cells(header)
    for name in (_PRIMARY_COLUMN, *_OBSERVED_COLUMNS):
        if stripped.count(name) > 1:
            raise ValueError(
                f"性能曲線ヘッダに列 {name!r} が複数あります: {stripped}"
            )
    if _PRIMARY_COLUMN not in stripped:
        raise ValueError(
            f"性能曲線ヘッダに必須列 {_PRIMARY_COLUMN!r} がありません: "
            f"{stripped}"
        )
    indices: dict[str, int] = {_PRIMARY_COLUMN: stripped.index(_PRIMARY_COLUMN)}
    for name in _OBSERVED_COLUMNS:
        if name in stripped:
            indices[name] = stripped.index(name)
    if not any(name in indices for name in _OBSERVED_COLUMNS):
        raise ValueError(
            f"性能曲線ヘッダには {_PRIMARY_COLUMN!r} に加えて "
            f"{list(_OBSERVED_COLUMNS)!r} のうち少なくとも 1 列が必要です: "
            f"{stripped}"
        )
    return indices


def _cell(row: list[str], idx: int) -> str:
    return row[idx].strip() if len(row) > idx else ""


def _primary_column_array(
    data_rows: list[list[str]],
    idx: int,
) -> np.ndarray:
    """``rotational_speed`` 列の値を読む（NaN/空セル禁止）。

    主軸として未観測値は許容しないため、空セルが見つかった場合はその
    行全体をスキップ（行ごと全空はスキップ）。値セルが空のときは
    ``ValueError``。``float()`` 変換失敗も ``ValueError``。
    """
    values: list[float] = []
    for row in data_rows:
        if not row or all(cell.strip() == "" for cell in row):
            continue
        cell = _cell(row, idx)
        if cell == "":
            raise ValueError(
                "性能曲線データ行の rotational_speed セルが空です。"
            )
        values.append(float(cell))
    return np.array(values, dtype=np.float64)


def _observed_column_array(
    *,
    data_rows: list[list[str]],
    col: dict[str, int],
    name: str,
) -> np.ndarray | None:
    """観測列を読む（空セル → ``np.nan``、非空かつ非数値は ``ValueError``）。

    ``name`` がヘッダに無い場合は ``None`` を返す。行ごと全空はスキップ。
    """
    if name not in col:
        return None
    values: list[float] = []
    idx = col[name]
    for row in data_rows:
        if not row or all(cell.strip() == "" for cell in row):
            continue
        cell = _cell(row, idx)
        if cell == "":
            values.append(np.nan)
        else:
            values.append(float(cell))
    return np.array(values, dtype=np.float64)


def _optional_unit(
    *,
    unit_row: list[str],
    col: dict[str, int],
    name: str,
) -> str | None:
    if name not in col:
        return None
    return _cell(unit_row, col[name])


def build_im_performance_curve_loaded_data(
    parsed: EstimateParamsParsedTables,
    poles: int,
) -> ImPerformanceCurveLoadedData:
    """統合 TSV のパース結果から性能曲線中間表現を組み立てる。

    Args:
        parsed: ``parse_unified_estimate_params_csv`` の戻り値。
        poles: 統合 TSV ``fixed_model_key`` の ``im_poles``。

    Returns:
        ImPerformanceCurveLoadedData: 性能曲線中間表現。

    Raises:
        ValueError: 下記いずれかを検出した場合。値レベルの妥当性
            （正値・有限性、単位文字列の表記揺れ吸収、配列長一致など）は
            本層では検査せず、DTO ``__post_init__`` と
            ``_validate_input_dto`` に寄せる。

            - ``supply`` セクションに必須キー ``frequency`` /
              ``voltage`` のいずれかが無い。
            - 性能曲線ヘッダで ``rotational_speed`` /
              ``power`` / ``current`` / ``power_factor`` /
              ``efficiency`` / ``torque`` のいずれかの列が重複している。
            - 必須列 ``rotational_speed`` が欠落
              （通常は :mod:`unified_input_parser` の曲線ヘッダ探索で
              先に検出されるため、本関数の二重チェックは防御的位置付け）。
            - 観測列 ``power`` / ``current`` / ``power_factor`` /
              ``efficiency`` / ``torque`` のいずれもヘッダに無い。
            - ``rotational_speed`` セルが空（独立軸として未観測点は
              不可）。
            - データ行の値セルが ``float()`` で数値に変換できない
              （観測列の **空セル** は ``np.nan`` として保持し
              ``ValueError`` にはしない）。
    """
    header = parsed.curve_header_row
    unit_row = parsed.curve_unit_row
    data_rows = parsed.curve_data_rows
    col = _column_indices(header)

    supply = parsed.supply_block
    if "frequency" not in supply or "voltage" not in supply:
        raise ValueError(
            f"統合 TSV supply セクションに必須キー 'frequency' / 'voltage' "
            f"がありません: {parsed.im_performance_curve_name}"
        )
    supply_freq_v, supply_freq_unit = supply["frequency"]
    supply_volt_v, supply_volt_unit = supply["voltage"]

    rpm = _primary_column_array(data_rows, col[_PRIMARY_COLUMN])
    power = _observed_column_array(data_rows=data_rows, col=col, name="power")
    current = _observed_column_array(
        data_rows=data_rows,
        col=col,
        name="current",
    )
    power_factor = _observed_column_array(
        data_rows=data_rows,
        col=col,
        name="power_factor",
    )
    efficiency = _observed_column_array(
        data_rows=data_rows,
        col=col,
        name="efficiency",
    )
    torque = _observed_column_array(data_rows=data_rows, col=col, name="torque")

    return ImPerformanceCurveLoadedData(
        name=parsed.im_performance_curve_name,
        poles=float(poles),
        supply_frequency=float(supply_freq_v),
        supply_frequency_unit=str(supply_freq_unit),
        supply_voltage=float(supply_volt_v),
        supply_voltage_unit=str(supply_volt_unit),
        rotational_speed=rpm,
        rotational_speed_unit=_cell(unit_row, col[_PRIMARY_COLUMN]),
        power=power,
        power_unit=_optional_unit(unit_row=unit_row, col=col, name="power"),
        current=current,
        current_unit=_optional_unit(unit_row=unit_row, col=col, name="current"),
        power_factor=power_factor,
        power_factor_unit=_optional_unit(
            unit_row=unit_row,
            col=col,
            name="power_factor",
        ),
        efficiency=efficiency,
        efficiency_unit=_optional_unit(
            unit_row=unit_row,
            col=col,
            name="efficiency",
        ),
        torque=torque,
        torque_unit=_optional_unit(unit_row=unit_row, col=col, name="torque"),
    )
