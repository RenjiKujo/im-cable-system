"""Tests for section factories and ``ConfigSnapshotFactory``.

内部実装の単体テスト。``schema/`` は config 窓口に載せない非公開パッケージのため
リーフ直 import とする。

各セクション factory のキー欠損時のデフォルト補完と、値ありで不正な
ケースが ``ValueError`` で fail-fast することを担保する。集約 factory
（``ConfigSnapshotFactory``）も同様に各セクションへ正しくディスパッチする
ことを確認する。
"""

from __future__ import annotations

import pytest

from im_cable_system.engine.shared.config.schema.current_estimation import (
    ConvergenceCriterion,
    CurrentEstimationConfigFactory,
)
from im_cable_system.engine.shared.config.schema.data_processing import (
    DataProcessingConfigFactory,
    DataProcessingMethod,
)
from im_cable_system.engine.shared.config.schema.dump import (
    DumpDataConfigFactory,
)
from im_cable_system.engine.shared.config.schema.estimate_params import (
    EstimateParamsConfigFactory,
    OptimizerAlgorithm,
    ResidualNormalizationMethod,
    ResidualNormalizationStatistic,
)
from im_cable_system.engine.shared.config.schema.factory_config import (
    ConfigSnapshotFactory,
)
from im_cable_system.engine.shared.config.schema.input_validation import (
    InputValidationConfigFactory,
)
from im_cable_system.engine.shared.config.schema.logging import (
    LoggingConfigFactory,
    LogLevel,
)
from im_cable_system.engine.shared.config.schema.numerical_guard import (
    NumericalGuardConfigFactory,
)
from im_cable_system.engine.shared.config.schema.output_figures import (
    OutputFiguresConfigFactory,
)
from im_cable_system.engine.shared.config.schema.project_info import (
    ProjectInfoConfigFactory,
)
from im_cable_system.engine.shared.config.schema.severity import Severity
from im_cable_system.engine.shared.config.schema.validation import (
    ValidationConfigFactory,
)


class TestProjectInfo:
    def test_defaults_when_missing(self) -> None:
        info = ProjectInfoConfigFactory.create(None)
        assert info.project_name == ""
        assert info.version == ""
        assert info.default_encoding == "utf-8"
        assert info.timezone == "UTC"

    def test_explicit_values(self) -> None:
        info = ProjectInfoConfigFactory.create(
            {"project_name": "p", "timezone": "Asia/Tokyo"},
        )
        assert info.project_name == "p"
        assert info.timezone == "Asia/Tokyo"


class TestLogging:
    def test_defaults_when_missing(self) -> None:
        log = LoggingConfigFactory.create(None)
        assert log.default_log_level is LogLevel.INFO
        assert "%(asctime)s" in log.default_log_format

    def test_explicit_level(self) -> None:
        log = LoggingConfigFactory.create({"default_log_level": "DEBUG"})
        assert log.default_log_level is LogLevel.DEBUG

    def test_unknown_level_raises(self) -> None:
        with pytest.raises(ValueError, match="logging.default_log_level"):
            LoggingConfigFactory.create({"default_log_level": "NOT_A_LEVEL"})

    def test_non_dict_raises(self) -> None:
        with pytest.raises(ValueError, match="logging は dict"):
            LoggingConfigFactory.create("not-a-dict")


class TestInputValidation:
    def test_default(self) -> None:
        cfg = InputValidationConfigFactory.create(None)
        assert cfg.max_reference_axes_grid_points == 25_000_000

    def test_explicit(self) -> None:
        cfg = InputValidationConfigFactory.create(
            {"max_reference_axes_grid_points": 100},
        )
        assert cfg.max_reference_axes_grid_points == 100

    def test_non_numeric_raises(self) -> None:
        with pytest.raises(ValueError, match="整数に変換可能"):
            InputValidationConfigFactory.create(
                {"max_reference_axes_grid_points": "nope"},
            )

    def test_non_positive_raises(self) -> None:
        with pytest.raises(ValueError, match="正の整数"):
            InputValidationConfigFactory.create(
                {"max_reference_axes_grid_points": 0},
            )


