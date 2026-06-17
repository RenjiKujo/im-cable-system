"""Tests for :class:`Config` (application configuration facade).

正常系（既定値・派生プロパティの正規化）と、``Config.create`` 時点での
fail-fast バリデーションを担保する。各セクションの詳細な値域チェックは
``schema/test_factory_config.py`` で担保しているため、本ファイルでは
Config を経由したときの振る舞い（同梱 YAML での代表値・既定値補完・
不正値時の即時 ``ValueError``）に絞る。
"""

from __future__ import annotations

from pathlib import Path

import pytest

from im_cable_system.engine.shared.config import (
    Config,
    ConvergenceCriterion,
    DataProcessingMethod,
    IConfig,
    LogLevel,
    Severity,
)

_REPO_ROOT = Path(__file__).resolve().parents[3]
_BOUNDS_DIR = _REPO_ROOT / "src" / "im_cable_system" / "bounds_and_init"
_BUNDLED_CONFIG_YAML = (
    _REPO_ROOT
    / "src"
    / "im_cable_system"
    / "engine"
    / "shared"
    / "config"
    / "config.yaml"
)


def _write_yaml(path: Path, body: str) -> Path:
    path.write_text(body, encoding="utf-8")
    return path


class TestConfigFactoryAndContract:
    """ファクトリと :class:`IConfig` 契約の最低限。"""

    def test_create_returns_iconfig(self) -> None:
        config = Config.create(config_file_path=_BUNDLED_CONFIG_YAML)
        assert isinstance(config, IConfig)

    def test_config_file_path_property(self) -> None:
        config = Config.create(config_file_path=_BUNDLED_CONFIG_YAML)
        assert config.config_file_path == _BUNDLED_CONFIG_YAML

    def test_create_without_config_file_path_uses_packaged_default(
        self,
    ) -> None:
        """``config_file_path`` 省略時は同梱 ``config.yaml`` を読み込む。"""
        config = Config.create()
        assert isinstance(config, IConfig)
        assert (
            config.config_file_path.resolve() == _BUNDLED_CONFIG_YAML.resolve()
        )
        info = config.project_info
        assert info.project_name == "im_cable_system"


class TestBundledConfigDerivedValues:
    """同梱 ``config.yaml`` から派生値を取り出す経路の正常系。"""

    @pytest.fixture
    def config(self) -> IConfig:
        return Config.create(config_file_path=_BUNDLED_CONFIG_YAML)

    def test_project_info_has_required_fields(self, config: IConfig) -> None:
        info = config.project_info
        assert info.project_name == "im_cable_system"
        assert info.default_encoding == "utf-8"
        assert info.timezone

    def test_logging_config_uses_yaml_values(self, config: IConfig) -> None:
        log_conf = config.logging_config
        assert log_conf.default_log_level == "INFO"
        assert "%(asctime)s" in log_conf.default_log_format

    def test_data_processing_defaults(self, config: IConfig) -> None:
        dp = config.data_processing
        assert dp.method is DataProcessingMethod.SEQUENTIAL
        assert dp.max_workers == 4

    def test_numerical_guard_eps_is_finite_positive(
        self,
        config: IConfig,
    ) -> None:
        eps = config.numerical_guard_config.eps
        assert eps > 0.0

    def test_validation_config_uses_yaml_values(
        self,
        config: IConfig,
    ) -> None:
        validation = config.validation_config
        assert validation.energy_conservation.enabled is True
        assert validation.energy_conservation.severity is Severity.ERROR
        assert validation.current_voltage_range.severity is Severity.WARNING

    def test_current_estimation_config_uses_yaml_values(
        self,
        config: IConfig,
    ) -> None:
        current_estimation = config.current_estimation_config
        assert (
            current_estimation.convergence_failure_severity is Severity.WARNING
        )
        assert current_estimation.iteration.max_iterations == 50
        assert (
            current_estimation.iteration.convergence_criterion
            is ConvergenceCriterion.LINE_CURRENT
        )

    def test_max_reference_axes_grid_points_matches_yaml(
        self,
        config: IConfig,
    ) -> None:
        """同梱 ``config.yaml`` の値を素直に返す。"""
        assert (
            config.input_validation_config.max_reference_axes_grid_points
            == 25_000_000
        )

    def test_dump_data_config_has_required_sections(
        self,
        config: IConfig,
    ) -> None:
        dump = config.dump_data_config
        # figures / tables / dtos がすべて attribute として揃う。
        assert dump.figures.sub_dir == "figures"
        assert dump.tables.sub_dir == "tables"
        assert dump.dtos.input_dtos.sub_dir == "dtos/input"
        assert dump.dtos.itm_dtos.sub_dir == "dtos/itm"
        assert dump.dtos.output_dtos.sub_dir == "dtos/output"

    def test_output_figures_config_uses_yaml_values(
        self,
        config: IConfig,
    ) -> None:
        figures = config.output_figures_config
        assert figures.show is False
        assert figures.show_duration_seconds == pytest.approx(3.0)

    def test_get_dump_base_dir_raises_on_bundled_config(
        self,
        config: IConfig,
    ) -> None:
        """同梱 ``config.yaml`` には ``base_dir`` を置かないので未指定エラー。"""
        with pytest.raises(ValueError):
            config.get_dump_base_dir()


