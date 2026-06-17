"""統合 estimate_params TSV のテキストパース（algorithm 層）。

統合 TSV のセクション構成:

1. ``im_performance_curve_name`` 行
2. ``nameplate`` セクション（``name, value, unit``）。
   IM 銘板（``input_line_voltage`` / ``input_line_current`` / ``output_power``
   / ``frequency``）を value-unit 表で保持する。
3. ``fixed_model_key`` セクション（key/value/unit）。``cable_length`` などの
   固定値を value と unit に分けたまま保持する。
4. ``model_candidate_axis`` セクション。一次・励磁・二次（single/double_inner
   /double_outer）・ケーブル導体の候補ラベルを **厳密に一致** で振り分ける。
   ``single`` と ``double_*`` が **同時に指定** されているときは、両方を
   独立した二次軸として保持する（直積展開時に単一かご run と二重かご run
   の両方が生成される）。``double_inner`` と ``double_outer`` は同時に
   指定する必要があり、片方だけだとエラー。
5. ``supply`` セクション（``name, value, unit``）。供給電源の ``frequency`` /
   ``voltage`` を value-unit 表で保持する。
6. 性能曲線ヘッダ・単位行・データ行。

``nameplate`` と ``supply`` は **別セクション** として扱う。両者で同じ行キー
（例: ``frequency``）が現れても衝突しないよう、パース後は別の dict に格納
する（``nameplate_block`` / ``supply_block``）。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from im_cable_system.engine.algorithm.input_algorithm.load_data.util import (
    read_csv_rows,
)

_PERF_CURVE_NAME_KEY = "im_performance_curve_name"
_NAMEPLATE_HEADER = "nameplate"
_SUPPLY_HEADER = "supply"
_FIXED_HEADER = "fixed_model_key"
_CANDIDATE_HEADER = "model_candidate_axis"

_VALUE_HEADER = "value"
_UNIT_HEADER = "unit"

_CANDIDATE_AXIS_LABELS = {
    "im_primary": "primary",
    "im_excitation": "excitation",
    "im_secondary(single)": "secondary_single",
    "im_secondary(double_inner)": "secondary_double_inner",
    "im_secondary(double_outer)": "secondary_double_outer",
    "cable_conductor_model": "cable_conductor",
}


@dataclass(frozen=True)
class FixedCell:
    """``fixed_model_key`` セクションの 1 セル。

    Attributes:
        value: ``float()`` 変換前の値文字列（``strip`` 済み）。
        unit: 単位文字列（無いときは ``None``）。
    """

    value: str
    unit: str | None


def _strip_cell(raw: str) -> str:
    return raw.strip()


def _is_blank_row(row: list[str]) -> bool:
    return not row or all(_strip_cell(c) == "" for c in row)


def _is_value_unit_block_header(row: list[str], section_name: str) -> bool:
    """``section_name, value, unit`` のヘッダ行か判定する。"""
    if len(row) < 3:
        return False
    header = [_strip_cell(c).lower() for c in row[:3]]
    return (
        header[0] == section_name
        and header[1] == _VALUE_HEADER
        and header[2] == _UNIT_HEADER
    )


def _parse_value_unit_block(
    rows: list[list[str]],
    start_idx: int,
) -> tuple[dict[str, tuple[float, str]], int]:
    """value-unit 表（ヘッダ行の **直後**）を読む。

    呼び出し側で ``rows[start_idx - 1]`` がヘッダ行であることを確認済み
    の前提。本関数はヘッダ直後のデータ行から走査する。
    """
    idx = start_idx
    out: dict[str, tuple[float, str]] = {}
    while idx < len(rows):
        row = rows[idx]
        if _is_blank_row(row):
            idx += 1
            break
        if len(row) < 2:
            idx += 1
            continue
        key = _strip_cell(row[0])
        if key == "":
            idx += 1
            continue
        val_cell = _strip_cell(row[1])
        unit_cell = _strip_cell(row[2]) if len(row) > 2 else ""
        unit_clean = unit_cell
        if unit_cell.startswith("[") and unit_cell.endswith("]"):
            unit_clean = unit_cell[1:-1].strip()
        try:
            val_f = float(val_cell)
        except ValueError:
            idx += 1
            continue
        out[key] = (val_f, unit_clean)
        idx += 1
    return out, idx


def _find_value_unit_block(
    rows: list[list[str]],
    section_name: str,
) -> dict[str, tuple[float, str]]:
    """``section_name, value, unit`` ブロックを探して中身を返す。

    Args:
        rows: TSV の全行。
        section_name: ``nameplate`` / ``supply`` 等のセクション名（小文字）。

    Returns:
        ブロック内の ``{key: (value, unit)}`` 辞書。

    Raises:
        ValueError: 該当セクションが TSV 中に見つからない、または重複している。
    """
    header_indices = [
        idx
        for idx, row in enumerate(rows)
        if row and _is_value_unit_block_header(row, section_name)
    ]
    if not header_indices:
        raise ValueError(
            f"統合 TSV に {section_name!r} セクションがありません。"
        )
    if len(header_indices) > 1:
        raise ValueError(
            f"統合 TSV に {section_name!r} セクションが {len(header_indices)} "
            f"回現れます（重複）。"
        )
    block, _ = _parse_value_unit_block(rows, header_indices[0] + 1)
    return block


def _parse_fixed_key_value_block(
    rows: list[list[str]],
    start_idx: int,
) -> tuple[dict[str, FixedCell], int]:
    """``fixed_model_key`` セクションを value と unit の組で読む。"""
    idx = start_idx
    if idx >= len(rows) or _strip_cell(rows[idx][0]) != _FIXED_HEADER:
        return {}, idx
    idx += 1
    out: dict[str, FixedCell] = {}
    while idx < len(rows):
        row = rows[idx]
        if _is_blank_row(row):
            idx += 1
            break
        key = _strip_cell(row[0]) if row else ""
        if key == "":
            idx += 1
            continue
        val_cell = _strip_cell(row[1]) if len(row) > 1 else ""
        unit_cell = _strip_cell(row[2]) if len(row) > 2 else ""
        out[key] = FixedCell(
            value=val_cell,
            unit=unit_cell if unit_cell != "" else None,
        )
        idx += 1
    return out, idx


def _candidate_tokens(row: list[str]) -> tuple[str, ...]:
    if len(row) < 2:
        return ()
    tokens: list[str] = []
    for cell in row[1:]:
        t = _strip_cell(cell)
        if t != "":
            tokens.append(t)
    return tuple(tokens)


def _find_curve_header_index(rows: list[list[str]]) -> int:
    for idx, row in enumerate(rows):
        if not row:
            continue
        first = _strip_cell(row[0]).lower()
        if first == "rotational_speed":
            return idx
    raise ValueError(
        "統合 TSV に rotational_speed を含む曲線ヘッダ行がありません。"
    )


@dataclass(frozen=True)
class EstimateParamsParsedTables:
    """パース結果（性能カーブ名・銘板・固定・候補・供給・曲線表）。

    Attributes:
        im_performance_curve_name: 性能曲線識別子。
        nameplate_block: ``nameplate`` セクションの ``{key: (value, unit)}``。
            必須行は ``input_line_voltage`` / ``input_line_current`` /
            ``output_power`` / ``frequency``。
        fixed: ``fixed_model_key`` セクションの ``{key: FixedCell}``。
        candidate_primary: ``model_candidate_axis`` の ``im_primary`` 候補。
        candidate_excitation: ``model_candidate_axis`` の ``im_excitation``
            候補。
        candidate_secondary_single: ``im_secondary(single)`` 候補
            （単一かご探索用、空のとき単一かご探索を行わない）。
        candidate_secondary_double_inner: ``im_secondary(double_inner)``
            候補（二重かご探索の内側、空のとき二重かご探索を行わない）。
        candidate_secondary_double_outer: ``im_secondary(double_outer)``
            候補（二重かご探索の外側、空のとき二重かご探索を行わない）。
        candidate_cable_conductor: ``cable_conductor_model`` 候補。
        supply_block: ``supply`` セクションの ``{key: (value, unit)}``。
            必須行は ``frequency`` / ``voltage``。
        curve_*: 性能曲線テーブルのヘッダ／単位／データ行。

    Note:
        ``single`` と ``double_*`` が **同時に指定される**ことを許容する。
        その場合は単一かご run と二重かご run の両方が直積展開され、
        :func:`...cartesian_product.iter_model_combos` がそれぞれの run
        分の :class:`EstimateParamsModelCombo` を yield する。
    """

    im_performance_curve_name: str
    nameplate_block: dict[str, tuple[float, str]]
    fixed: dict[str, FixedCell]
    candidate_primary: tuple[str, ...]
    candidate_excitation: tuple[str, ...]
    candidate_secondary_single: tuple[str, ...]
    candidate_secondary_double_inner: tuple[str, ...]
    candidate_secondary_double_outer: tuple[str, ...]
    candidate_cable_conductor: tuple[str, ...]
    supply_block: dict[str, tuple[float, str]]
    curve_header_row: list[str]
    curve_unit_row: list[str]
    curve_data_rows: list[list[str]]


def _find_perf_curve_name(rows: list[list[str]], path: Path) -> str:
    if not rows or not rows[0]:
        raise ValueError(f"CSV が空です: {path}")
    if _strip_cell(rows[0][0]) != _PERF_CURVE_NAME_KEY:
        raise ValueError(
            f"1行目は {_PERF_CURVE_NAME_KEY} である必要があります: {path}"
        )
    perf_name = _strip_cell(rows[0][1]) if len(rows[0]) > 1 else ""
    if perf_name == "":
        raise ValueError("im_performance_curve_name の値が空です。")
    return perf_name


def _find_fixed_section_start(rows: list[list[str]]) -> int:
    for idx, row in enumerate(rows):
        if row and _strip_cell(row[0]) == _FIXED_HEADER:
            return idx
    raise ValueError(f"{_FIXED_HEADER} セクションがありません。")


def _skip_blank_rows(rows: list[list[str]], start_idx: int) -> int:
    idx = start_idx
    while idx < len(rows) and _is_blank_row(rows[idx]):
        idx += 1
    return idx


@dataclass(frozen=True)
class _CandidateAxes:
    primary: tuple[str, ...] = ()
    excitation: tuple[str, ...] = ()
    secondary_single: tuple[str, ...] = ()
    secondary_double_inner: tuple[str, ...] = ()
    secondary_double_outer: tuple[str, ...] = ()
    cable_conductor: tuple[str, ...] = ()


def _parse_candidate_axes_block(
    rows: list[list[str]],
    start_idx: int,
) -> tuple[_CandidateAxes, int]:
    """``model_candidate_axis`` セクションを **厳密一致** で振り分ける。

    各ラベル（``im_secondary(single)`` / ``im_secondary(double_inner)`` /
    ``im_secondary(double_outer)`` 含む）は **それぞれ独立した軸** として
    分離して保持する。同じラベルが 2 行以上現れた場合は重複として
    :class:`ValueError`。
    """
    if (
        start_idx >= len(rows)
        or _strip_cell(rows[start_idx][0]) != _CANDIDATE_HEADER
    ):
        raise ValueError(f"{_CANDIDATE_HEADER} 行がありません。")
    idx = start_idx + 1
    axes: dict[str, tuple[str, ...]] = {}
    while idx < len(rows):
        row = rows[idx]
        if _is_blank_row(row):
            idx += 1
            break
        label = _strip_cell(row[0])
        axis_key = _CANDIDATE_AXIS_LABELS.get(label)
        if axis_key is None:
            raise ValueError(
                f"{_CANDIDATE_HEADER} に未知のラベル {label!r} があります。"
                f"許可ラベル: {sorted(_CANDIDATE_AXIS_LABELS)!r}"
            )
        tokens = _candidate_tokens(row)
        if tokens:
            if axis_key in axes:
                raise ValueError(
                    f"{_CANDIDATE_HEADER} に同じ軸 {axis_key!r} の行が"
                    f"重複しています（ラベル {label!r}）。"
                )
            axes[axis_key] = tokens
        idx += 1
    return (
        _CandidateAxes(
            primary=axes.get("primary", ()),
            excitation=axes.get("excitation", ()),
            secondary_single=axes.get("secondary_single", ()),
            secondary_double_inner=axes.get("secondary_double_inner", ()),
            secondary_double_outer=axes.get("secondary_double_outer", ()),
            cable_conductor=axes.get("cable_conductor", ()),
        ),
        idx,
    )


def parse_unified_estimate_params_csv(
    path: Path,
) -> EstimateParamsParsedTables:
    """統合 CSV を読み、カタログ構築用メタと候補軸を返す。"""
    rows = read_csv_rows(path)
    perf_name = _find_perf_curve_name(rows, path)

    nameplate_block = _find_value_unit_block(rows, _NAMEPLATE_HEADER)
    supply_block = _find_value_unit_block(rows, _SUPPLY_HEADER)

    fixed_start = _find_fixed_section_start(rows)
    fixed, idx_after_fixed = _parse_fixed_key_value_block(rows, fixed_start)
    idx_after_blanks = _skip_blank_rows(rows, idx_after_fixed)
    candidate_axes, _ = _parse_candidate_axes_block(rows, idx_after_blanks)

    _validate_required_candidate_axes(candidate_axes)

    curve_idx = _find_curve_header_index(rows)
    unit_row_idx = curve_idx + 1
    if unit_row_idx >= len(rows):
        raise ValueError("曲線単位行がありません。")

    return EstimateParamsParsedTables(
        im_performance_curve_name=perf_name,
        nameplate_block=nameplate_block,
        fixed=fixed,
        candidate_primary=candidate_axes.primary,
        candidate_excitation=candidate_axes.excitation,
        candidate_secondary_single=candidate_axes.secondary_single,
        candidate_secondary_double_inner=candidate_axes.secondary_double_inner,
        candidate_secondary_double_outer=candidate_axes.secondary_double_outer,
        candidate_cable_conductor=candidate_axes.cable_conductor,
        supply_block=supply_block,
        curve_header_row=rows[curve_idx],
        curve_unit_row=rows[unit_row_idx],
        curve_data_rows=rows[unit_row_idx + 1 :],
    )


def _validate_required_candidate_axes(axes: _CandidateAxes) -> None:
    """``primary`` / ``excitation`` および二次軸の必須条件を検証する。

    二次軸は ``single`` または ``(double_inner AND double_outer)`` の
    どちらか少なくとも一方が指定されている必要がある。``double_inner``
    と ``double_outer`` は **同時に指定** する必要があり、片方だけ
    指定するとエラー。
    """
    if not axes.primary:
        raise ValueError(
            "model_candidate_axis に im_primary 候補がありません。"
        )
    if not axes.excitation:
        raise ValueError(
            "model_candidate_axis に im_excitation 候補がありません。"
        )
    has_single = len(axes.secondary_single) > 0
    has_inner = len(axes.secondary_double_inner) > 0
    has_outer = len(axes.secondary_double_outer) > 0
    if has_inner != has_outer:
        raise ValueError(
            "model_candidate_axis の im_secondary(double_inner) と "
            "im_secondary(double_outer) は同時に指定する必要があります。"
        )
    if not has_single and not (has_inner and has_outer):
        raise ValueError(
            "model_candidate_axis には im_secondary(single)、または "
            "im_secondary(double_inner) と im_secondary(double_outer) の"
            "両方のいずれかを指定する必要があります。"
        )
