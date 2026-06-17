"""Application configuration interface (``app_`` = runtime config facade).

モジュール名の ``app_`` は、実行時アプリケーション設定の窓口であることを示し、
汎用語 ``config`` モジュール名との混同を避けるため付与している。

使い方、YAML スキーマ、2 段フォールバック、各メソッド返り値の構造などの
詳細は ``docs/shared/config_and_logger.md`` を参照する。

各セクションの返り値は :mod:`im_cable_system.engine.shared.config.schema`
配下で定義された正規化済み dataclass である。Config 構築（``Config.create``）
時に YAML のスキーマ検証が走り、不正値はその時点で ``ValueError`` として
弾かれる（fail-fast）。利用側は本 IF 越しに attribute アクセスするだけで
よく、schema パッケージを直接 import する必要はない。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

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


class IConfig(ABC):
    """設定のインターフェース（責務 x ステージ単位の公開 API）。

    各メソッドの返り値は :mod:`config.schema` で定義された dataclass。
    YAML キーマッピング・フォールバック仕様は
    ``docs/shared/config_and_logger.md`` を参照する。
    本契約では型と例外条件のみを定義する。
    """

    # ---- ファクトリ ----

    @classmethod
    @abstractmethod
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
        """設定インスタンスを取得するファクトリーメソッド（キーワード専用）。

        Raises:
            ValueError: ``dump_base_dir`` が絶対パスでない場合、または
                ``config.yaml`` のスキーマ検証に失敗した場合（fail-fast）。
        """
        pass

    # ---- 共通プロパティ ----

    @property
    @abstractmethod
    def config_file_path(self) -> Path:
        """設定ファイル（yaml）の絶対パスを返す。"""
        pass

    @property
    @abstractmethod
    def project_info(self) -> ProjectInfoConfig:
        """プロジェクト基本情報。"""
        pass

    @property
    @abstractmethod
    def logging_config(self) -> LoggingConfig:
        """ログ設定。"""
        pass

    # ---- カタログ / 境界（外部 YAML への参照解決）----

    @abstractmethod
    def get_im_series_catalog_file_path(self) -> Path:
        """IM シリーズカタログ YAML のパスを返す。

        Raises:
            ValueError: いずれのフォールバック段でもパスが解決できない場合。
        """
        pass

    @abstractmethod
    def get_cable_series_catalog_file_path(self) -> Path:
        """ケーブルシリーズカタログ YAML のパスを返す。

        Raises:
            ValueError: いずれのフォールバック段でもパスが解決できない場合。
        """
        pass

    @abstractmethod
    def get_im_bounds_and_init_file_path(self) -> Path:
        """IM パラメータフィット境界 YAML のパスを返す。

        Raises:
            ValueError: いずれのフォールバック段でもパスが解決できない場合。
        """
        pass

    @abstractmethod
    def get_cable_bounds_and_init_file_path(self) -> Path:
        """ケーブルパラメータフィット境界 YAML のパスを返す。

        Raises:
            ValueError: いずれのフォールバック段でもパスが解決できない場合。
        """
        pass

    # ---- dump 系（正規化済み）----

    @property
    @abstractmethod
    def dump_data_config(self) -> DumpDataConfig:
        """dump 設定（正規化済み、``base_dir`` を含まない）。"""
        pass

    @abstractmethod
    def get_dump_base_dir(self) -> Path:
        """dump 出力先のベースディレクトリ（絶対パス）を返す。

        Raises:
            ValueError: いずれのフォールバック段でも値が指定されていない場合。
        """
        pass

    # ---- calculation.input 系 ----

    @property
    @abstractmethod
    def input_validation_config(self) -> InputValidationConfig:
        """input ステージの入力 DTO 検証設定。"""
        pass

    # ---- calculation.execute 系 ----

    @property
    @abstractmethod
    def data_processing(self) -> DataProcessingConfig:
        """データ処理設定（並列／逐次の実行戦略）。"""
        pass

    @property
    @abstractmethod
    def numerical_guard_config(self) -> NumericalGuardConfig:
        """近接ゼロ判定などの数値安定化設定。"""
        pass

    @property
    @abstractmethod
    def validation_config(self) -> ValidationConfig:
        """中間 DTO 検証ブロック。"""
        pass

    @property
    @abstractmethod
    def current_estimation_config(self) -> CurrentEstimationConfig:
        """電流反復解法の設定（両モード共通）。"""
        pass

    @property
    @abstractmethod
    def estimate_params_calculation_config(self) -> EstimateParamsConfig:
        """estimate_params 固有のアルゴリズム設定（残差・最適化）。"""
        pass

    # ---- calculation.output 系 ----

    @property
    @abstractmethod
    def output_figures_config(self) -> OutputFiguresConfig:
        """図表示設定（コード側フォールバック補完済み）。"""
        pass
