"""engine の入出力ファイル契約の写し。

``apps/`` は engine を import しない（docs/apps/web/0_overview.md の
「やらないこと」）。検証・書き換え・結果表示に要る知識をここに閉じ込める。
写しである事実と drift 検出の所在は各モジュールの docstring 冒頭を正とする。

葉モジュール。HTTP も DB も engine も import しない（stdlib と ``yaml`` のみ）。
``api`` だけがこれを使う。``runner_gateway`` と ``store`` は使わない。
"""

from apps.web.engine_contract.estimate_params_input import (
    csv_delimiter_for_filename,
    effective_kinds_include_non_none,
    find_missing_required_axes,
    find_unknown_candidate_kind_errors,
    read_rows,
    teacher_curve_has_near_zero_slip,
)
from apps.web.engine_contract.fit_report import (
    FitMetricsView,
    FittedCatalogView,
    FittedParameterView,
    NameplateView,
    QuantityView,
    list_fitted_catalogs,
)
from apps.web.engine_contract.im_yaml_contract import (
    find_bounds_contract_errors,
    find_catalog_contract_errors,
)
from apps.web.engine_contract.model_kinds import (
    CANDIDATE_AXIS_KINDS,
    CANDIDATE_BLOCK_HEADER,
    IM_FRICTION_WINDAGE_KINDS,
    IM_STRAY_LOAD_KINDS,
    REQUIRED_CANDIDATE_AXIS_LABELS,
)

__all__ = [
    "CANDIDATE_AXIS_KINDS",
    "CANDIDATE_BLOCK_HEADER",
    "FitMetricsView",
    "FittedCatalogView",
    "FittedParameterView",
    "IM_FRICTION_WINDAGE_KINDS",
    "IM_STRAY_LOAD_KINDS",
    "NameplateView",
    "QuantityView",
    "REQUIRED_CANDIDATE_AXIS_LABELS",
    "csv_delimiter_for_filename",
    "effective_kinds_include_non_none",
    "find_bounds_contract_errors",
    "find_catalog_contract_errors",
    "find_missing_required_axes",
    "find_unknown_candidate_kind_errors",
    "list_fitted_catalogs",
    "read_rows",
    "teacher_curve_has_near_zero_slip",
]