class TestNumericalGuard:
    def test_default(self) -> None:
        cfg = NumericalGuardConfigFactory.create(None)
        assert cfg.eps == pytest.approx(1.0e-12)

    def test_explicit(self) -> None:
        cfg = NumericalGuardConfigFactory.create({"eps": 1.0e-9})
        assert cfg.eps == pytest.approx(1.0e-9)

    def test_non_positive_raises(self) -> None:
        with pytest.raises(ValueError, match="正の数値"):
            NumericalGuardConfigFactory.create({"eps": 0.0})


class TestDataProcessing:
    def test_defaults(self) -> None:
        cfg = DataProcessingConfigFactory.create(None)
        assert cfg.method is DataProcessingMethod.SEQUENTIAL
        assert cfg.max_workers is None
        assert cfg.timeout_seconds is None

    def test_explicit_thread(self) -> None:
        cfg = DataProcessingConfigFactory.create(
            {"method": "thread", "max_workers": 4, "timeout_seconds": 30.0},
        )
        assert cfg.method is DataProcessingMethod.THREAD
        assert cfg.max_workers == 4
        assert cfg.timeout_seconds == pytest.approx(30.0)

    def test_unknown_method_raises(self) -> None:
        with pytest.raises(ValueError, match="のいずれか"):
            DataProcessingConfigFactory.create({"method": "what"})

    def test_max_workers_non_positive_raises(self) -> None:
        with pytest.raises(ValueError, match="正の整数"):
            DataProcessingConfigFactory.create({"max_workers": 0})


class TestValidation:
    def test_defaults(self) -> None:
        cfg = ValidationConfigFactory.create(None)
        assert cfg.energy_conservation.enabled is True
        assert cfg.energy_conservation.severity is Severity.ERROR
        assert cfg.current_voltage_range.severity is Severity.WARNING

    def test_explicit(self) -> None:
        cfg = ValidationConfigFactory.create(
            {
                "energy_conservation": {
                    "enabled": False,
                    "severity": "INFO",
                    "tolerance": 1.0e-3,
                },
                "current_voltage_range": {
                    "enabled": True,
                    "severity": "ERROR",
                    "voltage_tolerance": 0.2,
                    "current_tolerance": 5.0,
                },
            },
        )
        assert cfg.energy_conservation.enabled is False
        assert cfg.energy_conservation.severity is Severity.INFO
        assert cfg.energy_conservation.tolerance == pytest.approx(1.0e-3)
        assert cfg.current_voltage_range.severity is Severity.ERROR
        assert cfg.current_voltage_range.voltage_tolerance == pytest.approx(
            0.2,
        )

    def test_unknown_severity_raises(self) -> None:
        with pytest.raises(ValueError, match="のいずれか"):
            ValidationConfigFactory.create(
                {"energy_conservation": {"severity": "FATAL"}},
            )

    def test_non_bool_enabled_raises(self) -> None:
        with pytest.raises(ValueError, match="bool"):
            ValidationConfigFactory.create(
                {"energy_conservation": {"enabled": "true"}},
            )

    def test_tolerance_non_positive_raises(self) -> None:
        with pytest.raises(ValueError, match="正の数値"):
            ValidationConfigFactory.create(
                {"energy_conservation": {"tolerance": 0.0}},
            )