class TestMinimalYamlFallbacks:
    """欠損キーに対する既定値補完の挙動。"""

    @pytest.fixture
    def minimal_config(self, tmp_path: Path) -> IConfig:
        path = _write_yaml(tmp_path / "minimal.yaml", "project_info: {}\n")
        return Config.create(config_file_path=path)

    def test_project_info_defaults_are_filled(
        self,
        minimal_config: IConfig,
    ) -> None:
        info = minimal_config.project_info
        assert info.default_encoding == "utf-8"
        assert info.timezone == "UTC"
        assert info.project_name == ""

    def test_logging_config_defaults(self, minimal_config: IConfig) -> None:
        log_conf = minimal_config.logging_config
        assert log_conf.default_log_level is LogLevel.INFO
        assert "%(asctime)s" in log_conf.default_log_format

    def test_numerical_guard_eps_default(
        self,
        minimal_config: IConfig,
    ) -> None:
        assert minimal_config.numerical_guard_config.eps == 1.0e-12

    def test_validation_defaults(self, minimal_config: IConfig) -> None:
        validation = minimal_config.validation_config
        assert validation.energy_conservation.enabled is True
        assert validation.energy_conservation.tolerance == pytest.approx(
            1.0e-6,
        )

    def test_current_estimation_defaults(
        self,
        minimal_config: IConfig,
    ) -> None:
        ce = minimal_config.current_estimation_config
        assert ce.convergence_failure_severity is Severity.WARNING
        assert ce.iteration.max_iterations == 20
        assert (
            ce.iteration.convergence_criterion
            is ConvergenceCriterion.LINE_CURRENT
        )

    def test_max_reference_axes_grid_points_default(
        self,
        minimal_config: IConfig,
    ) -> None:
        """YAML キー欠損ならコード側フォールバック ``25_000_000``。"""
        assert (
            minimal_config.input_validation_config.max_reference_axes_grid_points
            == 25_000_000
        )

    def test_series_catalog_path_raises_when_unset(
        self,
        minimal_config: IConfig,
    ) -> None:
        """yaml にも create 引数にもパスが無ければ ValueError。"""
        with pytest.raises(ValueError):
            minimal_config.get_im_series_catalog_file_path()
        with pytest.raises(ValueError):
            minimal_config.get_cable_series_catalog_file_path()

    def test_bounds_and_init_path_raises_when_unset(
        self,
        minimal_config: IConfig,
    ) -> None:
        """yaml にも create 引数にもパスが無ければ ValueError。"""
        with pytest.raises(ValueError):
            minimal_config.get_im_bounds_and_init_file_path()
        with pytest.raises(ValueError):
            minimal_config.get_cable_bounds_and_init_file_path()

    def test_create_with_bounds_paths_overrides_defaults(self) -> None:
        """create 引数で渡した bounds が yaml デフォルトより優先される。"""
        explicit_im = _BOUNDS_DIR / "im_descriptor_bounds_and_init.yaml"
        explicit_cable = _BOUNDS_DIR / "cable_descriptor_bounds_and_init.yaml"
        config = Config.create(
            config_file_path=_BUNDLED_CONFIG_YAML,
            im_bounds_and_init_file_path=explicit_im,
            cable_bounds_and_init_file_path=explicit_cable,
        )
        assert (
            config.get_im_bounds_and_init_file_path() == explicit_im.resolve()
        )
        assert (
            config.get_cable_bounds_and_init_file_path()
            == explicit_cable.resolve()
        )

    def test_create_with_catalog_paths_overrides_defaults(
        self,
        tmp_path: Path,
    ) -> None:
        """create 引数で渡したカタログパスが yaml デフォルトより優先される。"""
        explicit_im = tmp_path / "im_catalog.yaml"
        explicit_cable = tmp_path / "cable_catalog.yaml"
        explicit_im.write_text("dummy: true\n", encoding="utf-8")
        explicit_cable.write_text("dummy: true\n", encoding="utf-8")
        config = Config.create(
            config_file_path=_BUNDLED_CONFIG_YAML,
            im_series_catalog_file_path=explicit_im,
            cable_series_catalog_file_path=explicit_cable,
        )
        assert config.get_im_series_catalog_file_path() == explicit_im.resolve()
        assert (
            config.get_cable_series_catalog_file_path()
            == explicit_cable.resolve()
        )


