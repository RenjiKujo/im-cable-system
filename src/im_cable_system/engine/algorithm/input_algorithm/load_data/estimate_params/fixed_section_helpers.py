"""統合 TSV ``fixed_model_key`` セクションからの取り出しヘルパー。

:class:`EstimateParamsParsedTables.fixed` の dict から、Loader が必要とする
スカラー値（``im_poles`` / ``im_circuit_type`` / ``im_connection_type`` /
``cable_length``）を ``KeyError`` を漏らさず ``ValueError`` 化して取り出す
薄い純関数群。

責務:
    - 必須キーの存在チェック（:func:`fixed_required_str` /
      :func:`fixed_required_int`）。
    - ``cable_length`` の解決（:func:`resolve_cable_length`：未指定時は
      ケーブル無し扱いとして長さ 0 を返す）。

値レベルの妥当性（正整数性・正値・有限性、単位文字列の表記揺れ吸収など）は
本層では行わず、DTO ``__post_init__`` と ``_validate_input_dto`` に寄せる
（:class:`...load_data.i_data_loader.IInputDataLoader` の契約に従う）。
"""

from __future__ import annotations

from im_cable_system.engine.algorithm.input_algorithm.load_data.estimate_params.unified_input_parser import (  # noqa: E501
    EstimateParamsParsedTables,
)

_CABLE_LENGTH_KEY = "cable_length"
_DEFAULT_CABLE_LENGTH_UNIT = "m"


def fixed_required_str(
    parsed: EstimateParamsParsedTables,
    key: str,
) -> str:
    """``fixed_model_key`` セクションから必須の文字列 value を取り出す。

    Args:
        parsed: 統合 TSV のパース結果。
        key: ``fixed`` dict 上のキー。

    Returns:
        セルの値文字列（パース時点で ``strip`` 済み）。

    Raises:
        ValueError: ``key`` がセクションに無い場合。
    """
    if key not in parsed.fixed:
        raise ValueError(
            f"統合 TSV の fixed_model_key に必須キー {key!r} がありません。"
        )
    return parsed.fixed[key].value


def fixed_required_int(
    parsed: EstimateParamsParsedTables,
    key: str,
) -> int:
    """``fixed_model_key`` セクションから必須の整数値を取り出す。

    Args:
        parsed: 統合 TSV のパース結果。
        key: ``fixed`` dict 上のキー。

    Returns:
        ``int()`` で変換した整数値。

    Raises:
        ValueError: ``key`` がセクションに無い、または ``int()`` で変換
            できない場合。
    """
    raw = fixed_required_str(parsed, key)
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(
            f"統合 TSV の fixed_model_key[{key!r}] は整数である必要が"
            f"あります（実際の値: {raw!r}）。"
        ) from exc


def resolve_cable_length(
    parsed: EstimateParamsParsedTables,
) -> tuple[float, str]:
    """``cable_length`` を ``(value, unit)`` で取り出す。

    キーが無い／値が空のときは長さ 0（ケーブル無し扱い）とする。単位が
    指定されていないときは ``"m"`` を補う。値域の妥当性（有限性、単位
    文字列の表記揺れ吸収）は本層では検査せず、DTO ``__post_init__`` と
    ``_validate_input_dto`` に寄せる。

    ただし **負値は構造的破綻** として扱い ``ValueError`` を投げる。
    ``build_cable_loaded_data`` 側は ``cable_length <= 0`` を「ケーブル
    無し」として早期 ``None`` 返却するため、負値を許すと DTO 化まで進む
    前に silent にケーブル無しに丸められてしまう。Loader 層で raise して
    silent failure を避ける。

    Args:
        parsed: 統合 TSV のパース結果。

    Returns:
        ``(length_value, length_unit)``。``length_value >= 0`` を保証する。

    Raises:
        ValueError: ``cable_length`` の値セルが ``float()`` で数値に
            変換できない、または変換結果が負値の場合。
    """
    cell = parsed.fixed.get(_CABLE_LENGTH_KEY)
    if cell is None or cell.value == "":
        return 0.0, _DEFAULT_CABLE_LENGTH_UNIT
    try:
        value = float(cell.value)
    except ValueError as exc:
        raise ValueError(
            f"統合 TSV の fixed_model_key[{_CABLE_LENGTH_KEY!r}] は数値で"
            f"ある必要があります（実際の値: {cell.value!r}）。"
        ) from exc
    if value < 0.0:
        raise ValueError(
            f"統合 TSV の fixed_model_key[{_CABLE_LENGTH_KEY!r}] は非負で"
            f"ある必要があります（実際の値: {value}）。"
        )
    unit = cell.unit if cell.unit is not None else _DEFAULT_CABLE_LENGTH_UNIT
    return value, unit
