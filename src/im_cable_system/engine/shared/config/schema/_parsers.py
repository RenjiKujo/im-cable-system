"""schema 内部用の型変換・検証ヘルパー。

各セクション factory から共通利用する。YAML キー欠損は ``default`` への
フォールバック、値ありで型変換失敗・範囲外・Enum 外などは ``ValueError``
を送出する（fail-fast）。

エラーメッセージは常に ``key_path``（YAML のフルパス）と受け取った値を
含め、設定ミスの発生箇所を特定できるようにする。
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from enum import Enum
from typing import Any, Literal, TypeVar, overload

_MISSING: Any = object()

EnumT = TypeVar("EnumT", bound=Enum)


def parse_dict(
    raw: Any,
    *,
    key_path: str,
) -> dict[str, Any]:
    """YAML ノードが dict であることを保証して返す。

    ``raw`` が ``None`` のときは空 dict を返す（キー欠損扱い）。dict 以外
    の型が来た場合は YAML 構造が壊れているため ``ValueError`` を送出する。

    Args:
        raw: YAML 由来の値。
        key_path: 値が属する YAML キーのフルパス（エラー用）。

    Returns:
        dict[str, Any]: 入力をそのまま返した dict。

    Raises:
        ValueError: ``raw`` が ``None`` でも dict でもない場合。
    """
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise ValueError(
            f"{key_path} は dict である必要がありますが、"
            f"{type(raw).__name__} を受け取りました（値: {raw!r}）。"
        )
    return raw


def parse_required_str(
    raw: Any,
    *,
    key_path: str,
    default: str | None = None,
    choices: Iterable[str] | None = None,
) -> str:
    """文字列を取り出し、必要なら ``choices`` で値域を検証する。

    Args:
        raw: YAML 由来の値。``None`` または欠損のとき ``default`` を使う。
        key_path: 値が属する YAML キーのフルパス（エラー用）。
        default: キー欠損時の既定値。``None`` のままで欠損なら ``ValueError``。
        choices: 許容する値の集合。``None`` なら任意の str を許容。

    Returns:
        str: 検証済みの値。

    Raises:
        ValueError: 必須なのに欠損、または ``choices`` 外の値が来た場合。
    """
    if raw is None:
        if default is None:
            raise ValueError(f"{key_path} は必須です。")
        return default
    value = str(raw)
    if choices is not None and value not in choices:
        choice_str = ", ".join(repr(c) for c in choices)
        raise ValueError(
            f"{key_path} は {{{choice_str}}} のいずれかである必要がありますが、"
            f"{value!r} を受け取りました。"
        )
    return value


@overload
def parse_int(
    raw: Any,
    *,
    key_path: str,
    default: int = ...,
    positive: bool = False,
    allow_none: Literal[False] = False,
) -> int: ...


@overload
def parse_int(
    raw: Any,
    *,
    key_path: str,
    default: int | None = None,
    positive: bool = False,
    allow_none: Literal[True],
) -> int | None: ...


def parse_int(
    raw: Any,
    *,
    key_path: str,
    default: int | None | Any = _MISSING,
    positive: bool = False,
    allow_none: bool = False,
) -> int | None:
    """整数値を取り出して検証する。

    Args:
        raw: YAML 由来の値。``None`` または欠損のとき ``default`` を使う。
        key_path: 値が属する YAML キーのフルパス（エラー用）。
        default: キー欠損時の既定値。未指定で欠損なら ``ValueError``。
            ``allow_none=True`` のときは既定 ``None`` で None を返す。
        positive: True のとき値は正である必要がある。
        allow_none: True のとき ``None`` を返し得る（並列ワーカー数等）。

    Returns:
        int | None: 検証済みの整数値。``allow_none=False`` なら必ず int。

    Raises:
        ValueError: 整数に変換できない、または ``positive`` 違反、または
            必須なのに欠損だった場合。
    """
    if raw is None:
        if allow_none:
            return None
        if default is _MISSING:
            raise ValueError(f"{key_path} は必須です。")
        if default is None:
            raise ValueError(f"{key_path} は整数の既定値が必要です。")
        return int(default)
    if isinstance(raw, bool):
        raise ValueError(
            f"{key_path} は整数である必要がありますが、bool を受け取りました"
            f"（値: {raw!r}）。"
        )
    try:
        value = int(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"{key_path} は整数に変換可能な値である必要がありますが、"
            f"{type(raw).__name__}={raw!r} を受け取りました。"
        ) from exc
    if positive and value <= 0:
        raise ValueError(
            f"{key_path} は正の整数である必要がありますが、{value} を"
            "受け取りました。"
        )
    return value


@overload
def parse_float(
    raw: Any,
    *,
    key_path: str,
    default: float = ...,
    positive: bool = False,
    non_negative: bool = False,
    finite: bool = True,
    allow_none: Literal[False] = False,
) -> float: ...


@overload
def parse_float(
    raw: Any,
    *,
    key_path: str,
    default: float | None = None,
    positive: bool = False,
    non_negative: bool = False,
    finite: bool = True,
    allow_none: Literal[True],
) -> float | None: ...


def parse_float(
    raw: Any,
    *,
    key_path: str,
    default: float | None | Any = _MISSING,
    positive: bool = False,
    non_negative: bool = False,
    finite: bool = True,
    allow_none: bool = False,
) -> float | None:
    """浮動小数点値を取り出して検証する。

    Args:
        raw: YAML 由来の値。``None`` または欠損のとき ``default`` を使う。
        key_path: 値が属する YAML キーのフルパス（エラー用）。
        default: キー欠損時の既定値。未指定で欠損なら ``ValueError``。
        positive: True のとき値は正である必要がある。
        non_negative: True のとき値は非負である必要がある。
        finite: True のとき ``NaN`` / ``inf`` を許可しない。
        allow_none: True のとき ``None`` を返し得る。

    Returns:
        float | None: 検証済みの浮動小数点値。

    Raises:
        ValueError: float に変換できない、``positive`` / ``non_negative``
            / ``finite`` 違反、または必須なのに欠損だった場合。
    """
    if raw is None:
        if allow_none:
            return None
        if default is _MISSING:
            raise ValueError(f"{key_path} は必須です。")
        if default is None:
            raise ValueError(f"{key_path} は数値の既定値が必要です。")
        return float(default)
    if isinstance(raw, bool):
        raise ValueError(
            f"{key_path} は数値である必要がありますが、bool を受け取りました"
            f"（値: {raw!r}）。"
        )
    try:
        value = float(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"{key_path} は数値に変換可能な値である必要がありますが、"
            f"{type(raw).__name__}={raw!r} を受け取りました。"
        ) from exc
    if finite and not math.isfinite(value):
        raise ValueError(
            f"{key_path} は有限値である必要がありますが、{value!r} を"
            "受け取りました。"
        )
    if positive and value <= 0.0:
        raise ValueError(
            f"{key_path} は正の数値である必要がありますが、{value} を"
            "受け取りました。"
        )
    if non_negative and value < 0.0:
        raise ValueError(
            f"{key_path} は非負の数値である必要がありますが、{value} を"
            "受け取りました。"
        )
    return value


def parse_bool(
    raw: Any,
    *,
    key_path: str,
    default: bool | None = None,
) -> bool:
    """真偽値を取り出して検証する。

    YAML loader が bool 化していない値（"true" 文字列など）は許容しない。
    人為的なミスを早期検知するため、必ず bool で記述されていることを
    要求する。
    """
    if raw is None:
        if default is None:
            raise ValueError(f"{key_path} は必須です。")
        return default
    if not isinstance(raw, bool):
        raise ValueError(
            f"{key_path} は bool である必要がありますが、"
            f"{type(raw).__name__}={raw!r} を受け取りました。"
        )
    return raw


def parse_enum(
    raw: Any,
    enum_cls: type[EnumT],
    *,
    key_path: str,
    default: EnumT | None = None,
) -> EnumT:
    """Enum 値を取り出して検証する。

    Args:
        raw: YAML 由来の値（文字列前提）。前後空白は除去する。
        enum_cls: 期待する Enum クラス。
        key_path: YAML キーのフルパス（エラー用）。
        default: キー欠損時の既定値。``None`` のままで欠損なら ``ValueError``。

    Returns:
        EnumT: 検証済みの Enum メンバ。

    Raises:
        ValueError: Enum メンバに該当しない値の場合。
    """
    if raw is None:
        if default is None:
            raise ValueError(f"{key_path} は必須です。")
        return default
    value = str(raw).strip()
    try:
        return enum_cls(value)
    except ValueError as exc:
        valid_values = ", ".join(repr(member.value) for member in enum_cls)
        raise ValueError(
            f"{key_path} は {{{valid_values}}} のいずれかである必要が"
            f"ありますが、{raw!r} を受け取りました。"
        ) from exc
