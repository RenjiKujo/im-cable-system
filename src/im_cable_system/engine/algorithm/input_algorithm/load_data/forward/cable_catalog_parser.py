"""cable_series_catalog.yaml のパース（Forward 系で共通）。

責務:
    - ケーブル区間ごとにシリーズ entry を解決し、``CableLoadedData`` に
      詰める。
    - 必須キー欠落・型不一致・シリーズ name の重複や欠落を ``ValueError``
      として検出する（``KeyError`` を漏らさない）。
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

from im_cable_system.engine.algorithm.input_algorithm.load_data.data_class.cable_loaded_data import (  # noqa: E501
    CableLoadedData,
    CableSectionLoadedData,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data.forward.series_selection_parser import (  # noqa: E501
    SeriesSelectionCableRow,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data.forward.yaml_utils import (  # noqa: E501
    float_with_unit_from_yaml,
    model_name_and_params_from_yaml,
    require_mapping_key,
    require_scalar_key,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data.util import (
    load_yaml_root_map,
)


def _cable_series_entries_from_root(root_map: Mapping[str, Any]) -> list[Any]:
    entries = root_map.get("cable_series")
    if not isinstance(entries, list):
        raise ValueError(
            "ケーブルシリーズカタログのルートに cable_series リストがありません"
        )
    return entries


def _validate_unique_named_entries(
    series_list: list[Any],
    catalog_path: Path,
) -> dict[str, Mapping[str, Any]]:
    """``cable_series`` リストを 1 周走査し、name 欠落と重複を検出する。"""
    by_name: dict[str, Mapping[str, Any]] = {}
    seen_at: dict[str, int] = {}
    for idx, raw_item in enumerate(series_list):
        if not isinstance(raw_item, Mapping):
            raise ValueError(
                f"ケーブルシリーズカタログの cable_series[{idx}] が"
                f"マッピングではありません: {catalog_path}"
            )
        item = cast(Mapping[str, Any], raw_item)
        if "name" not in item or str(item.get("name")).strip() == "":
            raise ValueError(
                f"ケーブルシリーズカタログの cable_series[{idx}] に "
                f"name キーがありません: {catalog_path}"
            )
        name = str(item["name"])
        if name in by_name:
            raise ValueError(
                f"ケーブルシリーズカタログにシリーズ名 {name!r} が"
                f"重複しています (cable_series[{seen_at[name]}] と "
                f"cable_series[{idx}]): {catalog_path}"
            )
        by_name[name] = item
        seen_at[name] = idx
    return by_name


def _section_from_catalog_entry(
    entry: Mapping[str, Any],
    row: SeriesSelectionCableRow,
) -> CableSectionLoadedData:
    ctx = f"ケーブルシリーズ {row.cable_series_name!r}"
    shape_type = str(require_scalar_key(entry, "shape_type", ctx))
    conductor = require_mapping_key(entry, "conductor", ctx)
    r_pl = require_mapping_key(
        conductor, "resistance_per_length", f"{ctx}.conductor"
    )
    l_pl = require_mapping_key(
        conductor, "inductance_per_length", f"{ctx}.conductor"
    )
    ground = require_mapping_key(entry, "ground", ctx)
    g_rl = require_mapping_key(ground, "resistance_length", f"{ctx}.ground")
    g_cpl = require_mapping_key(
        ground, "capacitance_per_length", f"{ctx}.ground"
    )
    r_val, r_unit = float_with_unit_from_yaml(
        r_pl, context=f"{ctx}.conductor.resistance_per_length"
    )
    l_val, l_unit = float_with_unit_from_yaml(
        l_pl, context=f"{ctx}.conductor.inductance_per_length"
    )
    gr_val, gr_unit = float_with_unit_from_yaml(
        g_rl, context=f"{ctx}.ground.resistance_length"
    )
    gc_val, gc_unit = float_with_unit_from_yaml(
        g_cpl, context=f"{ctx}.ground.capacitance_per_length"
    )
    return CableSectionLoadedData(
        name=row.cable_series_name,
        length=row.length,
        length_unit=row.length_unit,
        shape_type=shape_type,
        conductor_resistance_per_length=r_val,
        conductor_resistance_per_length_unit=r_unit,
        conductor_inductance_per_length=l_val,
        conductor_inductance_per_length_unit=l_unit,
        ground_resistance_length=gr_val,
        ground_resistance_length_unit=gr_unit,
        ground_capacitance_per_length=gc_val,
        ground_capacitance_per_length_unit=gc_unit,
    )


def _conductor_model_from_profile(
    root_map: Mapping[str, Any],
    profile_key: str,
    catalog_path: Path,
) -> tuple[str, dict[str, float] | None]:
    models = root_map.get("cable_conductor_models")
    if not isinstance(models, Mapping):
        raise ValueError(
            f"ケーブルシリーズカタログに cable_conductor_models がありません: "
            f"{catalog_path}"
        )
    entry = cast(Mapping[str, Any], models).get(profile_key)
    if not isinstance(entry, Mapping):
        raise ValueError(
            f"cable_conductor_models にキー '{profile_key}' がありません: "
            f"{catalog_path}"
        )
    block = cast(Mapping[str, Any], entry)
    ctx = f"cable_conductor_models[{profile_key!r}]"
    name, params = model_name_and_params_from_yaml(block, context=ctx)
    params_out: dict[str, float] | None = params if params else None
    return name, params_out


def parse_cable_from_catalog(
    catalog_path: Path,
    cable_rows: tuple[SeriesSelectionCableRow, ...],
    cable_bundle_label: str | None,
    conductor_model_profile: str | None,
) -> CableLoadedData | None:
    """ケーブルカタログとシリーズ選択行からケーブル中間表現を構築する。

    Args:
        catalog_path: ``cable_series_catalog.yaml`` のパス。
        cable_rows: シリーズ選択ファイルのケーブル区間行。
        cable_bundle_label: ケーブル束ラベル（未指定時は None）。
        conductor_model_profile: 導体モデルプロファイルキー。

    Returns:
        CableLoadedData | None: 区間が無いときは None。

    Raises:
        ValueError: スキーマ不正、プロファイル欠落、シリーズ entry の
            ``name`` 欠落 / 重複、必須キー欠落、または型不一致を検出
            した場合。
    """
    if len(cable_rows) == 0:
        return None

    root_map = load_yaml_root_map(catalog_path)
    series_list = _cable_series_entries_from_root(root_map)
    by_name = _validate_unique_named_entries(
        series_list=series_list,
        catalog_path=catalog_path,
    )
    sections: list[CableSectionLoadedData] = []
    for row in cable_rows:
        entry = by_name.get(row.cable_series_name)
        if entry is None:
            raise ValueError(
                f"ケーブルシリーズカタログに名前 "
                f"'{row.cable_series_name}' が見つかりません: "
                f"{catalog_path}"
            )
        sections.append(_section_from_catalog_entry(entry=entry, row=row))

    if conductor_model_profile is None or conductor_model_profile.strip() == "":
        raise ValueError(
            "ケーブル区間があるときは cable_conductor_model_profile が必要です。"
        )
    conductor_model, conductor_params = _conductor_model_from_profile(
        root_map=root_map,
        profile_key=conductor_model_profile,
        catalog_path=catalog_path,
    )
    bundle_name = cable_bundle_label if cable_bundle_label else "CABLE"
    return CableLoadedData(
        name=bundle_name,
        sections=tuple(sections),
        conductor_model=conductor_model,
        conductor_model_params=conductor_params,
    )
