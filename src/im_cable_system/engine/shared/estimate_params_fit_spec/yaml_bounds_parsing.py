"""estimation YAML から bounds / init 辞書を取り出す内部ヘルパ。

``parse_*_block_with_init`` は :class:`ParameterFitSpec` を返す厳格スキーマ。
各パラメータ行は ``bounds``（``lb`` / ``ub`` を両方必須）と ``init.method``
を必須とする。``bounds`` が片方でも欠ける行は設定誤りとして拒否する
（スキップしない）。``init.method='value'`` のときは ``init.value`` も必須で、
``[lb, ub]`` 範囲内であること。

非公開（層外・層横断向けではない）:
    本モジュールは ``estimate_params_fit_spec`` パッケージの **内部実装**
    であり、公開窓口 ``__init__.py`` の ``__all__`` には載せない。層外
    （algorithm / processor 等）からは ``ImParameterFitDescriptorBounds`` /
    ``CableParameterFitDescriptorBounds`` の ``from_estimation_document``
    を経由すること。本モジュールの関数を直接 import してよいのは、
    同一パッケージ内の実装と、スキーマ解釈の分岐網羅を目的とする内部
    テストに限る。
"""

from __future__ import annotations

from typing import Any

from im_cable_system.engine.shared.estimate_params_fit_spec.parameter_fit_spec import (  # noqa: E501
    InitMethod,
    ParameterFitSpec,
)

_FIXED_PARAM_BLOCK_KEYS = ("fit_parameters", "rl_parameters", "rc_parameters")


def document_body_without_version(document: dict[str, Any]) -> dict[str, Any]:
    """トップレベルから ``version`` 以外のキーを返す（ルートをサブシステムノードとみなす）。"""
    return {k: v for k, v in document.items() if k != "version"}


def _extract_lb_ub(
    entry: dict[str, Any],
    param_key: str,
) -> tuple[float, float]:
    """``entry`` から ``(lb, ub)`` を取り出す（strict スキーマ）。

    ``bounds`` は ``lb`` / ``ub`` を必ず両方持つこと。片方のみ・両方欠落・
    mapping でない場合はいずれも設定誤りとして拒否する。

    Args:
        entry: パラメータ単位の dict（``bounds`` と ``init`` を含む）。
        param_key: エラーメッセージに含めるパラメータ名。

    Returns:
        tuple[float, float]: ``(lb, ub)``。

    Raises:
        ValueError: ``bounds`` キー欠落、``bounds`` が mapping でない、
            ``lb`` か ``ub`` のいずれかが欠けている場合。
    """
    bounds = entry.get("bounds")
    if not isinstance(bounds, dict):
        raise ValueError(
            f"parameter {param_key!r} requires 'bounds' mapping with "
            f"'lb' and 'ub' fields"
        )
    missing = [key for key in ("lb", "ub") if key not in bounds]
    if missing:
        missing_keys = ", ".join(missing)
        raise ValueError(
            f"parameter {param_key!r} 'bounds' is missing required "
            f"field(s): {missing_keys}"
        )
    return (float(bounds["lb"]), float(bounds["ub"]))


def _parse_init_block(
    entry: dict[str, Any],
    param_key: str,
) -> tuple[InitMethod, float | None]:
    """``entry`` の ``init`` ブロックを解釈する。

    Args:
        entry: パラメータ単位の dict（``bounds`` と ``init`` を含む）。
        param_key: エラーメッセージに含めるパラメータ名。

    Returns:
        tuple[InitMethod, float | None]: ``(method, value)``。
            ``method`` が VALUE 以外のとき ``value`` は ``None``。

    Raises:
        ValueError: ``init`` キー欠落、``method`` キー欠落、未知 method、
            ``method='value'`` のときの ``value`` 欠落のいずれか。
    """
    init = entry.get("init")
    if not isinstance(init, dict):
        raise ValueError(
            f"parameter {param_key!r} requires 'init' mapping with "
            f"'method' field"
        )
    method_str = init.get("method")
    if not isinstance(method_str, str):
        raise ValueError(
            f"parameter {param_key!r} 'init.method' is required and must "
            f"be a string"
        )
    try:
        method = InitMethod(method_str)
    except ValueError as exc:
        valid = ", ".join(m.value for m in InitMethod)
        raise ValueError(
            f"parameter {param_key!r} 'init.method' must be one of "
            f"{{{valid}}} (got {method_str!r})"
        ) from exc
    if method != InitMethod.VALUE:
        return (method, None)
    if "value" not in init:
        raise ValueError(
            f"parameter {param_key!r} 'init.method=value' requires "
            f"'init.value' field"
        )
    return (method, float(init["value"]))


