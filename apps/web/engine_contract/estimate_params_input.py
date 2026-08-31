"""統合 estimate_params 入力 CSV/TSV の候補軸検証と s≈0 警告判定。

これは engine の入出力ファイル契約の**写し**である。区切り文字判定
（``.tsv`` → タブ、それ以外 → カンマ）と必須軸ラベルは engine 側
（``csv_utils.csv_delimiter_for_path`` /
``unified_input_parser._CANDIDATE_AXIS_LABELS``）と揃える。写しが離れたら
``tests/test_apps/test_web/engine_contract/test_engine_contract_drift.py`` が落ちる。

候補（``model_candidate_axis``）は統合入力 CSV、境界・初期値は ``im_bounds``
YAML が正本で、どちらもプリセット選択で渡す。ここでは書き換えは行わない。

stdlib と ``yaml`` 以外に依存しない。HTTP / DB / engine は import しない。
"""

from __future__ import annotations

import csv
import io
from pathlib import Path

from apps.web.engine_contract.model_kinds import (
    CANDIDATE_AXIS_KINDS,
    CANDIDATE_BLOCK_HEADER,
    IM_FRICTION_WINDAGE_KINDS,
    IM_STRAY_LOAD_KINDS,
    REQUIRED_CANDIDATE_AXIS_LABELS,
)

_NEAR_ZERO_SLIP_ABS = 1.0e-3
_NAMEPLATE_HEADER = "nameplate"
_FIXED_HEADER = "fixed_model_key"
_CURVE_HEADER = "rotational_speed"
_FREQUENCY_KEY = "frequency"
_POLES_KEY = "im_poles"


def csv_delimiter_for_filename(filename: str) -> str:
    """拡張子に応じた区切り文字（engine の ``csv_delimiter_for_path`` と同じ規則）。"""
    if Path(filename).suffix.lower() == ".tsv":
        return "\t"
    return ","


def read_rows(content: bytes, *, filename: str) -> list[list[str]]:
    """バイト列を行リストへ読む。

    Args:
        content: アップロードされたファイル本体。
        filename: 区切り文字判定に使うファイル名（拡張子のみ見る）。

    Returns:
        セル文字列の行リスト。
    """
    text = content.decode("utf-8")
    delimiter = csv_delimiter_for_filename(filename)
    return list(csv.reader(io.StringIO(text), delimiter=delimiter))


def _strip_cell(raw: str) -> str:
    return raw.strip()


def _is_blank_row(row: list[str]) -> bool:
    return not row or all(_strip_cell(cell) == "" for cell in row)


def _candidate_tokens(row: list[str]) -> tuple[str, ...]:
    if len(row) < 2:
        return ()
    return tuple(
        token
        for token in (_strip_cell(cell) for cell in row[1:])
        if token != ""
    )


def _find_candidate_block(
    rows: list[list[str]],
) -> tuple[int, int] | None:
    """``model_candidate_axis`` ヘッダ行 index とブロック終端 index（排他）を返す。"""
    header_idx: int | None = None
    for idx, row in enumerate(rows):
        if row and _strip_cell(row[0]) == CANDIDATE_BLOCK_HEADER:
            header_idx = idx
            break
    if header_idx is None:
        return None
    end_idx = header_idx + 1
    while end_idx < len(rows) and not _is_blank_row(rows[end_idx]):
        end_idx += 1
    return header_idx, end_idx


def find_missing_required_axes(rows: list[list[str]]) -> list[str]:
    """必須候補軸のうち、行が無い／候補セルが全て空のラベルを返す。

    Args:
        rows: ``read_rows`` が返す形の行リスト。

    Returns:
        欠落している軸ラベル（``REQUIRED_CANDIDATE_AXIS_LABELS`` の順）。
    """
    present_with_tokens: set[str] = set()
    block = _find_candidate_block(rows)
    if block is not None:
        _header_idx, end_idx = block
        for row in rows[_header_idx + 1 : end_idx]:
            if _is_blank_row(row):
                continue
            label = _strip_cell(row[0])
            if label in REQUIRED_CANDIDATE_AXIS_LABELS and _candidate_tokens(
                row
            ):
                present_with_tokens.add(label)
    return [
        label
        for label in REQUIRED_CANDIDATE_AXIS_LABELS
        if label not in present_with_tokens
    ]


