"""IM ケーブルシステム Input 用・データローダーの基底インターフェース。

4 段フロー（``_validate_job_spec`` → ``_load_data`` →
``_assemble_input_dto`` → ``_validate_input_dto``）の 2 段目
``_load_data`` で使われる契約。具象クラスはファクトリ :meth:`create` で
インスタンスを生成し、:meth:`load` にモード固有の入力（job spec 等）を
渡してパース済みデータ（``LoadedDataT``）を返す。

Generic 型引数（モード別ローダーで具体化する）:

- ``InputT``: ``load`` の引数型（モード別の入力 = job spec 等）。
- ``LoadedDataT``: ``load`` の戻り値型（モード別のロード結果データクラス）。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from im_cable_system.engine.shared.config import IConfig, ILogger

InputT = TypeVar("InputT")
LoadedDataT = TypeVar("LoadedDataT")


class IInputDataLoader(ABC, Generic[InputT, LoadedDataT]):
    """ファイル等からロード結果を返すローダーの共通インターフェース。

    raise する条件は ``LoadedDataT`` を作れないケースに限る。値レベルの
    契約（正値・有限性・単位文字列の妥当性など）は ``_assemble_input_dto``
    段の DTO ``__post_init__`` または ``_validate_input_dto`` に寄せる。
    ``LoadedDataT`` 自身も ``__post_init__`` を持たない方針。
    """

    @classmethod
    @abstractmethod
    def create(
        cls,
        config: IConfig,
        logger: ILogger,
    ) -> IInputDataLoader[InputT, LoadedDataT]:
        """ローダーインスタンスを生成する。

        Args:
            config: 設定（例: シリーズカタログ YAML のパス解決）。
            logger: ロガー。

        Returns:
            IInputDataLoader: 生成されたローダー。
        """
        raise NotImplementedError

    @abstractmethod
    def load(self, input_data: InputT) -> LoadedDataT:
        """データを読み込み、ロード結果を返す。

        raise する条件は ``LoadedDataT`` を作れないケースに限る
        （ファイル読み取り不可、ヘッダ欠落、必須キーなどファイル構造の
        破綻、カタログキー未登録、``float()`` 変換失敗、co-indexed の
        前提が崩れる構造的不整合など）。

        Args:
            input_data: モード固有の入力（job spec 等。パス束を含む）。

        Returns:
            LoadedDataT: パース済みデータ。

        Raises:
            ValueError: 入力ファイルの形式・スキーマが不正な場合。
            OSError: ファイルが開けない場合（``FileNotFoundError`` も含む）。
        """
        raise NotImplementedError
