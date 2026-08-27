"""IM catalog / bounds YAML の軸出力控除 2 軸の契約検証。

これは engine の入出力ファイル契約の**写し**である。catalog は各 series に
``friction_windage.model.name`` / ``stray_load.model.name`` が必須、bounds は
トップレベルに ``friction_windage`` / ``stray_load`` の ``model_parameters`` が
必須、という engine 側パーサの事前条件を apps が投入時に再現する。

写しが engine から離れたことは、``test_im_yaml_contract.py`` が**同梱の実 catalog
/ bounds YAML をここへ通す**ことで検出する（engine と同じファイルを見ているので、
engine 側が形を変えれば同梱 YAML も変わり、ここが落ちる）。種別語彙そのものの
一致は ``test_engine_contract_drift.py`` が Enum と突き合わせる。

**この検証は engine の事前条件すべてを写したものではない。** ここを通っても
engine 側が別の理由で落ちることはあり（例: 候補種別に対応する係数が bounds に
無い場合の ``KeyError``）、その場合は exit 1 → ``error_kind = "unexpected"``
として扱われる。どこまで投入時に弾くかは docs/apps/web/0_overview.md の
「投入時プリフライト」を見る。

stdlib と ``yaml`` 以外に依存しない。HTTP / DB / engine は import しない。
"""

from __future__ import annotations

from typing import Any

import yaml

from apps.web.engine_contract.model_kinds import (
    IM_FRICTION_WINDAGE_KINDS,
    IM_STRAY_LOAD_KINDS,
)

_FRICTION_WINDAGE_KEY = "friction_windage"
_STRAY_LOAD_KEY = "stray_load"
_MODEL_PARAMETERS_KEY = "model_parameters"
_KNOWN_KINDS_BY_BRANCH: dict[str, tuple[str, ...]] = {
    _FRICTION_WINDAGE_KEY: IM_FRICTION_WINDAGE_KINDS,
    _STRAY_LOAD_KEY: IM_STRAY_LOAD_KINDS,
}


def _load_mapping(yaml_text: str, *, context: str) -> dict[str, Any] | str:
    """YAML を辞書として読む。失敗時はエラーメッセージ文字列を返す。"""
    try:
        raw = yaml.safe_load(yaml_text)
    except yaml.YAMLError as exc:
        return f"{context} を YAML として解釈できません: {exc}"
    if not isinstance(raw, dict):
        return f"{context} のトップレベルは辞書である必要があります。"
    return raw


def _series_name(entry: object, index: int) -> str:
    if isinstance(entry, dict):
        name = entry.get("name")
        if isinstance(name, str) and name.strip():
            return name
    return f"#{index}"


def _model_name_from_branch(
    entry: dict[str, Any], branch_key: str
) -> str | None:
    block = entry.get(branch_key)
    if not isinstance(block, dict):
        return None
    model = block.get("model")
    if not isinstance(model, dict):
        return None
    name = model.get("name")
    if name is None:
        return None
    return str(name)


def find_catalog_contract_errors(yaml_text: str) -> list[str]:
    """各 ``im_series`` エントリの軸出力控除 2 軸を検証する。

    Args:
        yaml_text: IM シリーズカタログ YAML 全文。

    Returns:
        エラーメッセージ（series 名付き）。空なら契約を満たす。
    """
    loaded = _load_mapping(yaml_text, context="IM catalog")
    if isinstance(loaded, str):
        return [loaded]
    series_list = loaded.get("im_series")
    if not isinstance(series_list, list):
        return ["IM catalog に im_series リストがありません。"]

    errors: list[str] = []
    for index, entry in enumerate(series_list):
        name = _series_name(entry, index)
        if not isinstance(entry, dict):
            errors.append(f"IM シリーズ {name!r} が辞書ではありません。")
            continue
        for branch_key, known_kinds in _KNOWN_KINDS_BY_BRANCH.items():
            model_name = _model_name_from_branch(entry, branch_key)
            if model_name is None:
                errors.append(
                    f"IM シリーズ {name!r} に {branch_key}.model.name が"
                    "ありません。"
                )
                continue
            if model_name not in known_kinds:
                errors.append(
                    f"IM シリーズ {name!r} の {branch_key}.model.name が"
                    f"未知です: {model_name!r}（許可: {list(known_kinds)}）。"
                )
    return errors


def find_bounds_contract_errors(yaml_text: str) -> list[str]:
    """トップレベルの ``friction_windage`` / ``stray_load`` が ``model_parameters`` を持つか。

    Args:
        yaml_text: IM パラメータ境界・初期値 YAML 全文。

    Returns:
        エラーメッセージ。空なら契約を満たす。
    """
    loaded = _load_mapping(yaml_text, context="IM bounds")
    if isinstance(loaded, str):
        return [loaded]
    errors: list[str] = []
    for branch_key in (_FRICTION_WINDAGE_KEY, _STRAY_LOAD_KEY):
        block = loaded.get(branch_key)
        if not isinstance(block, dict):
            errors.append(f"IM bounds に {branch_key} ブロックがありません。")
            continue
        params = block.get(_MODEL_PARAMETERS_KEY)
        if not isinstance(params, dict):
            errors.append(
                f"IM bounds の {branch_key} に {_MODEL_PARAMETERS_KEY} が"
                "ありません。"
            )
    return errors
