"""性能曲線 TSV のパース（Forward 系で共通）。

メタブロック ``name,value,unit`` で ``poles`` / ``supply_frequency`` /
``supply_voltage`` を保持し、曲線テーブルは ``rotational_speed`` を主とする。
テーブルに ``slip`` 列は持たない。スリップ導出は ``assemble_input_dto`` 層で
``poles`` と ``supply_frequency`` から行う。

列要件:
    曲線ヘッダには ``rotational_speed`` が必須で、加えて ``power`` /
    ``current`` / ``power_factor`` / ``efficiency`` / ``torque`` のうち
    少なくとも 1 本が必要。欠落している列は ``ImPerformanceCurveLoadedData``
    の対応フィールドが ``None`` になり、後段 ``assemble_input_dto`` で
    DTO 系列を作らずに済ませる。

セル単位の欠損 (NaN) の扱い:
    観測列（``power`` / ``current`` / ``power_factor`` / ``efficiency`` /
    ``torque``）の **空セルは ``np.nan`` として保持** する（未観測点。
    後段 ``assemble_input_dto`` で 0 埋め + mask 配列に変換）。
    ``rotational_speed`` セルは独立軸として **空セル禁止**
    （空セル行はスキップ）。``float()`` 変換失敗（``"abc"`` 等）は
    ``ValueError`` のままとする。

単位文字列は ``strip()`` のみで保持する。``[Hz]`` 等の角括弧除去、
``poles`` の正整数性、空配列・空セルなどの値レベル検証は
``assemble_input_dto`` 段の DTO ``__post_init__`` および
``_validate_input_dto`` に寄せる。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import numpy as np

from im_cable_system.engine.algorithm.input_algorithm.load_data.data_class.im_performance_curve_loaded_data import (  # noqa: E501
    ImPerformanceCurveLoadedData,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data.util import (  # noqa: E501
    read_csv_rows,
)

_META_KEY_CURVE_NAME = "im_performance_curve_name"
_META_TABLE_HEADER = ("name", "value", "unit")
_CURVE_PRIMARY_COLUMN = "rotational_speed"
_CURVE_OPTIONAL_COLUMNS = (
    "power",
    "current",
    "power_factor",
    "efficiency",
    "torque",
)


def _parse_supply_meta_block(
    file_path: Path,
    rows: list[list[str]],
    start_idx: int,
) -> tuple[dict[str, Any], int]:
    idx = start_idx
    if idx >= len(rows) or not rows[idx] or not rows[idx][0].strip():
        raise ValueError(
            f"性能曲線 CSV は {_META_KEY_CURVE_NAME} 行から始まる必要があります: "
            f"{file_path}"
        )
    key0 = rows[idx][0].strip()
    if key0 != _META_KEY_CURVE_NAME:
        raise ValueError(
            f"性能曲線 CSV の1行目は {_META_KEY_CURVE_NAME} である必要があります: "
            f"先頭キー={key0!r}"
        )
    val0 = rows[idx][1].strip() if len(rows[idx]) > 1 else ""
    if val0 == "":
        raise ValueError(f"{_META_KEY_CURVE_NAME} の値が空です。")
    meta: dict[str, Any] = {_META_KEY_CURVE_NAME: val0}
    idx += 1

    if idx >= len(rows):
        raise ValueError("性能曲線 CSV にメタ表ヘッダがありません。")
    header = [c.strip() for c in rows[idx]]
    if tuple(header[:3]) != _META_TABLE_HEADER:
        raise ValueError(
            "性能曲線 CSV のメタ表は name,value,unit 行の直後である必要があります。"
        )
    idx += 1

    while idx < len(rows):
        row = rows[idx]
        if not row or all(c.strip() == "" for c in row):
            idx += 1
            break
        if len(row) < 3:
            raise ValueError(
                f"メタ表の各行は name,value,unit の3列が必要です: 行={row!r}"
            )
        name = row[0].strip()
        if name == "":
            raise ValueError(
                f"性能曲線 CSV のメタ表に name セルが空の行があります: "
                f"行={row!r}: {file_path}"
            )
        if name in meta:
            raise ValueError(
                f"性能曲線 CSV のメタ表にキー {name!r} が重複しています: "
                f"{file_path}"
            )
        val_cell = row[1].strip()
        unit_cell = row[2].strip()
        meta[name] = (float(val_cell), unit_cell)
        idx += 1
    else:
        raise ValueError(
            f"性能曲線 CSV のメタ表のあとに空行が必要です: {file_path}"
        )

    while idx < len(rows) and (
        not rows[idx] or all(c.strip() == "" for c in rows[idx])
    ):
        idx += 1
    return meta, idx


def _find_curve_indices(header: list[str]) -> dict[str, int]:
    """曲線ヘッダから列番号を解決する。

    ``rotational_speed`` は必須、その他は optional。少なくとも 1 本の
    optional 列（power / current / power_factor / efficiency / torque）が
    無いと残差・プロットいずれにも使えないため ``ValueError`` を上げる。
    重複列も ``ValueError``。
    """
    header_stripped = [h.strip() for h in header]
    for col in (_CURVE_PRIMARY_COLUMN, *_CURVE_OPTIONAL_COLUMNS):
        if header_stripped.count(col) > 1:
            raise ValueError(
                f"性能曲線ヘッダに列 {col!r} が複数あります: {header_stripped}"
            )
    if _CURVE_PRIMARY_COLUMN not in header_stripped:
        raise ValueError(
            f"性能曲線ヘッダに必須列 {_CURVE_PRIMARY_COLUMN!r} がありません: "
            f"{header_stripped}"
        )
    indices: dict[str, int] = {
        _CURVE_PRIMARY_COLUMN: header_stripped.index(_CURVE_PRIMARY_COLUMN),
    }
    for col in _CURVE_OPTIONAL_COLUMNS:
        if col in header_stripped:
            indices[col] = header_stripped.index(col)
    if not any(col in indices for col in _CURVE_OPTIONAL_COLUMNS):
        raise ValueError(
            f"性能曲線ヘッダには {_CURVE_PRIMARY_COLUMN} に加えて "
            f"{list(_CURVE_OPTIONAL_COLUMNS)!r} のうち少なくとも 1 列が必要です: "
            f"{header_stripped}"
        )
    return indices


def _curve_units_from_row(
    col: dict[str, int],
    unit_row: list[str],
) -> dict[str, str]:
    """単位行を ``strip`` のみで抽出する。

    ``col`` に含まれる列の単位文字列だけを返す。妥当性判定や ``[Hz]`` 等の
    正規化は行わず、``assemble_input_dto`` 層に任せる。
    """
    units: dict[str, str] = {}
    for key, idx in col.items():
        units[key] = unit_row[idx].strip() if len(unit_row) > idx else ""
    return units


def _curve_table_cell(row: list[str], idx_col: int) -> str:
    return row[idx_col].strip() if len(row) > idx_col else ""


def _read_curve_arrays(
    data_rows: list[list[str]],
    col: dict[str, int],
) -> dict[str, np.ndarray]:
    """``col`` で指示された列だけを 1 次元 ``float64`` 配列に読む。

    ``rotational_speed`` 以外の列は optional。観測列（``power`` /
    ``current`` / ``power_factor`` / ``efficiency`` / ``torque``）の
    空セルは ``np.nan`` として保持する（未観測点を表す）。``float()``
    変換に失敗する非空セル（``"abc"`` 等）は従来通り ``ValueError``。

    ``rotational_speed`` セルが空の行はスキップする（独立軸として
    未観測点を許容しない）。
    """
    keys = [_CURVE_PRIMARY_COLUMN] + [
        c for c in _CURVE_OPTIONAL_COLUMNS if c in col
    ]
    buffers: dict[str, list[float]] = {k: [] for k in keys}

    for row in data_rows:
        if not row or all(c.strip() == "" for c in row):
            continue
        rpm_cell = _curve_table_cell(row, col[_CURVE_PRIMARY_COLUMN])
        if rpm_cell == "":
            continue
        buffers[_CURVE_PRIMARY_COLUMN].append(float(rpm_cell))
        for k in keys:
            if k == _CURVE_PRIMARY_COLUMN:
                continue
            cell = _curve_table_cell(row, col[k])
            if cell == "":
                buffers[k].append(np.nan)
            else:
                buffers[k].append(float(cell))

    return {k: np.array(v, dtype=np.float64) for k, v in buffers.items()}


def _require_meta_scalar(
    meta: dict[str, Any],
    key: str,
) -> tuple[float, str]:
    if key not in meta:
        raise ValueError(f"性能曲線メタに {key!r} が必要です。")
    return cast(tuple[float, str], meta[key])


def parse_performance_curve_optional(
    path: Path | None,
) -> ImPerformanceCurveLoadedData | None:
    """性能曲線 TSV を中間表現にパースする（未指定時は ``None``）。

    Args:
        path: 性能曲線ファイルパス。``None`` のときは ``None`` を返す。

    Returns:
        ImPerformanceCurveLoadedData | None: パース結果。

    Raises:
        ValueError: ``im_performance_curve_name`` 行不在、メタ表ヘッダ
            ``name,value,unit`` 不在、必須メタキー
            （``poles`` / ``supply_frequency`` / ``supply_voltage``）
            欠落、曲線ヘッダの ``rotational_speed`` 欠落、曲線ヘッダで
            ``power`` / ``current`` / ``power_factor`` / ``efficiency`` /
            ``torque`` のいずれも無い、曲線ヘッダ・単位行の不足、
            ``float()`` 変換失敗（観測列の空セルは ``np.nan`` として
            保持され ``ValueError`` にしない）のいずれかが起きた場合。
    """
    if path is None:
        return None

    rows = read_csv_rows(path)
    meta, curve_start = _parse_supply_meta_block(path, rows, 0)
    curve_name = cast(str, meta[_META_KEY_CURVE_NAME])
    poles_value, _poles_unit = _require_meta_scalar(meta, "poles")
    supply_f_hz, supply_f_unit = _require_meta_scalar(meta, "supply_frequency")
    supply_v, supply_v_unit = _require_meta_scalar(meta, "supply_voltage")

    if curve_start >= len(rows):
        raise ValueError("性能曲線 CSV に曲線ヘッダがありません。")
    header = rows[curve_start]
    unit_row_idx = curve_start + 1
    if unit_row_idx >= len(rows):
        raise ValueError("性能曲線 CSV に単位行がありません。")
    col = _find_curve_indices(header)
    units = _curve_units_from_row(col=col, unit_row=rows[unit_row_idx])
    data_rows = rows[unit_row_idx + 1 :]
    arrays = _read_curve_arrays(data_rows=data_rows, col=col)

    return ImPerformanceCurveLoadedData(
        name=curve_name,
        poles=float(poles_value),
        supply_frequency=supply_f_hz,
        supply_frequency_unit=supply_f_unit,
        supply_voltage=supply_v,
        supply_voltage_unit=supply_v_unit,
        rotational_speed=arrays[_CURVE_PRIMARY_COLUMN],
        rotational_speed_unit=units[_CURVE_PRIMARY_COLUMN],
        power=arrays.get("power"),
        power_unit=units.get("power"),
        current=arrays.get("current"),
        current_unit=units.get("current"),
        power_factor=arrays.get("power_factor"),
        power_factor_unit=units.get("power_factor"),
        efficiency=arrays.get("efficiency"),
        efficiency_unit=units.get("efficiency"),
        torque=arrays.get("torque"),
        torque_unit=units.get("torque"),
    )
