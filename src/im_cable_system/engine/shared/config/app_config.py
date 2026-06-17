"""Application configuration (``app_`` = runtime config facade).

モジュール名の ``app_`` は、実行時アプリケーション設定の窓口であることを示し、
汎用語 ``config`` モジュール名との混同を避けるため付与している。

設計方針（YAML スキーマ検証）:
    ``Config.create`` 時に
    :class:`im_cable_system.engine.shared.config.schema.factory_config.ConfigSnapshotFactory`
    が YAML 全体を検証・正規化し、不正値はその時点で ``ValueError`` で
    弾く（fail-fast）。各プロパティは保持済みスナップショットからの
    attribute アクセスを返すだけの薄い facade。

使い方、YAML スキーマ、2 段フォールバック、各メソッド返り値の構造などの
詳細は ``docs/shared/config_and_logger.md`` を参照する。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from im_cable_system.engine.shared.config.config_reader import load_config
from im_cable_system.engine.shared.config.i_app_config import IConfig
from im_cable_system.engine.shared.config.schema.config_snapshot import (
    ConfigSnapshot,
)
from im_cable_system.engine.shared.config.schema.current_estimation import (
    CurrentEstimationConfig,
)
from im_cable_system.engine.shared.config.schema.data_processing import (
    DataProcessingConfig,
)
from im_cable_system.engine.shared.config.schema.dump import (
    DumpDataConfig,
)
from im_cable_system.engine.shared.config.schema.estimate_params import (
    EstimateParamsConfig,
)
from im_cable_system.engine.shared.config.schema.factory_config import (
    ConfigSnapshotFactory,
)
from im_cable_system.engine.shared.config.schema.input_validation import (
    InputValidationConfig,
)
from im_cable_system.engine.shared.config.schema.logging import (
    LoggingConfig,
)
from im_cable_system.engine.shared.config.schema.numerical_guard import (
    NumericalGuardConfig,
)
from im_cable_system.engine.shared.config.schema.output_figures import (
    OutputFiguresConfig,
)
from im_cable_system.engine.shared.config.schema.project_info import (
    ProjectInfoConfig,
)
from im_cable_system.engine.shared.config.schema.validation import (
    ValidationConfig,
)


class Config(IConfig):
    """設定管理クラス。YAML を直接参照し、責務単位の API を提供する。

    各メソッド／プロパティの詳細仕様は ``IConfig`` の契約と、
    ``docs/shared/config_and_logger.md`` を参照する。
    """

    def __init__(
        self,
        *,
        config_file_path: Path | None = None,
        im_series_catalog_file_path: Path | None = None,
        cable_series_catalog_file_path: Path | None = None,
        im_bounds_and_init_file_path: Path | None = None,
        cable_bounds_and_init_file_path: Path | None = None,
        dump_base_dir: Path | None = None,
    ) -> None:
        """設定を初期化する（仕様は ``IConfig.create`` と ``docs/shared/config_and_logger.md`` を参照）。

        ``ConfigSnapshotFactory`` を経由するため、YAML スキーマに違反する値
        が混入していた場合は本コンストラクタが ``ValueError`` を送出する。

        Raises:
            ValueError: ``dump_base_dir`` が絶対パスでない場合、または
                ``config.yaml`` のスキーマ検証に失敗した場合。
        """
        if dump_base_dir is not None and not dump_base_dir.is_absolute():
            raise ValueError(
                "Config.create(dump_base_dir=...) は絶対パスで指定してください。"
                "config.yaml の dump.base_dir であれば、その config.yaml が"
                "あるディレクトリ基準の相対パスでも構いません。"
            )
        # NOTE: 同梱既定パスも明示パスも、以降の相対パス解決基準として揃えるため
        # ここで必ず resolve() する（呼び出し側が相対パスを渡しても安全）。
        resolved_config_file_path: Path = (
            config_file_path.resolve()
            if config_file_path is not None
            else (Path(__file__).resolve().parent / "config.yaml").resolve()
        )
        self._config_file_path: Path = resolved_config_file_path
        self._config_data: dict[str, Any] = load_config(
            resolved_config_file_path
        )
        self._snapshot: ConfigSnapshot = ConfigSnapshotFactory.create(
            self._config_data
        )
        self._im_series_catalog_file_path: Path | None = (
            im_series_catalog_file_path.resolve()
            if im_series_catalog_file_path is not None
            else None
        )
        self._cable_series_catalog_file_path: Path | None = (
            cable_series_catalog_file_path.resolve()
            if cable_series_catalog_file_path is not None
            else None
        )
        self._im_bounds_and_init_file_path: Path | None = (
            im_bounds_and_init_file_path.resolve()
            if im_bounds_and_init_file_path is not None
            else None
        )
        self._cable_bounds_and_init_file_path: Path | None = (
            cable_bounds_and_init_file_path.resolve()
            if cable_bounds_and_init_file_path is not None
            else None
        )
        self._dump_base_dir: Path | None = (
            dump_base_dir.resolve() if dump_base_dir is not None else None
        )

    @classmethod
    def create(
        cls,
        *,
        config_file_path: Path | None = None,
        im_series_catalog_file_path: Path | None = None,
        cable_series_catalog_file_path: Path | None = None,
        im_bounds_and_init_file_path: Path | None = None,
        cable_bounds_and_init_file_path: Path | None = None,
        dump_base_dir: Path | None = None,
    ) -> IConfig:
        """設定を取得するファクトリーメソッド（仕様は ``IConfig.create`` 参照）。

        Raises:
            ValueError: ``dump_base_dir`` が絶対パスでない場合、または
                ``config.yaml`` のスキーマ検証に失敗した場合。
        """
        return cls(
            config_file_path=config_file_path,
            im_series_catalog_file_path=im_series_catalog_file_path,
            cable_series_catalog_file_path=cable_series_catalog_file_path,
            im_bounds_and_init_file_path=im_bounds_and_init_file_path,
            cable_bounds_and_init_file_path=cable_bounds_and_init_file_path,
            dump_base_dir=dump_base_dir,
        )

    # ---- 共通プロパティ ----

    @property
    def config_file_path(self) -> Path:
        return self._config_file_path

    @property
    def project_info(self) -> ProjectInfoConfig:
        return self._snapshot.project_info

    @property
    def logging_config(self) -> LoggingConfig:
        return self._snapshot.logging

    # ---- カタログ / 境界（外部 YAML への参照解決）----

    def get_im_series_catalog_file_path(self) -> Path:
        return self._resolve_required_path(
            override=self._im_series_catalog_file_path,
            yaml_key_path=[
                "series_catalog_for_forward_simulation",
                "im_file_path",
            ],
            error_hint=(
                "IM シリーズカタログ YAML のパスが解決できません。"
                "Config.create(im_series_catalog_file_path=...) で渡すか、"
                "config.yaml の "
                "series_catalog_for_forward_simulation.im_file_path "
                "を設定してください。"
            ),
        )

    def get_cable_series_catalog_file_path(self) -> Path:
        return self._resolve_required_path(
            override=self._cable_series_catalog_file_path,
            yaml_key_path=[
                "series_catalog_for_forward_simulation",
                "cable_file_path",
            ],
            error_hint=(
                "ケーブルシリーズカタログ YAML のパスが解決できません。"
                "Config.create(cable_series_catalog_file_path=...) で渡すか、"
                "config.yaml の "
                "series_catalog_for_forward_simulation.cable_file_path "
                "を設定してください。"
            ),
        )

    def get_im_bounds_and_init_file_path(self) -> Path:
        return self._resolve_required_path(
            override=self._im_bounds_and_init_file_path,
            yaml_key_path=[
                "bounds_and_init_for_estimation_parameters",
                "im_file_path",
            ],
            error_hint=(
                "IM パラメータフィット境界 YAML のパスが解決できません。"
                "Config.create(im_bounds_and_init_file_path=...) で渡すか、"
                "config.yaml の "
                "bounds_and_init_for_estimation_parameters.im_file_path "
                "を設定してください。"
            ),
        )

    def get_cable_bounds_and_init_file_path(self) -> Path:
        return self._resolve_required_path(
            override=self._cable_bounds_and_init_file_path,
            yaml_key_path=[
                "bounds_and_init_for_estimation_parameters",
                "cable_file_path",
            ],
            error_hint=(
                "ケーブルパラメータフィット境界 YAML のパスが解決できません。"
                "Config.create(cable_bounds_and_init_file_path=...) で渡すか、"
                "config.yaml の "
                "bounds_and_init_for_estimation_parameters.cable_file_path "
                "を設定してください。"
            ),
        )

    # ---- dump 系（正規化済み）----

    @property
    def dump_data_config(self) -> DumpDataConfig:
        return self._snapshot.dump_data

    def get_dump_base_dir(self) -> Path:
        if self._dump_base_dir is not None:
            return self._dump_base_dir
        candidate = self._get_node(["dump", "base_dir"])
        if not isinstance(candidate, str) or not candidate.strip():
            raise ValueError(
                "dump.base_dir が設定されていません。"
                "Config.create(dump_base_dir=Path('/abs/path/to/outputs')) で"
                "渡すか、config.yaml の dump.base_dir を設定してください "
                "（同梱パッケージの config.yaml には書き出し先を置きません）。"
            )
        yaml_path = Path(candidate.strip())
        if yaml_path.is_absolute():
            return yaml_path.resolve()
        return (self._config_file_path.parent / yaml_path).resolve()

    # ---- calculation.input 系 ----

    @property
    def input_validation_config(self) -> InputValidationConfig:
        return self._snapshot.input_validation

    # ---- calculation.execute 系 ----

    @property
    def data_processing(self) -> DataProcessingConfig:
        return self._snapshot.data_processing

    @property
    def numerical_guard_config(self) -> NumericalGuardConfig:
        return self._snapshot.numerical_guard

    @property
    def validation_config(self) -> ValidationConfig:
        return self._snapshot.validation

    @property
    def current_estimation_config(self) -> CurrentEstimationConfig:
        return self._snapshot.current_estimation

    @property
    def estimate_params_calculation_config(self) -> EstimateParamsConfig:
        return self._snapshot.estimate_params

    # ---- calculation.output 系 ----

    @property
    def output_figures_config(self) -> OutputFiguresConfig:
        return self._snapshot.output_figures

    # ---- 内部ヘルパー ----

    def _get_node(self, path: list[str]) -> object | None:
        node: object = self._config_data
        for key in path:
            if not isinstance(node, dict):
                return None
            node = node.get(key)
        return node

    def _resolve_yaml_relative_path(
        self,
        key_path: list[str],
    ) -> Path | None:
        raw = self._get_node(key_path)
        if raw is None or not str(raw).strip():
            return None
        return (self._config_file_path.parent / str(raw)).resolve()

    def _resolve_required_path(
        self,
        override: Path | None,
        yaml_key_path: list[str],
        error_hint: str,
    ) -> Path:
        if override is not None:
            return override
        yaml_path = self._resolve_yaml_relative_path(yaml_key_path)
        if yaml_path is None:
            raise ValueError(error_hint)
        return yaml_path