class TestCurrentEstimation:
    def test_defaults(self) -> None:
        cfg = CurrentEstimationConfigFactory.create(None)
        assert cfg.convergence_failure_severity is Severity.WARNING
        assert cfg.iteration.max_iterations == 20
        assert cfg.iteration.convergence_tolerance == pytest.approx(1.0e-6)
        assert (
            cfg.iteration.convergence_criterion
            is ConvergenceCriterion.LINE_CURRENT
        )

    def test_explicit(self) -> None:
        cfg = CurrentEstimationConfigFactory.create(
            {
                "convergence_failure_severity": "ERROR",
                "iteration": {
                    "max_iterations": 100,
                    "convergence_tolerance": 1.0e-9,
                    "convergence_criterion": "max_over_merged_currents",
                },
            },
        )
        assert cfg.convergence_failure_severity is Severity.ERROR
        assert cfg.iteration.max_iterations == 100
        assert cfg.iteration.convergence_tolerance == pytest.approx(1.0e-9)
        assert (
            cfg.iteration.convergence_criterion
            is ConvergenceCriterion.MAX_OVER_MERGED_CURRENTS
        )

    def test_unknown_criterion_raises(self) -> None:
        with pytest.raises(ValueError, match="のいずれか"):
            CurrentEstimationConfigFactory.create(
                {"iteration": {"convergence_criterion": "unknown"}},
            )

    def test_max_iterations_non_positive_raises(self) -> None:
        with pytest.raises(ValueError, match="正の整数"):
            CurrentEstimationConfigFactory.create(
                {"iteration": {"max_iterations": 0}},
            )

    def test_tolerance_non_positive_raises(self) -> None:
        with pytest.raises(ValueError, match="正の数値"):
            CurrentEstimationConfigFactory.create(
                {"iteration": {"convergence_tolerance": 0.0}},
            )


class TestEstimateParams:
    def test_defaults(self) -> None:
        cfg = EstimateParamsConfigFactory.create(None)
        weights = cfg.residual.weights
        assert weights.current == pytest.approx(1.0)
        assert weights.efficiency == pytest.approx(1.0)
        assert (
            cfg.residual.normalization.method
            is ResidualNormalizationMethod.BY_CURVE_SCALE
        )
        assert (
            cfg.residual.normalization.statistic
            is ResidualNormalizationStatistic.STD
        )
        assert cfg.optimizer.algorithm is OptimizerAlgorithm.LEAST_SQUARES
        assert cfg.optimizer.max_nfev == 100
        assert cfg.optimizer.least_squares.max_nfev == 100
        assert cfg.optimizer.ftol == pytest.approx(1.0e-8)

    def test_explicit(self) -> None:
        cfg = EstimateParamsConfigFactory.create(
            {
                "residual": {
                    "weights": {
                        "current": 2.0,
                        "power": 0.0,
                    },
                    "normalization": {
                        "method": "by_reference",
                        "by_reference": {
                            "statistic": "max",
                            "eps": 1.0e-9,
                        },
                    },
                },
                "optimizer": {
                    "algorithm": "least_squares",
                    "least_squares": {"max_nfev": 50, "ftol": 1.0e-12},
                },
            },
        )
        assert cfg.residual.weights.current == pytest.approx(2.0)
        assert cfg.residual.weights.power == pytest.approx(0.0)
        assert (
            cfg.residual.normalization.method
            is ResidualNormalizationMethod.BY_REFERENCE
        )
        assert (
            cfg.residual.normalization.statistic
            is ResidualNormalizationStatistic.MAX
        )
        assert cfg.optimizer.max_nfev == 50
        assert cfg.optimizer.ftol == pytest.approx(1.0e-12)

    def test_negative_weight_raises(self) -> None:
        with pytest.raises(ValueError, match="非負"):
            EstimateParamsConfigFactory.create(
                {"residual": {"weights": {"current": -0.1}}},
            )

    def test_unknown_optimizer_algorithm_raises(self) -> None:
        with pytest.raises(ValueError, match="のいずれか"):
            EstimateParamsConfigFactory.create(
                {"optimizer": {"algorithm": "wat"}},
            )


class TestOutputFigures:
    def test_defaults(self) -> None:
        cfg = OutputFiguresConfigFactory.create(None)
        assert cfg.show is False
        assert cfg.show_duration_seconds == pytest.approx(3.0)

    def test_explicit(self) -> None:
        cfg = OutputFiguresConfigFactory.create(
            {"show": True, "show_duration_seconds": 5.0},
        )
        assert cfg.show is True
        assert cfg.show_duration_seconds == pytest.approx(5.0)

    def test_non_numeric_duration_raises(self) -> None:
        with pytest.raises(ValueError, match="数値に変換可能"):
            OutputFiguresConfigFactory.create(
                {"show_duration_seconds": "not-a-number"},
            )

    def test_negative_duration_raises(self) -> None:
        with pytest.raises(ValueError, match="非負"):
            OutputFiguresConfigFactory.create({"show_duration_seconds": -1.0})


