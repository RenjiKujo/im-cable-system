"""Application logger interface (``app_`` = runtime log output facade).

モジュール名の ``app_`` は、実行時アプリケーションのログ出力窓口であることを示し、
汎用語 ``logger`` や stdlib ``logging`` との混同を避けるため付与している。

設計方針:
    :class:`ILogger` は :class:`IConfig` の検証済みスナップショットを
    受け取って構成する。YAML 解釈ルートを Config に一本化するためで、
    Logger 側で改めて YAML を読み直すことはしない（fail-fast の一貫性）。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from im_cable_system.engine.shared.config.i_app_config import IConfig


class ILogger(ABC):
    """ログ出力のインターフェイス。

    :class:`IConfig` と同様、ファクトリーメソッドによるインスタンス生成の
    契約を定義する。標準ライブラリ ``logging`` には依存しない。
    """

    @classmethod
    @abstractmethod
    def create(cls, config: IConfig) -> ILogger:
        """ログ出力インスタンスを取得するファクトリーメソッド。

        Args:
            config: 構成済みの :class:`IConfig`。``logging`` セクションは
                :class:`IConfig.create` 時点でスキーマ検証済みである。

        Returns:
            ILogger: 構成済みログ出力インスタンス。
        """

    @property
    @abstractmethod
    def config_file_path(self) -> Path:
        """構成時に用いた設定ファイルのパスを返す。

        Returns:
            Path: 設定ファイル（yaml）のパス。
        """

    @abstractmethod
    def info(self, msg: str, *args: object) -> None:
        """INFO レベルでログを出力する。

        Args:
            msg: メッセージ。
            *args: メッセージに渡す追加引数。
        """

    @abstractmethod
    def warning(self, msg: str, *args: object) -> None:
        """WARNING レベルでログを出力する。

        Args:
            msg: メッセージ。
            *args: メッセージに渡す追加引数。
        """

    @abstractmethod
    def error(self, msg: str, *args: object) -> None:
        """ERROR レベルでログを出力する。

        Args:
            msg: メッセージ。
            *args: メッセージに渡す追加引数。
        """

    @abstractmethod
    def exception(self, msg: str, *args: object) -> None:
        """ERROR レベルでスタックトレース付きログを出力する。

        ``except`` 句の中から呼ぶことを想定する。現在処理中の例外の
        スタックトレースが ``msg`` の後に自動的に付与される。Runner 等
        最上位境界での「想定外エラーの最終報告」用。

        Args:
            msg: メッセージ。
            *args: メッセージに渡す追加引数。
        """
