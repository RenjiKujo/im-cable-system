"""投入前の契約検証。

``routes_jobs`` と同じ責務ツリー内の内部実装。公開窓口へは再エクスポートしない。

ここは HTTP を知らない。内容の不整合は
``InputContractError``（``ValueError`` 派生）を投げるだけにし、422 への翻訳は
呼び出し側（``routes_jobs.submit_job`` の ``try/except``）に集約する。
JSON 不正（``overrides_json``）は本モジュールの対象外で、呼び出し側が 400 にする。
"""

from __future__ import annotations

from apps.web.engine_contract import (
    effective_kinds_include_non_none,
    find_bounds_contract_errors,
    find_catalog_contract_errors,
    find_missing_required_axes,
    find_unknown_candidate_kind_errors,
    read_rows,
    teacher_curve_has_near_zero_slip,
)

_NONE_HINT = (
    "ゼロ損失なら NONE を明示してください。"
    "雛形は examples/input/estimate_params_input.csv です。"
)


class InputContractError(ValueError):
    """投入内容が engine の入出力契約を満たさない。ルート側で 422 へ翻訳する。"""

    def __init__(self, *messages: str) -> None:
        """``NONE`` 明示と雛形への案内を必ず末尾へ付けて 1 本のメッセージにする。"""
        lines = [msg for msg in messages if msg]
        lines.append(_NONE_HINT)
        super().__init__("\n".join(lines))


def validate_estimate_params_csv(
    content: bytes, *, filename: str
) -> tuple[str, ...]:
    """候補軸（`model_candidate_axis`）を検証し、s≈0 警告を返す。

    候補は入力 CSV、境界・初期値は `im_bounds` YAML が正本で、どちらも
    プリセット選択で渡す（ここでは書き換えない）。

    Raises:
        InputContractError: 必須軸欠落、または候補セルに未知のモデル種別名。
    """
    rows = read_rows(content, filename=filename)

    missing = find_missing_required_axes(rows)
    if missing:
        raise InputContractError(
            *[
                f"model_candidate_axis に {label} 候補がありません。"
                for label in missing
            ]
        )

    # 未知の種別名は engine 側だと bounds YAML 引きの KeyError になり、
    # runner の exit 1 ＝ unexpected へ落ちる。利用者のタイポを
    # 「想定外エラー」にしないため、ここで 422 に翻訳する
    # （docs/apps/web/0_overview.md「エラーの伝え方」）。
    unknown_kind_errors = find_unknown_candidate_kind_errors(rows)
    if unknown_kind_errors:
        raise InputContractError(*unknown_kind_errors)

    warnings: list[str] = []
    if effective_kinds_include_non_none(
        rows
    ) and teacher_curve_has_near_zero_slip(rows):
        warnings.append(
            "非 NONE の軸出力控除を指定していますが、教師曲線に s≈0 の点が"
            "含まれています。s≈0 を含む教師曲線は避けてください"
            "（docs/model/curve_fitting_consistency.md の「軸出力控除」）。"
        )

    return tuple(warnings)


def validate_uploaded_im_catalog(yaml_text: str) -> None:
    """IM catalog の軸出力控除契約を検証する（アップロード・プリセット共通）。

    Raises:
        InputContractError: 契約違反。
    """
    errors = find_catalog_contract_errors(yaml_text)
    if errors:
        raise InputContractError(*errors)


def validate_uploaded_im_bounds(yaml_text: str) -> None:
    """IM bounds の軸出力控除契約を検証する（アップロード・プリセット共通）。

    Raises:
        InputContractError: 契約違反。
    """
    errors = find_bounds_contract_errors(yaml_text)
    if errors:
        raise InputContractError(*errors)