def _build_spec(
    entry: dict[str, Any],
    param_key: str,
) -> ParameterFitSpec:
    """``entry`` から :class:`ParameterFitSpec` を組み立てる（strict スキーマ）。

    ``bounds`` は ``lb`` / ``ub`` を両方必須、``init`` も必須とする。いずれ
    か欠ける行は設定誤りとして :class:`ValueError` を送出する。

    Raises:
        ValueError: ``bounds`` または ``init`` が不正・不足の場合。
    """
    lb, ub = _extract_lb_ub(entry, param_key)
    method, init_value = _parse_init_block(entry, param_key)
    return ParameterFitSpec(
        lb=lb,
        ub=ub,
        init_method=method,
        init_value=init_value,
    )


def parse_fixed_parameters_block_with_init(
    section: object,
) -> dict[str, ParameterFitSpec]:
    """サブシステムノード直下の固定パラメータブロックから spec を抽出する。

    各パラメータ行は ``bounds``（``lb`` / ``ub`` を両方必須）と
    ``init.method`` を必須とする strict スキャン。

    Raises:
        ValueError: ``bounds`` が無い・片方欠落、``init`` が無い、
            ``init.method`` が未対応の値、``method='value'`` で ``value``
            が無いなどの場合。
    """
    if not isinstance(section, dict):
        return {}
    out: dict[str, ParameterFitSpec] = {}
    for block_key in _FIXED_PARAM_BLOCK_KEYS:
        block = section.get(block_key)
        if not isinstance(block, dict):
            continue
        for key, entry in block.items():
            if not isinstance(entry, dict):
                continue
            out[str(key)] = _build_spec(entry, str(key))
    return out


def _require_params_mapping(
    model_name: object,
    model_entry: object,
) -> dict[str, Any]:
    """モデル種別エントリから ``params`` マッピングを取り出す。

    係数を取らない種別（``BASIC`` / ``NONE`` 等）も ``params: {}`` を必ず
    書く規約のため、省略・null・非マッピングはすべて設定誤りとして扱う。

    Raises:
        ValueError: ``params`` マッピングを持たない場合。
    """
    if isinstance(model_entry, dict) and isinstance(
        model_entry.get("params"), dict
    ):
        return model_entry["params"]
    raise ValueError(
        f"model type {model_name!r} requires 'params' mapping; write "
        "'params: {}' for a model type that takes no parameters"
    )


def parse_model_parameters_block_with_init(
    section: object,
) -> dict[str, dict[str, ParameterFitSpec]]:
    """``model_parameters`` 配下の各モデルタイプの params を spec で抽出する。

    各パラメータ行は ``bounds``（``lb`` / ``ub`` を両方必須）と
    ``init.method`` を必須とする strict スキャン。

    モデル種別は ``params`` マッピングを必ず持つ（係数を取らない種別は
    ``params: {}``）。``params`` の省略・null・非マッピングを黙って読み飛
    ばすとモデル種別キーごと欠落し、下流で「YAML にキーはあるのに未知の
    モデル種別」という原因を誤導する :class:`KeyError` になるため、ここで
    :class:`ValueError` にして真因を示す。

    Raises:
        ValueError: ``bounds`` が無い・片方欠落、``init`` が無い、
            ``init.method`` が未対応の値、``method='value'`` で ``value``
            が無い、モデル種別が ``params`` マッピングを持たないなどの場合。
    """
    if not isinstance(section, dict):
        return {}
    mp = section.get("model_parameters", {})
    if not isinstance(mp, dict):
        return {}
    out: dict[str, dict[str, ParameterFitSpec]] = {}
    for model_name, model_entry in mp.items():
        params = _require_params_mapping(model_name, model_entry)
        inner: dict[str, ParameterFitSpec] = {}
        for pname, pentry in params.items():
            if not isinstance(pentry, dict):
                raise ValueError(
                    f"parameter {f'{model_name}.{pname}'!r} requires "
                    f"'bounds' mapping with 'lb' and 'ub', got "
                    f"{type(pentry).__name__}"
                )
            inner[str(pname)] = _build_spec(pentry, f"{model_name}.{pname}")
        out[str(model_name)] = inner
    return out
