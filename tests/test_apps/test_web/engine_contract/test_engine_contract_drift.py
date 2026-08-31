"""apps は engine を import しないので写しが存在する。この写しが engine から離れたらここが落ちる。

内部実装の単体テスト: drift 検出のため engine 側の Enum・
``unified_input_parser._CANDIDATE_AXIS_LABELS``・
``fitted_catalog_builder.build_fitted_catalog`` を直接参照する。

``report_model_*.yaml`` の形は engine 側 builder の戻り値が正本なので、
固定サンプル YAML ではなく **builder を実際に呼んで** キー集合を突き合わせる
（固定ファイルは engine と一緒に動かないため、キー改名を検出できない）。
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from apps.web.engine_contract import (
    CANDIDATE_AXIS_KINDS,
    IM_FRICTION_WINDAGE_KINDS,
    IM_STRAY_LOAD_KINDS,
    REQUIRED_CANDIDATE_AXIS_LABELS,
    list_fitted_catalogs,
)
from apps.web.engine_contract.estimate_params_input import (
    csv_delimiter_for_filename,
)
from apps.web.engine_contract.fit_report import (  # noqa: PLC2701
    _FIT_METRICS_KEYS,
    _MODEL_LABEL_KEYS,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data.estimate_params.unified_input_parser import (  # noqa: PLC2701
    _CANDIDATE_AXIS_LABELS,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data.util.csv_utils import (
    csv_delimiter_for_path,
)
from im_cable_system.engine.algorithm.output_algorithm.make_report.estimate_params.fitted_catalog_builder import (
    build_fitted_catalog,
)
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ConductorModelType,
    ImExcitationModelType,
    ImFrictionWindageModelType,
    ImPrimaryModelType,
    ImSecondaryModelType,
    ImStrayLoadModelType,
)
from im_cable_system.engine.shared.dto.generic.reporting import (
    EstimateParamsFitSummaryDto,
    FitChannelMetricDto,
    FittedModelLabelsDto,
    FittedParameterReportDto,
    OptimizerResultDto,
    OptimizerSettingsDto,
    ResidualObjectiveSettingsDto,
)


def _channel_metric() -> FitChannelMetricDto:
    return FitChannelMetricDto(n_valid=1, rmse=0.0, std_delta=0.0, unit="A")


def _fit_summary() -> EstimateParamsFitSummaryDto:
    """builder を呼ぶのに最低限必要な要約 DTO（値そのものは検証対象ではない）。"""
    return EstimateParamsFitSummaryDto(
        model_labels=FittedModelLabelsDto(
            im_primary="P",
            im_excitation="E",
            im_secondary_inner=None,
            im_secondary_outer="S",
            im_friction_windage="NONE",
            im_stray_load="NONE",
            cable_conductor=None,
        ),
        optimizer_settings=OptimizerSettingsDto(
            algorithm="least_squares",
            max_nfev=1,
            ftol=1e-8,
            xtol=1e-8,
            gtol=1e-8,
        ),
        residual_objective_settings=ResidualObjectiveSettingsDto(
            current_weight=1.0,
            power_weight=1.0,
            power_factor_weight=1.0,
            efficiency_weight=1.0,
            normalization_method="by_curve_scale",
            normalization_statistic="std",
            normalization_eps=1e-12,
            normalize_by_point_count=False,
        ),
        optimizer_result=OptimizerResultDto(
            success=True, message="ok", nfev=1, cost=0.0
        ),
        overall_rmse_weighted_residual=0.0,
        n_residual_elements=1,
        n_valid_curve_points=1,
        line_current=_channel_metric(),
        output_power=_channel_metric(),
        power_factor=_channel_metric(),
        im_efficiency=_channel_metric(),
        fitted_parameters=(
            FittedParameterReportDto(
                path="im.primary.r1",
                initial_value=1.0,
                fitted_value=1.5,
                lower_bound=0.5,
                upper_bound=2.0,
                unit="ohm",
                is_fixed=False,
                is_at_lower_bound=False,
                is_at_upper_bound=False,
            ),
        ),
    )


def _built_catalog() -> dict[str, object]:
    return build_fitted_catalog(
        name="sample",
        summary=_fit_summary(),
        nameplate_power_w=1000.0,
        nameplate_current_a=10.0,
    )


class TestEngineContractDrift:
    """apps 側の写しが engine の種別・軸ラベル・区切り文字規則と一致すること。"""

    def test_friction_windage_kinds_match_enum(self) -> None:
        assert set(IM_FRICTION_WINDAGE_KINDS) == {
            member.value for member in ImFrictionWindageModelType
        }

    def test_stray_load_kinds_match_enum(self) -> None:
        assert set(IM_STRAY_LOAD_KINDS) == {
            member.value for member in ImStrayLoadModelType
        }

    def test_required_axis_labels_are_in_engine_candidate_labels(self) -> None:
        engine_labels = set(_CANDIDATE_AXIS_LABELS)
        for label in REQUIRED_CANDIDATE_AXIS_LABELS:
            assert label in engine_labels

    def test_candidate_axis_kinds_cover_exactly_engine_labels(self) -> None:
        """種別語彙の写しが engine の候補軸ラベルと 1:1 であること。

        engine 側に軸が増えたら、その軸の語彙を写し忘れたままプリフライトが
        素通りするので、キー集合の一致まで見る。
        """
        assert set(CANDIDATE_AXIS_KINDS) == set(_CANDIDATE_AXIS_LABELS)

    def test_primary_kinds_match_enum(self) -> None:
        assert set(CANDIDATE_AXIS_KINDS["im_primary"]) == {
            member.value for member in ImPrimaryModelType
        }

    def test_excitation_kinds_match_enum(self) -> None:
        assert set(CANDIDATE_AXIS_KINDS["im_excitation"]) == {
            member.value for member in ImExcitationModelType
        }

    @pytest.mark.parametrize(
        "label",
        [
            "im_secondary(single)",
            "im_secondary(double_inner)",
            "im_secondary(double_outer)",
        ],
    )
    def test_secondary_kinds_match_enum(self, label: str) -> None:
        assert set(CANDIDATE_AXIS_KINDS[label]) == {
            member.value for member in ImSecondaryModelType
        }

    def test_cable_conductor_kinds_match_enum_plus_none(self) -> None:
        """導体軸だけ ``NONE`` が Enum メンバではなく「ケーブル無し」の特別値。"""
        assert set(CANDIDATE_AXIS_KINDS["cable_conductor_model"]) == {
            member.value for member in ConductorModelType
        } | {"NONE"}

    def test_axis_kinds_match_the_standalone_loss_tuples(self) -> None:
        """軸出力控除 2 軸は、既存の公開タプルと同じ語彙を指すこと。"""
        assert (
            CANDIDATE_AXIS_KINDS["im_friction_windage"]
            == IM_FRICTION_WINDAGE_KINDS
        )
        assert CANDIDATE_AXIS_KINDS["im_stray_load"] == IM_STRAY_LOAD_KINDS

    def test_model_label_keys_match_builder(self) -> None:
        """``_MODEL_LABEL_KEYS`` が builder の出す ``model_labels`` と一致する。"""
        built = _built_catalog()
        labels = built["model_labels"]
        assert isinstance(labels, dict)
        assert set(_MODEL_LABEL_KEYS) == set(labels)

    def test_fit_metrics_keys_match_builder(self) -> None:
        """``_FIT_METRICS_KEYS`` が builder の出す ``fit_metrics`` と一致する。"""
        built = _built_catalog()
        metrics = built["fit_metrics"]
        assert isinstance(metrics, dict)
        assert set(_FIT_METRICS_KEYS) == set(metrics)

    def test_top_level_keys_cover_what_apps_reads(self) -> None:
        """apps が読むトップレベルキーが builder の出力に揃っている。"""
        built = _built_catalog()
        assert {
            "name",
            "nameplate",
            "model_labels",
            "fitted_parameters",
            "fit_metrics",
        } <= set(built)

    def test_nameplate_and_parameter_fields_match_builder(self) -> None:
        """``nameplate`` と ``fitted_parameters`` の要素フィールドが写しと一致する。

        ``fit_report._parse_*`` が名指しで取り出すキーを、builder の出力側から
        逆に確認する（片側だけ改名されたら落ちる）。
        """
        built = _built_catalog()
        nameplate = built["nameplate"]
        assert isinstance(nameplate, dict)
        assert set(nameplate) == {"power", "current"}
        for quantity in nameplate.values():
            assert isinstance(quantity, dict)
            assert set(quantity) == {"value", "unit"}

        parameters = built["fitted_parameters"]
        assert isinstance(parameters, list)
        assert set(parameters[0]) == {
            "path",
            "value",
            "unit",
            "initial_value",
            "lower_bound",
            "upper_bound",
            "bound_status",
        }

    def test_apps_can_parse_what_the_builder_emits(self, tmp_path) -> None:
        """builder の出力を YAML に落として、apps 側パーサが読めること。

        キー集合の一致だけでなく、値の型（bool / float / int）まで往復させる。
        固定サンプルではなく毎回 builder から生成するので、engine 側が形を
        変えればここが落ちる。
        """
        report_path = tmp_path / "report_model_drift_check.yaml"
        report_path.write_text(
            yaml.safe_dump(_built_catalog(), allow_unicode=True),
            encoding="utf-8",
        )

        views = list_fitted_catalogs(tmp_path)

        assert [view.name for view in views] == ["sample"]
        assert views[0].fit_metrics.optimizer_success is True
        assert views[0].fitted_parameters[0].bound_status == "interior"

    def test_delimiter_rule_matches_engine(self) -> None:
        assert csv_delimiter_for_filename(
            "input.tsv"
        ) == csv_delimiter_for_path(Path("input.tsv"))
        assert csv_delimiter_for_filename(
            "input.csv"
        ) == csv_delimiter_for_path(Path("input.csv"))
        assert csv_delimiter_for_filename(
            "input.CSV"
        ) == csv_delimiter_for_path(Path("input.CSV"))