def find_unknown_candidate_kind_errors(rows: list[list[str]]) -> list[str]:
    """候補セルのうち、その軸の種別語彙に無いトークンを指すエラーを返す。

    engine はモデル種別名の合法性を検証せず、未知の名前は bounds YAML 引きの
    ``KeyError`` になる（``docs/architecture/algorithm/input/3_design_principles.md``
    の「値レベルの契約は _assemble_input_dto へ寄せる」方針）。``KeyError`` は
    runner の exit 1 ＝ ``unexpected`` へ落ちるため、利用者のタイポが「想定外
    エラー」として表示される。ここで拾って 422 にするのがプリフライトの役目。

    未知の**軸ラベル**は対象外。engine が ``ValueError``（exit 2 ＝
    ``validation``）にするので、終了コードの粒度で既に足りている。

    Args:
        rows: ``read_rows`` が返す形の行リスト。

    Returns:
        エラーメッセージ。空なら全トークンが既知。
    """
    block = _find_candidate_block(rows)
    if block is None:
        return []
    header_idx, end_idx = block
    errors: list[str] = []
    for row in rows[header_idx + 1 : end_idx]:
        if _is_blank_row(row):
            continue
        label = _strip_cell(row[0])
        allowed = CANDIDATE_AXIS_KINDS.get(label)
        if allowed is None:
            continue
        for token in _candidate_tokens(row):
            if token not in allowed:
                errors.append(
                    f"{CANDIDATE_BLOCK_HEADER} の {label} に未知の種別 "
                    f"{token!r} があります。使えるのは "
                    f"{' / '.join(allowed)} です。"
                )
    return errors


def teacher_curve_has_near_zero_slip(rows: list[list[str]]) -> bool:
    """教師曲線に $s \\approx 0$ の点が含まれるか。

    ``nameplate.frequency`` と ``fixed_model_key.im_poles``、曲線の
    ``rotational_speed`` から同期速度 $n_s = 120 f / p$ を経由してスリップを
    出す。値が読めないときは ``False``（警告できないので黙る）。

    判定閾値 ``1e-3`` は apps 側のヒューリスティックであり、engine が
    公開している定数ではない。
    """
    frequency_hz = _section_float(rows, _NAMEPLATE_HEADER, _FREQUENCY_KEY)
    poles = _section_float(rows, _FIXED_HEADER, _POLES_KEY)
    if frequency_hz is None or poles is None or poles == 0.0:
        return False
    sync_rpm = 120.0 * frequency_hz / poles
    if sync_rpm == 0.0:
        return False
    for rpm in _curve_rotational_speeds(rows):
        slip = (sync_rpm - rpm) / sync_rpm
        if abs(slip) <= _NEAR_ZERO_SLIP_ABS:
            return True
    return False


def effective_kinds_include_non_none(rows: list[list[str]]) -> bool:
    """統合入力 CSV 上の候補（``model_candidate_axis``）に非 ``NONE`` があるか。"""
    block = _find_candidate_block(rows)
    if block is None:
        return False
    header_idx, end_idx = block
    allowed_non_none = set(IM_FRICTION_WINDAGE_KINDS + IM_STRAY_LOAD_KINDS) - {
        "NONE"
    }
    for row in rows[header_idx + 1 : end_idx]:
        if _is_blank_row(row):
            continue
        label = _strip_cell(row[0])
        if label not in REQUIRED_CANDIDATE_AXIS_LABELS:
            continue
        if any(token in allowed_non_none for token in _candidate_tokens(row)):
            return True
    return False


def _section_float(
    rows: list[list[str]], section: str, key: str
) -> float | None:
    in_section = False
    for row in rows:
        if _is_blank_row(row):
            if in_section:
                return None
            continue
        first = _strip_cell(row[0])
        if first == section:
            in_section = True
            continue
        if in_section and first == key and len(row) > 1:
            try:
                return float(_strip_cell(row[1]))
            except ValueError:
                return None
    return None


def _curve_rotational_speeds(rows: list[list[str]]) -> list[float]:
    header_idx: int | None = None
    for idx, row in enumerate(rows):
        if row and _strip_cell(row[0]).lower() == _CURVE_HEADER:
            header_idx = idx
            break
    if header_idx is None:
        return []
    speeds: list[float] = []
    # ヘッダの次は単位行。その次からデータ。
    for row in rows[header_idx + 2 :]:
        if _is_blank_row(row):
            break
        try:
            speeds.append(float(_strip_cell(row[0])))
        except ValueError:
            continue
    return speeds
