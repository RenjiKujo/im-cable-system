"""アセンブラ共通: LoadedData 由来の単位文字列を正規化する。

LoadData 層は単位文字列に対して ``strip()`` のみ行い、TSV / YAML 上の
表記をほぼそのまま保持する責務（``axes_parser`` / ``series_selection_parser``
/ ``performance_curve_parser`` の各 docstring 参照）。よって LoadedData の
単位セルには ``[m]`` / ``[rpm]`` のように外側角括弧が残ったままになり得る。

アセンブラ層が DTO へ詰める前にこの「外側角括弧の剥がし」を一括で担う。
``assemble_input_dto.common`` 配下の各 ``*_dto_builder`` から、また
``assemble_input_dto.estimate_params.perf_curve_unit_converter`` からも
共通利用される。

Note:
    値域チェック・許容単位チェックは DTO の ``__post_init__`` 側
    （``Float*Dto`` / ``Array*Dto``）の責務であり、本モジュールでは
    行わない。本モジュールは「`[xxx]` → `xxx` の純粋な表記正規化」のみ。
"""

from __future__ import annotations


def normalize_loaded_unit_cell(raw: str) -> str:
    """LoadedData 由来の単位文字列の外側角括弧を剥がして返す。

    例:
        ``"[m]"`` → ``"m"``
        ``"  [rpm] "`` → ``"rpm"``
        ``"Nm"`` → ``"Nm"``（変化なし）
        ``""`` → ``""``

    Args:
        raw: ロード時に ``strip()`` のみ施された単位文字列。

    Returns:
        外側 ``[...]`` を剥がして再度 ``strip()`` した文字列。
    """
    stripped = raw.strip()
    if len(stripped) >= 2 and stripped[0] == "[" and stripped[-1] == "]":
        return stripped[1:-1].strip()
    return stripped
