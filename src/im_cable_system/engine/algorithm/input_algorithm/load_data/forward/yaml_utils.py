"""YAML カタログ読み込みの共通ユーティリティ（Forward 系で共通）。

本モジュールの方針:

- YAML パース後の Mapping から必須キーを取り出す処理は、すべて
  ``KeyError`` ではなく ``ValueError`` を投げる。Loader 層の
  ``Raises:`` 契約（``ValueError`` のみ）と整合させる。
- エラーメッセージには ``context`` 文字列を前置し、どの YAML / どの
  シリーズの、どこで欠落したかを呼び出し側が辿れるようにする。

YAML のルート読込（``load_yaml_root_map``）は load_data 横断の
:mod:`load_data.util.yaml_utils` に集約済み。本モジュールには **Forward
カタログのスキーマ解釈**（必須キー取り出し、``{value, unit}``、
``{name, params}`` の解釈）のみを残す。
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, cast


def _prefix(context: str) -> str:
    return f"{context}: " if context else ""


def require_mapping_key(
    parent: Mapping[str, Any],
    key: str,
    context: str = "",
) -> Mapping[str, Any]:
    """``parent[key]`` がマッピングであることを保証して返す。

    キーが存在しないか、マッピングでない場合は ``ValueError``。
    """
    if key not in parent:
        raise ValueError(f"{_prefix(context)}必須キー {key!r} がありません")
    value = parent[key]
    if not isinstance(value, Mapping):
        raise ValueError(
            f"{_prefix(context)}キー {key!r} はマッピングである必要があります"
        )
    return cast(Mapping[str, Any], value)


def require_scalar_key(
    parent: Mapping[str, Any],
    key: str,
    context: str = "",
) -> Any:  # noqa: ANN401
    """``parent[key]`` を返す。キーが無ければ ``ValueError``。"""
    if key not in parent:
        raise ValueError(f"{_prefix(context)}必須キー {key!r} がありません")
    return parent[key]


def float_with_unit_from_yaml(
    block: Mapping[str, Any],
    context: str = "",
) -> tuple[float, str]:
    """``{value, unit}`` ブロックから値と単位を取り出す。

    ``value`` / ``unit`` のどちらかが欠けていれば ``ValueError``。
    """
    prefix = _prefix(context)
    if "value" not in block:
        raise ValueError(
            f"{prefix}{{value, unit}} ブロックに 'value' がありません"
        )
    if "unit" not in block:
        raise ValueError(
            f"{prefix}{{value, unit}} ブロックに 'unit' がありません"
        )
    return float(block["value"]), str(block["unit"])


def model_params_dict_from_yaml(
    params_raw: object,
    context: str = "",
) -> dict[str, float]:
    """YAML の ``params`` リストを ``{name: value}`` 辞書に正規化する。

    Args:
        params_raw: ``None``、空リスト、または ``{name, value}`` のリスト。
        context: エラーメッセージ用の前置文字列。

    Returns:
        パラメータ辞書。無いときは空辞書。
    """
    prefix = _prefix(context)
    if params_raw is None:
        return {}
    if isinstance(params_raw, list) and len(params_raw) == 0:
        return {}
    if not isinstance(params_raw, list):
        raise ValueError(f"{prefix}params はリストである必要があります")
    result: dict[str, float] = {}
    for i, item in enumerate(params_raw):
        if not isinstance(item, Mapping):
            raise ValueError(
                f"{prefix}params[{i}] はマッピングである必要があります"
            )
        mapping = cast(Mapping[str, Any], item)
        if "name" not in mapping or "value" not in mapping:
            raise ValueError(
                f"{prefix}params[{i}] には 'name' と 'value' が必要です"
            )
        result[str(mapping["name"])] = float(mapping["value"])
    return result


def model_name_and_params_from_yaml(
    block: Mapping[str, Any],
    context: str = "",
) -> tuple[str, dict[str, float]]:
    """``model: { name, params }`` ブロックを解釈する。

    ``name`` が無ければ ``ValueError``。``params`` は optional。
    """
    if "name" not in block:
        raise ValueError(
            f"{_prefix(context)}model ブロックに 'name' がありません"
        )
    name = str(block["name"])
    params = model_params_dict_from_yaml(
        block.get("params"),
        context=context,
    )
    return name, params
