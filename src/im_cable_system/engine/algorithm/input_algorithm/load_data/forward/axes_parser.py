"""評価点軸 TSV のパース（Forward 系で共通）。

CartesianGrid モードと OperatingPoints モードで、軸 TSV のレイアウトは
異なるが、本パーサはモードに依存せず **列ごとに空でないセルを集めて
1 次元配列にする** という単一の解釈で両者を読む。

- ``slip`` / ``frequency`` / ``input_line_voltage`` の各列について、
  空でないセルだけを抽出し、登場順を保ったまま 1 次元 ``np.ndarray`` に
  詰める。重複排除は行わない。
- 結果として、列ごとの長さは異なってよい。CartesianGrid 用ファイル
  （非スリップ列に空セルが多い）でも、OperatingPoints 用ファイル
  （3 列すべて埋まる co-indexed の運転点列）でも、同じ手順で読める。
- 直積か co-indexed かの解釈は ``assemble_input_dto`` 段の
  ``reference_axes`` 指定で表現する。本パーサは関与しない。
- 単位セル・値域・空配列の妥当性判定は行わず、入力ファイルの文字列を
  ``strip`` した値と ``float()`` 変換した数値だけを保持する。値レベルの
  検証は DTO ``__post_init__`` および ``_validate_input_dto`` に寄せる。
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from im_cable_system.engine.algorithm.input_algorithm.load_data.data_class.axes_loaded_data import (  # noqa: E501
    AxesLoadedData,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data.util import (  # noqa: E501
    read_csv_rows,
)

_REQUIRED_AXES_COLUMNS = ("slip", "frequency", "input_line_voltage")


def _axes_units_from_row(
    unit_row: list[str],
    idx_slip: int,
    idx_freq: int,
    idx_volt: int,
) -> tuple[str, str, str]:
    slip_unit = unit_row[idx_slip].strip() if len(unit_row) > idx_slip else ""
    freq_unit = unit_row[idx_freq].strip() if len(unit_row) > idx_freq else ""
    volt_unit = unit_row[idx_volt].strip() if len(unit_row) > idx_volt else ""
    return slip_unit, freq_unit, volt_unit


def _resolve_axes_column_indices(
    header: list[str],
    path: Path,
) -> tuple[int, int, int]:
    """必須 3 列の列番号を取り出し、重複列・欠落列を ``ValueError`` 化する。"""
    for col in _REQUIRED_AXES_COLUMNS:
        count = header.count(col)
        if count > 1:
            raise ValueError(
                f"軸 TSV のヘッダに必須列 {col!r} が複数あります: {path}"
            )
    try:
        idx_slip = header.index("slip")
        idx_freq = header.index("frequency")
        idx_volt = header.index("input_line_voltage")
    except ValueError as exc:
        raise ValueError(f"軸 TSV に必須列がありません: {path}") from exc
    return idx_slip, idx_freq, idx_volt


def parse_axes(path: Path) -> AxesLoadedData:
    """Forward 系の軸 TSV をパースする（モード非依存）。

    各列について空でないセルを行順に集め、それぞれ独立した 1 次元配列
    として保持する。重複排除は行わない。列ごとの長さは異なってよい。

    Args:
        path: 軸ファイルパス（``ForwardJobSpec.axes_path``）。

    Returns:
        AxesLoadedData: 各列を独立な 1 次元配列として持つ中間表現。
        単位文字列は ``strip`` のみ適用した生文字列。

    Raises:
        ValueError: ヘッダ・単位行・データ行のいずれかが不足する、
            必須 3 列（``slip`` / ``frequency`` /
            ``input_line_voltage``）が欠落 / 重複している、データ行の
            幅が必須 3 列を満たさない（空行は除く）、あるいは
            ``float()`` 変換に失敗した場合。
    """
    rows = read_csv_rows(path)
    if len(rows) < 3:
        raise ValueError(
            f"軸 TSV にはヘッダ・単位行・データ行が必要です: {path}"
        )
    header = [cell.strip() for cell in rows[0]]
    idx_slip, idx_freq, idx_volt = _resolve_axes_column_indices(header, path)

    slip_unit, freq_unit, volt_unit = _axes_units_from_row(
        rows[1],
        idx_slip,
        idx_freq,
        idx_volt,
    )

    slip_values: list[float] = []
    freq_values: list[float] = []
    volt_values: list[float] = []

    max_required = max(idx_slip, idx_freq, idx_volt)
    for row in rows[2:]:
        if not row or all(c.strip() == "" for c in row):
            continue
        if len(row) <= max_required:
            raise ValueError(
                f"軸 TSV のデータ行に必須 3 列を満たさない行があります: "
                f"行={row!r}: {path}"
            )
        slip_cell = row[idx_slip].strip()
        freq_cell = row[idx_freq].strip()
        volt_cell = row[idx_volt].strip()
        if slip_cell != "":
            slip_values.append(float(slip_cell))
        if freq_cell != "":
            freq_values.append(float(freq_cell))
        if volt_cell != "":
            volt_values.append(float(volt_cell))

    return AxesLoadedData(
        slip=np.array(slip_values, dtype=np.float64),
        frequency=np.array(freq_values, dtype=np.float64),
        input_line_voltage=np.array(volt_values, dtype=np.float64),
        slip_unit=slip_unit,
        frequency_unit=freq_unit,
        voltage_unit=volt_unit,
    )
