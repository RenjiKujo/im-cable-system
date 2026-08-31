"""``report_model_*.yaml`` の読み取り。

これは engine の入出力ファイル契約の**写し**である。推定結果 YAML の形
（``model_labels`` 7 キー / ``fitted_parameters`` / ``fit_metrics`` /
``nameplate``）は engine 側 ``fitted_catalog_builder.build_fitted_catalog`` が
正本。写しが離れたら
``tests/test_apps/test_web/engine_contract/test_engine_contract_drift.py`` が落ちる
（同テストは固定サンプルではなく builder を実際に呼んでキー集合を突き合わせる）。

stdlib と ``yaml`` 以外に依存しない。HTTP / DB / engine は import しない。
表示目的で成果物 YAML を読むだけであり、DB にもマニフェストにも持たない。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

_REPORT_GLOB = "report_model_*.yaml"
_MODEL_LABEL_KEYS: tuple[str, ...] = (
    "im_primary",
    "im_excitation",
    "im_secondary_inner",
    "im_secondary_outer",
    "im_friction_windage",
    "im_stray_load",
    "cable_conductor",
)
_FIT_METRICS_KEYS: tuple[str, ...] = (
    "optimizer_success",
    "least_squares_cost",
    "overall_rmse_weighted_residual",
    "n_residual_elements",
    "n_valid_curve_points",
)


@dataclass(frozen=True)
class QuantityView:
    """名板量 1 件。"""

    value: float
    unit: str


@dataclass(frozen=True)
class NameplateView:
    """推定結果 YAML の名板（出力・電流）。"""

    power: QuantityView
    current: QuantityView


@dataclass(frozen=True)
class FittedParameterView:
    """推定パラメータ 1 件。"""

    path: str
    value: float
    unit: str | None
    initial_value: float | None
    lower_bound: float | None
    upper_bound: float | None
    bound_status: str


@dataclass(frozen=True)
class FitMetricsView:
    """適合指標。"""

    optimizer_success: bool
    least_squares_cost: float
    overall_rmse_weighted_residual: float
    n_residual_elements: int
    n_valid_curve_points: int


@dataclass(frozen=True)
class FittedCatalogView:
    """``report_model_*.yaml`` から表示に使う範囲だけを写した DTO。"""

    name: str
    nameplate: NameplateView
    model_labels: dict[str, str]
    fitted_parameters: tuple[FittedParameterView, ...]
    fit_metrics: FitMetricsView
    source_filename: str


def list_fitted_catalogs(reports_dir: Path) -> tuple[FittedCatalogView, ...]:
    """``report_model_*.yaml`` を全件読み、``(name, source_filename)`` 昇順で返す。

    Args:
        reports_dir: ジョブの ``<output_dir>/reports/``。

    Returns:
        読めた ``FittedCatalogView`` のタプル。ディレクトリが無い / 空なら ``()``。

    Raises:
        ValueError: YAML が契約を満たさない場合。
    """
    if not reports_dir.is_dir():
        return ()
    views = [
        _parse_fitted_catalog(path) for path in reports_dir.glob(_REPORT_GLOB)
    ]
    return tuple(
        sorted(views, key=lambda view: (view.name, view.source_filename))
    )


def _parse_fitted_catalog(path: Path) -> FittedCatalogView:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ValueError(
            f"{path.name} を YAML として解釈できません: {exc}"
        ) from exc
    if not isinstance(raw, dict):
        raise ValueError(
            f"{path.name} のトップレベルは辞書である必要があります。"
        )

    name = raw.get("name")
    if not isinstance(name, str) or not name:
        raise ValueError(f"{path.name} に name がありません。")

    return FittedCatalogView(
        name=name,
        nameplate=_parse_nameplate(raw.get("nameplate"), path.name),
        model_labels=_parse_model_labels(raw.get("model_labels"), path.name),
        fitted_parameters=_parse_fitted_parameters(
            raw.get("fitted_parameters"), path.name
        ),
        fit_metrics=_parse_fit_metrics(raw.get("fit_metrics"), path.name),
        source_filename=path.name,
    )


def _parse_nameplate(raw: object, filename: str) -> NameplateView:
    if not isinstance(raw, dict):
        raise ValueError(f"{filename} に nameplate がありません。")
    return NameplateView(
        power=_parse_quantity(raw.get("power"), filename, "nameplate.power"),
        current=_parse_quantity(
            raw.get("current"), filename, "nameplate.current"
        ),
    )


def _parse_quantity(raw: object, filename: str, context: str) -> QuantityView:
    if not isinstance(raw, dict):
        raise ValueError(f"{filename} に {context} がありません。")
    value = raw.get("value")
    unit = raw.get("unit")
    if not isinstance(value, (int, float)):
        raise ValueError(
            f"{filename} の {context}.value が数値ではありません。"
        )
    if not isinstance(unit, str):
        raise ValueError(
            f"{filename} の {context}.unit が文字列ではありません。"
        )
    return QuantityView(value=float(value), unit=unit)


def _parse_model_labels(raw: object, filename: str) -> dict[str, str]:
    if not isinstance(raw, dict):
        raise ValueError(f"{filename} に model_labels がありません。")
    labels: dict[str, str] = {}
    for key in _MODEL_LABEL_KEYS:
        value = raw.get(key)
        if value is None:
            labels[key] = ""
            continue
        labels[key] = str(value)
    return labels


def _parse_fitted_parameters(
    raw: object, filename: str
) -> tuple[FittedParameterView, ...]:
    if raw is None:
        return ()
    if not isinstance(raw, list):
        raise ValueError(
            f"{filename} の fitted_parameters はリストである必要があります。"
        )
    parsed: list[FittedParameterView] = []
    for index, entry in enumerate(raw):
        if not isinstance(entry, dict):
            raise ValueError(
                f"{filename} の fitted_parameters[{index}] が辞書ではありません。"
            )
        missing = [
            key for key in ("path", "value", "bound_status") if key not in entry
        ]
        if missing:
            raise ValueError(
                f"{filename} の fitted_parameters[{index}] に {missing} がありません。"
            )
        parsed.append(
            FittedParameterView(
                path=str(entry["path"]),
                value=float(entry["value"]),
                unit=_optional_str(entry.get("unit")),
                initial_value=_optional_float(entry.get("initial_value")),
                lower_bound=_optional_float(entry.get("lower_bound")),
                upper_bound=_optional_float(entry.get("upper_bound")),
                bound_status=str(entry["bound_status"]),
            )
        )
    return tuple(parsed)


def _parse_fit_metrics(raw: object, filename: str) -> FitMetricsView:
    if not isinstance(raw, dict):
        raise ValueError(f"{filename} に fit_metrics がありません。")
    missing = [key for key in _FIT_METRICS_KEYS if key not in raw]
    if missing:
        raise ValueError(
            f"{filename} の fit_metrics に {missing} がありません。"
        )
    return FitMetricsView(
        optimizer_success=bool(raw["optimizer_success"]),
        least_squares_cost=float(raw["least_squares_cost"]),
        overall_rmse_weighted_residual=float(
            raw["overall_rmse_weighted_residual"]
        ),
        n_residual_elements=int(raw["n_residual_elements"]),
        n_valid_curve_points=int(raw["n_valid_curve_points"]),
    )


def _optional_float(raw: object) -> float | None:
    if raw is None:
        return None
    if isinstance(raw, (int, float, str)):
        return float(raw)
    raise ValueError(f"数値に変換できません: {raw!r}")


def _optional_str(raw: object) -> str | None:
    if raw is None:
        return None
    return str(raw)
