"""im_series_catalog.yaml のパース（Forward 系で共通）。

責務:
    - YAML ファイルからシリーズ entry を解決し、``ImLoadedData`` に詰める。
    - 必須キー欠落・型不一致・シリーズ name の重複や欠落を ``ValueError``
      として検出する（``KeyError`` を漏らさない）。
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

from im_cable_system.engine.algorithm.input_algorithm.load_data.data_class.im_loaded_data import (  # noqa: E501
    ImBranchLoadedData,
    ImLoadedData,
    ImNameplateLoadedData,
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


def _im_series_entries_from_root(root_map: Mapping[str, Any]) -> list[Any]:
    entries = root_map.get("im_series")
    if not isinstance(entries, list):
        raise ValueError(
            "IM シリーズカタログのルートに im_series リストがありません"
        )
    return entries


def _cage_multiplicity_from_entry(entry: Mapping[str, Any]) -> str:
    raw = entry.get("cage_multiplicity")
    if raw is None:
        return "SINGLE_CAGE"
    return str(raw).strip()


def _branch_from_yaml(
    sec_block: Mapping[str, Any],
    context: str,
) -> ImBranchLoadedData:
    model_name, model_params = model_name_and_params_from_yaml(
        require_mapping_key(sec_block, "model", context),
        context=f"{context}.model",
    )
    r_val, r_unit = float_with_unit_from_yaml(
        require_mapping_key(sec_block, "resistance", context),
        context=f"{context}.resistance",
    )
    l_val, l_unit = float_with_unit_from_yaml(
        require_mapping_key(sec_block, "inductance", context),
        context=f"{context}.inductance",
    )
    return ImBranchLoadedData(
        model=model_name,
        model_params=model_params,
        resistance=r_val,
        resistance_unit=r_unit,
        inductance=l_val,
        inductance_unit=l_unit,
    )


def _nameplate_from_entry(
    entry: Mapping[str, Any],
    series_name: str,
) -> ImNameplateLoadedData:
    nameplate = require_mapping_key(
        entry, "nameplate", f"IM シリーズ {series_name!r}"
    )
    ctx = f"IM シリーズ {series_name!r}.nameplate"
    v_val, v_unit = float_with_unit_from_yaml(
        require_mapping_key(nameplate, "voltage", ctx),
        context=f"{ctx}.voltage",
    )
    c_val, c_unit = float_with_unit_from_yaml(
        require_mapping_key(nameplate, "current", ctx),
        context=f"{ctx}.current",
    )
    p_val, p_unit = float_with_unit_from_yaml(
        require_mapping_key(nameplate, "power", ctx),
        context=f"{ctx}.power",
    )
    f_val, f_unit = float_with_unit_from_yaml(
        require_mapping_key(nameplate, "frequency", ctx),
        context=f"{ctx}.frequency",
    )
    return ImNameplateLoadedData(
        voltage=v_val,
        voltage_unit=v_unit,
        current=c_val,
        current_unit=c_unit,
        power=p_val,
        power_unit=p_unit,
        frequency=f_val,
        frequency_unit=f_unit,
    )


def _secondary_branches_from_entry(
    entry: Mapping[str, Any],
    series_name: str,
    cage_multiplicity: str,
) -> tuple[
    ImBranchLoadedData | None,
    ImBranchLoadedData | None,
    ImBranchLoadedData | None,
]:
    ctx = f"IM シリーズ {series_name!r}"
    if cage_multiplicity == "DOUBLE_CAGE":
        inner_block = entry.get("secondary_inner")
        outer_block = entry.get("secondary_outer")
        if not isinstance(inner_block, Mapping) or not isinstance(
            outer_block, Mapping
        ):
            raise ValueError(
                f"二重かごシリーズ '{series_name}' には secondary_inner と "
                "secondary_outer が必要です"
            )
        return (
            None,
            _branch_from_yaml(
                cast(Mapping[str, Any], inner_block),
                context=f"{ctx}.secondary_inner",
            ),
            _branch_from_yaml(
                cast(Mapping[str, Any], outer_block),
                context=f"{ctx}.secondary_outer",
            ),
        )
    sec_raw = entry.get("secondary")
    if not isinstance(sec_raw, Mapping):
        raise ValueError(
            f"単一かごシリーズ '{series_name}' には secondary が必要です"
        )
    return (
        _branch_from_yaml(
            cast(Mapping[str, Any], sec_raw),
            context=f"{ctx}.secondary",
        ),
        None,
        None,
    )


def _entry_to_im_loaded_data(
    entry: Mapping[str, Any],
    series_name: str,
) -> ImLoadedData:
    ctx = f"IM シリーズ {series_name!r}"
    cage_multiplicity = _cage_multiplicity_from_entry(entry)
    primary = _branch_from_yaml(
        require_mapping_key(entry, "primary", ctx),
        context=f"{ctx}.primary",
    )
    excitation = _branch_from_yaml(
        require_mapping_key(entry, "excitation", ctx),
        context=f"{ctx}.excitation",
    )
    secondary, secondary_inner, secondary_outer = (
        _secondary_branches_from_entry(
            entry=entry,
            series_name=series_name,
            cage_multiplicity=cage_multiplicity,
        )
    )
    poles_raw = require_scalar_key(entry, "poles", ctx)
    connection_type = str(require_scalar_key(entry, "connection_type", ctx))
    circuit_type = str(require_scalar_key(entry, "circuit_type", ctx))

    return ImLoadedData(
        name=series_name,
        poles=int(poles_raw),
        cage_multiplicity=cage_multiplicity,
        connection_type=connection_type,
        circuit_type=circuit_type,
        nameplate=_nameplate_from_entry(entry, series_name),
        primary=primary,
        excitation=excitation,
        secondary=secondary,
        secondary_inner=secondary_inner,
        secondary_outer=secondary_outer,
    )


def _validate_unique_named_entries(
    series_list: list[Any],
    catalog_path: Path,
) -> dict[str, Mapping[str, Any]]:
    """``im_series`` リストを 1 周走査し、name 欠落と重複を検出する。

    非マッピングの entry は ``ValueError`` で弾く（カタログとしての
    整合性を優先する。空 entry ``- `` 等は YAML 上で偶発的に混入する
    typo であることが多く、silent に飛ばすメリットは小さい）。
    """
    by_name: dict[str, Mapping[str, Any]] = {}
    seen_at: dict[str, int] = {}
    for idx, raw_item in enumerate(series_list):
        if not isinstance(raw_item, Mapping):
            raise ValueError(
                f"IM シリーズカタログの im_series[{idx}] がマッピングでは"
                f"ありません: {catalog_path}"
            )
        item = cast(Mapping[str, Any], raw_item)
        if "name" not in item or str(item.get("name")).strip() == "":
            raise ValueError(
                f"IM シリーズカタログの im_series[{idx}] に name キーが"
                f"ありません: {catalog_path}"
            )
        name = str(item["name"])
        if name in by_name:
            raise ValueError(
                f"IM シリーズカタログにシリーズ名 {name!r} が重複しています "
                f"(im_series[{seen_at[name]}] と im_series[{idx}]): "
                f"{catalog_path}"
            )
        by_name[name] = item
        seen_at[name] = idx
    return by_name


def parse_im_from_catalog(
    catalog_path: Path,
    series_name: str,
) -> ImLoadedData:
    """IM シリーズカタログから指定名の中間表現を読み込む。

    Args:
        catalog_path: ``im_series_catalog.yaml`` のパス。
        series_name: カタログ内の系列名。

    Returns:
        ImLoadedData: 誘導電動機の中間表現。

    Raises:
        ValueError: 該当系列が無い、シリーズ entry の ``name`` 欠落、
            ``name`` 重複、必須キー欠落、または型不一致を検出した場合。
    """
    root_map = load_yaml_root_map(catalog_path)
    series_list = _im_series_entries_from_root(root_map)
    by_name = _validate_unique_named_entries(
        series_list=series_list,
        catalog_path=catalog_path,
    )
    entry = by_name.get(series_name)
    if entry is None:
        raise ValueError(
            f"シリーズカタログに名前 '{series_name}' が見つかりません: "
            f"{catalog_path}"
        )
    return _entry_to_im_loaded_data(entry=entry, series_name=series_name)
