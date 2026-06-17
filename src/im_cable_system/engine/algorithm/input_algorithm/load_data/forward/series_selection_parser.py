"""シリーズ選択 TSV のパース（Forward 系で共通）。

本モジュールは ``series_forward/*.tsv`` を読み、後段のカタログパーサ
（:mod:`cable_catalog_parser` / :mod:`im_catalog_parser`）と
:mod:`loader` が受け取れる **パース直後の中間型** を返す。

データクラスを ``data_class/`` 配下に置かない理由:
    :mod:`load_data.data_class` は ``load_data`` 層の **最終戻り値**
    （``CableLoadedData`` / ``ImLoadedData`` /
    ``ForwardInputLoadedData`` 等）を集める公開窓口である。
    これらは YAML カタログを引いて物性まで埋めた「完成した中間表現」で
    あり、参照キーや単位文字列だけを持つパース直後の構造とは段階が
    異なる。

    一方、本モジュール定義の :class:`SeriesSelectionMeta` /
    :class:`SeriesSelectionCableRow` / :class:`SeriesSelectionTable` /
    :class:`SeriesSelectionParsed` は、入力ファイル
    ``series_forward/*.tsv`` の **行構造そのもの** に引っ張られた一次型
    で、後段のカタログパーサに渡す **入口用の入れ物** である。最終
    LoadedData ではないため ``data_class/`` には置かず、生成元の parser
    と同じファイルに同居させる。

    ForwardByCartesianGrid / ForwardByOperatingPoints の両パイプラインで
    同形の中間型を扱うため、本モジュールに 1 セットだけ集約する。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from im_cable_system.engine.algorithm.input_algorithm.load_data.util import (  # noqa: E501
    read_csv_rows,
)


@dataclass(frozen=True)
class SeriesSelectionMeta:
    """シリーズ選択ファイルのメタ行。"""

    im_cable_system_name: str
    cable_bundle_label: str | None


@dataclass(frozen=True)
class SeriesSelectionCableRow:
    """ケーブル区間 1 行分（シリーズ選択ファイル由来）。"""

    cable_series_name: str
    length: float
    length_unit: str


@dataclass(frozen=True)
class SeriesSelectionTable:
    """シリーズ選択ファイルのテーブル部。"""

    im_series_name: str
    cable_rows: tuple[SeriesSelectionCableRow, ...]
    cable_conductor_model_profile: str | None


@dataclass(frozen=True)
class SeriesSelectionParsed:
    """シリーズ選択ファイル全体のパース結果。"""

    meta: SeriesSelectionMeta
    table: SeriesSelectionTable


_REQUIRED_TABLE_COLUMNS = (
    "im_series_name",
    "cable_series_name",
    "cable_length",
    "cable_conductor_model",
)


def _find_im_series_header_row_index(
    rows: list[list[str]],
    path: Path,
) -> int:
    """``im_series_name`` で始まるヘッダ行を 1 つだけ見つける。

    1 つも無いか、2 つ以上ある場合は ``ValueError``。
    """
    indices = [
        idx
        for idx, row in enumerate(rows)
        if row and row[0].strip() == "im_series_name"
    ]
    if not indices:
        raise ValueError(
            f"シリーズ CSV に im_series_name ヘッダ行がありません: {path}"
        )
    if len(indices) > 1:
        raise ValueError(
            f"シリーズ CSV に im_series_name ヘッダ行が複数あります "
            f"(行={indices}): {path}"
        )
    return indices[0]


def _cable_length_column_index(header: list[str], path: Path) -> int:
    if "cable_length" in header:
        return header.index("cable_length")
    raise ValueError(
        f"シリーズ CSV の im テーブルに cable_length 列がありません: {path}"
    )


def _resolve_cable_conductor_model_profile(
    path: Path,
    section_count: int,
    bundle_profile: str | None,
) -> str | None:
    if section_count > 0:
        if bundle_profile is None or bundle_profile == "":
            raise ValueError(
                f"ケーブル区間があるときは cable_conductor_model を "
                f"1 行だけ指定してください: {path}"
            )
        return bundle_profile
    if bundle_profile is not None and bundle_profile != "":
        raise ValueError(
            f"ケーブル無しのときは cable_conductor_model を空にしてください: "
            f"{path}"
        )
    return None


def _parse_series_meta(
    rows: list[list[str]],
    header_idx: int,
    path: Path,
) -> SeriesSelectionMeta:
    system_name: str | None = None
    cable_label: str | None = None
    for row in rows[:header_idx]:
        if not row or all(c.strip() == "" for c in row):
            continue
        key = row[0].strip()
        val = row[1].strip() if len(row) > 1 else ""
        if key == "im_cable_system_name":
            system_name = val
        elif key == "cable_name":
            cable_label = val if val != "" else None
    if system_name is None or system_name == "":
        raise ValueError(
            f"シリーズ CSV にメタキー im_cable_system_name がありません: {path}"
        )
    return SeriesSelectionMeta(
        im_cable_system_name=system_name,
        cable_bundle_label=cable_label,
    )


def _update_bundle_profile(
    profile_cell: str,
    bundle_profile: str | None,
    path: Path,
) -> str | None:
    """``cable_conductor_model`` セルを 1 つだけ拾って返す。

    2 行以上に書かれていた場合は ``ValueError`` を投げる。
    """
    if profile_cell == "":
        return bundle_profile
    if bundle_profile is not None:
        raise ValueError(
            f"cable_conductor_model はケーブル束につき 1 つだけ指定してください: "
            f"{path}"
        )
    return profile_cell


def _update_current_im(
    im_cell: str,
    current_im: str,
    path: Path,
) -> str:
    """``im_series_name`` セルを 1 つだけ拾って返す。

    既に確定済みのところに別行で書かれていた場合（同一値・別値を問わず）
    は ``ValueError`` を投げる。
    """
    if im_cell == "":
        return current_im
    if current_im != "":
        raise ValueError(
            f"im_series_name はテーブル全体で 1 つだけ指定してください: "
            f"既に {current_im!r} が指定された後に {im_cell!r} が "
            f"追加されています: {path}"
        )
    return im_cell


def _build_cable_row(
    cable_cell: str,
    len_cell: str,
    cable_length_unit: str,
    path: Path,
) -> SeriesSelectionCableRow | None:
    """ケーブル区間 1 行分を組み立てる（無効ペアは ``ValueError``）。"""
    if cable_cell == "" and len_cell == "":
        return None
    if cable_cell == "" or len_cell == "":
        raise ValueError(
            f"cable_series_name と cable_length は両方必須です: {path}"
        )
    return SeriesSelectionCableRow(
        cable_series_name=cable_cell,
        length=float(len_cell),
        length_unit=cable_length_unit,
    )


def _table_column_indices(
    header: list[str],
    path: Path,
) -> tuple[int, int, int, int]:
    """テーブルヘッダから必須 4 列の列番号を取り出す。

    必須列が重複して現れた場合は ``ValueError``（最初の出現で素通り
    させない）。欠落の場合も ``ValueError``。
    """
    for col in _REQUIRED_TABLE_COLUMNS:
        if header.count(col) > 1:
            raise ValueError(
                f"シリーズ CSV のテーブルヘッダに必須列 {col!r} が"
                f"複数あります: {path}"
            )
    try:
        idx_im = header.index("im_series_name")
        idx_cable = header.index("cable_series_name")
        idx_conductor_model = header.index("cable_conductor_model")
    except ValueError as exc:
        raise ValueError(
            f"シリーズ CSV の im テーブルに必須列がありません: {path}"
        ) from exc
    idx_len = _cable_length_column_index(header, path)
    return idx_im, idx_cable, idx_len, idx_conductor_model


def _parse_series_table(
    rows: list[list[str]],
    header_idx: int,
    path: Path,
) -> SeriesSelectionTable:
    if len(rows) < header_idx + 3:
        raise ValueError(
            f"シリーズ CSV には im テーブルに単位行・データ行が必要です: {path}"
        )
    header = [cell.strip() for cell in rows[header_idx]]
    idx_im, idx_cable, idx_len, idx_conductor_model = _table_column_indices(
        header=header,
        path=path,
    )
    unit_row = rows[header_idx + 1]
    cable_length_unit = (
        unit_row[idx_len].strip() if len(unit_row) > idx_len else ""
    )

    max_idx = max(idx_im, idx_cable, idx_len, idx_conductor_model)
    current_im = ""
    cable_rows: list[SeriesSelectionCableRow] = []
    bundle_profile: str | None = None

    for row in rows[header_idx + 2 :]:
        if not row or all(c.strip() == "" for c in row):
            continue
        while len(row) <= max_idx:
            row.append("")
        im_cell = row[idx_im].strip()
        cable_cell = row[idx_cable].strip()
        len_cell = row[idx_len].strip()
        profile_cell = row[idx_conductor_model].strip()

        bundle_profile = _update_bundle_profile(
            profile_cell=profile_cell,
            bundle_profile=bundle_profile,
            path=path,
        )
        current_im = _update_current_im(
            im_cell=im_cell,
            current_im=current_im,
            path=path,
        )
        new_cable_row = _build_cable_row(
            cable_cell=cable_cell,
            len_cell=len_cell,
            cable_length_unit=cable_length_unit,
            path=path,
        )
        if new_cable_row is not None:
            cable_rows.append(new_cable_row)

    if current_im == "":
        raise ValueError(f"im_series_name が1行も定義されていません: {path}")

    profile_key = _resolve_cable_conductor_model_profile(
        path=path,
        section_count=len(cable_rows),
        bundle_profile=bundle_profile,
    )
    return SeriesSelectionTable(
        im_series_name=current_im,
        cable_rows=tuple(cable_rows),
        cable_conductor_model_profile=profile_key,
    )


def parse_series_selection(path: Path) -> SeriesSelectionParsed:
    """シリーズ選択 TSV をパースする。

    Args:
        path: シリーズ選択ファイルパス。

    Returns:
        SeriesSelectionParsed: メタとテーブル部。

    Raises:
        ValueError: 形式が不正な場合。
    """
    rows = read_csv_rows(path)
    header_idx = _find_im_series_header_row_index(rows, path)
    meta = _parse_series_meta(rows, header_idx, path)
    table = _parse_series_table(rows, header_idx, path)
    return SeriesSelectionParsed(meta=meta, table=table)