class TestDumpData:
    def test_defaults(self) -> None:
        cfg = DumpDataConfigFactory.create(None)
        assert cfg.figures.enabled is False
        assert cfg.figures.sub_dir == "figures"
        assert cfg.tables.enabled is False
        assert cfg.reports.enabled is False
        assert cfg.reports.sub_dir == "reports"
        assert cfg.reports.fit_summary_pattern.endswith(".csv")
        assert cfg.reports.fitted_catalog_pattern.endswith(".yaml")
        assert cfg.reports.numerical_stability_pattern.endswith(".csv")
        assert cfg.dtos.input_dtos.sub_dir == "dtos/input"
        assert cfg.dtos.itm_dtos.sub_dir == "dtos/itm"
        assert cfg.dtos.output_dtos.sub_dir == "dtos/output"

    def test_explicit(self) -> None:
        cfg = DumpDataConfigFactory.create(
            {
                "output": {
                    "figures": {
                        "enabled": True,
                        "sub_dir": "out_figs",
                        "filename_pattern": "f_{kind}_{timestamp}.png",
                    },
                    "tables": {"enabled": True},
                    "reports": {"enabled": True, "sub_dir": "out_reports"},
                },
                "execute": {"dtos": {"enabled": True}},
            },
        )
        assert cfg.figures.enabled is True
        assert cfg.figures.sub_dir == "out_figs"
        assert cfg.tables.enabled is True
        assert cfg.reports.enabled is True
        assert cfg.reports.sub_dir == "out_reports"
        assert cfg.dtos.itm_dtos.enabled is True
        # 未指定の input_dtos は既定で disabled。
        assert cfg.dtos.input_dtos.enabled is False


class TestConfigSnapshotFactory:
    def test_empty_yaml_uses_all_defaults(self) -> None:
        snap = ConfigSnapshotFactory.create({})
        assert snap.project_info.timezone == "UTC"
        assert snap.numerical_guard.eps == pytest.approx(1.0e-12)
        assert snap.data_processing.method is DataProcessingMethod.SEQUENTIAL
        assert (
            snap.current_estimation.iteration.convergence_criterion
            is ConvergenceCriterion.LINE_CURRENT
        )

    def test_bundled_like_structure_round_trips(self) -> None:
        raw = {
            "project_info": {"timezone": "Asia/Tokyo"},
            "calculation": {
                "execute": {
                    "data_processing": {
                        "method": "thread",
                        "max_workers": 8,
                    },
                    "numerical_guard": {"eps": 1.0e-10},
                    "current_estimation": {
                        "convergence_failure_severity": "ERROR",
                        "iteration": {
                            "max_iterations": 10,
                            "convergence_tolerance": 1.0e-4,
                            "convergence_criterion": "phase_current",
                        },
                    },
                },
                "output": {"figures": {"show": True}},
            },
        }
        snap = ConfigSnapshotFactory.create(raw)
        assert snap.project_info.timezone == "Asia/Tokyo"
        assert snap.data_processing.method is DataProcessingMethod.THREAD
        assert snap.data_processing.max_workers == 8
        assert snap.numerical_guard.eps == pytest.approx(1.0e-10)
        assert (
            snap.current_estimation.convergence_failure_severity
            is Severity.ERROR
        )
        assert (
            snap.current_estimation.iteration.convergence_criterion
            is ConvergenceCriterion.PHASE_CURRENT
        )
        assert snap.output_figures.show is True

    def test_bad_section_raises_with_key_path(self) -> None:
        raw = {
            "calculation": {
                "execute": {
                    "current_estimation": {
                        "iteration": {"max_iterations": -5},
                    },
                },
            },
        }
        with pytest.raises(ValueError, match="max_iterations"):
            ConfigSnapshotFactory.create(raw)