class TestYamlRobustness:
    """``Config.create`` 時の fail-fast バリデーションと dump 関係の挙動。"""

    def test_dump_base_dir_raises_when_blank(
        self,
        tmp_path: Path,
    ) -> None:
        """``base_dir`` が空文字なら ``get_dump_base_dir`` で ValueError。"""
        path = _write_yaml(
            tmp_path / "blank_base.yaml",
            "dump:\n  base_dir: ''\n",
        )
        config = Config.create(config_file_path=path)
        with pytest.raises(ValueError):
            config.get_dump_base_dir()

    def test_dump_base_dir_resolves_relative_against_config_parent(
        self,
        tmp_path: Path,
    ) -> None:
        """``base_dir`` が相対パスなら、その ``config.yaml`` 親ディレクトリ基準で解決。"""
        path = _write_yaml(
            tmp_path / "relative_base.yaml",
            "dump:\n  base_dir: 'dump'\n",
        )
        config = Config.create(config_file_path=path)
        assert config.get_dump_base_dir() == (tmp_path / "dump").resolve()

    def test_dump_base_dir_uses_yaml_when_absolute(
        self,
        tmp_path: Path,
    ) -> None:
        """yaml に絶対パスが書かれていればそれを返す。"""
        abs_dir = (tmp_path / "outputs").resolve()
        path = _write_yaml(
            tmp_path / "abs_base.yaml",
            f"dump:\n  base_dir: '{abs_dir}'\n",
        )
        config = Config.create(config_file_path=path)
        assert config.get_dump_base_dir() == abs_dir

    def test_dump_base_dir_create_override_wins(
        self,
        tmp_path: Path,
    ) -> None:
        """create 引数（絶対パス）が yaml の値より優先される。"""
        yaml_abs = (tmp_path / "yaml_outputs").resolve()
        override_abs = (tmp_path / "override_outputs").resolve()
        path = _write_yaml(
            tmp_path / "abs_base_with_override.yaml",
            f"dump:\n  base_dir: '{yaml_abs}'\n",
        )
        config = Config.create(
            config_file_path=path,
            dump_base_dir=override_abs,
        )
        assert config.get_dump_base_dir() == override_abs

    def test_create_raises_when_dump_base_dir_is_relative(
        self,
        tmp_path: Path,
    ) -> None:
        """create 引数 ``dump_base_dir`` は絶対パス必須。"""
        path = _write_yaml(
            tmp_path / "any.yaml",
            "project_info: {}\n",
        )
        with pytest.raises(ValueError):
            Config.create(
                config_file_path=path,
                dump_base_dir=Path("relative_outputs"),
            )

    def test_create_raises_on_non_positive_numerical_guard_eps(
        self,
        tmp_path: Path,
    ) -> None:
        """``numerical_guard.eps`` の 0 / 負値は ``Config.create`` で fail-fast。"""
        path = _write_yaml(
            tmp_path / "non_positive_eps.yaml",
            "calculation:\n  execute:\n    numerical_guard:\n      eps: 0\n",
        )
        with pytest.raises(ValueError, match="numerical_guard.eps"):
            Config.create(config_file_path=path)

    def test_create_raises_on_non_numeric_grid_points(
        self,
        tmp_path: Path,
    ) -> None:
        """非数値値は ``Config.create`` 時点で fail-fast。"""
        path = _write_yaml(
            tmp_path / "bad_grid_points.yaml",
            "calculation:\n"
            "  input:\n"
            "    validation:\n"
            "      max_reference_axes_grid_points: 'not-an-int'\n",
        )
        with pytest.raises(ValueError, match="max_reference_axes_grid_points"):
            Config.create(config_file_path=path)

    def test_create_raises_on_non_positive_grid_points(
        self,
        tmp_path: Path,
    ) -> None:
        """0 / 負値も ``Config.create`` 時点で fail-fast。"""
        path = _write_yaml(
            tmp_path / "non_positive_grid_points.yaml",
            "calculation:\n"
            "  input:\n"
            "    validation:\n"
            "      max_reference_axes_grid_points: 0\n",
        )
        with pytest.raises(ValueError, match="max_reference_axes_grid_points"):
            Config.create(config_file_path=path)

    def test_create_accepts_explicit_grid_points(
        self,
        tmp_path: Path,
    ) -> None:
        """正の整数なら YAML 値をそのまま採用する。"""
        path = _write_yaml(
            tmp_path / "explicit_grid_points.yaml",
            "calculation:\n"
            "  input:\n"
            "    validation:\n"
            "      max_reference_axes_grid_points: 100\n",
        )
        config = Config.create(config_file_path=path)
        assert (
            config.input_validation_config.max_reference_axes_grid_points == 100
        )

    def test_create_raises_on_non_numeric_figures_duration(
        self,
        tmp_path: Path,
    ) -> None:
        path = _write_yaml(
            tmp_path / "bad_figures.yaml",
            "calculation:\n"
            "  output:\n"
            "    figures:\n"
            "      show: true\n"
            "      show_duration_seconds: 'not-a-number'\n",
        )
        with pytest.raises(ValueError, match="show_duration_seconds"):
            Config.create(config_file_path=path)

    def test_create_raises_when_logging_node_is_not_dict(
        self,
        tmp_path: Path,
    ) -> None:
        path = _write_yaml(
            tmp_path / "type_mismatch.yaml",
            "logging: 'not-a-dict'\n",
        )
        with pytest.raises(ValueError, match="logging"):
            Config.create(config_file_path=path)

    def test_create_raises_on_unknown_log_level(
        self,
        tmp_path: Path,
    ) -> None:
        """``LogLevel`` Enum 外のレベル名は ``Config.create`` 時点で fail-fast。"""
        path = _write_yaml(
            tmp_path / "bad_log_level.yaml",
            "logging:\n  default_log_level: NOT_A_LEVEL\n",
        )
        with pytest.raises(ValueError, match="logging.default_log_level"):
            Config.create(config_file_path=path)
