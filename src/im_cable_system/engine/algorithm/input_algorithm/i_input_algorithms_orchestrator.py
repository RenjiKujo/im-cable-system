"""IM ケーブルシステム Input アルゴリズムの共通オーケストレーター契約。

実行モードごとに異なる入力型・ロード結果型・出力 DTO 型を ``Generic`` で
パラメータ化し、全モードで同じ呼び出し順を契約として共有する。

Generic 型引数（per-mode IF で特殊化される）:

- ``InputT``: ``build_input_dto`` / ``_validate_job_spec`` /
    ``_load_data`` が受け取る入力型。
- ``LoadedDataT``: ``_load_data`` の戻り値型かつ ``_assemble_input_dto``
    の入力型。
- ``InputDtoT``: ``build_input_dto`` の戻り値型（通常は :class:`InputDto`）。

呼び出し順は ``per-mode IF.create`` → ``build_input_dto``。
``build_input_dto`` の内部では ``_validate_job_spec`` → ``_load_data`` →
``_assemble_input_dto`` → ``_validate_input_dto`` の順に実行する。

Note:
    インスタンス生成契約（``create``）はモードごとに必要引数が異なるため
    （Forward は ``reference_axes`` が必要、EstimateParams は不要）、
    本共通 IF には置かず **per-mode IF** に置く。共通 IF が ``create`` を
    持つと、引数を追加した派生 IF が LSP（リスコフ置換）違反になるため。

責務分担:

- ``_validate_job_spec``: ファイルを開く前に確認できる軽量チェック
    （パス存在、必須フィールドの非空など）。
- ``_load_data``: ``LoadedDataT`` を作れない場合のみ raise する
    （ファイルが読めない、ヘッダ欠落、必須キーなどファイル構造の
    破綻、カタログキーが未登録、``float()`` 変換失敗、co-indexed の
    前提が崩れる構造上の不整合など）。値レベル検証（空配列、有限性、
    値域、単位文字列の妥当性など）はここでは行わず、``LoadedDataT``
    自身も ``__post_init__`` を持たない方針。
- ``_assemble_input_dto``: ``InputDtoT`` を作れない場合のみ raise する。
    個々の DTO が単独で判定できる契約は各 DTO の ``__post_init__`` で
    カバーする。フィールド単体の値域（正値、有限性、単位など）に加え、
    1 つの DTO 内で閉じたキー集合の過不足（モデル種別が要求する係数名に
    対する ``params`` の不足・余分など）もここに含む。上流の
    ``_load_data`` は名前の絞り込みを行わず、読み込んだものをそのまま渡す。
- ``_validate_input_dto``: フィールド単体の ``__post_init__`` を超える
    DTO 構造の整合、SI 基本単位整合、cross-field / cross-DTO 整合
    （参照軸長さ、catalog vs candidate の整合など）、物理関係式の整合
    （T·ω と P など）、定格 vs supply 乖離 warning までを担う。
    本ステップは意図的に重く、上流のステップは「構築できるかどうか」に
    集中させる。

per-mode IF は :class:`IInputAlgorithmsOrchestrator` を継承し、Generic
パラメータをモード固有のデータクラスで埋めることで契約を具体化する。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

InputT = TypeVar("InputT")
LoadedDataT = TypeVar("LoadedDataT")
InputDtoT = TypeVar("InputDtoT")


class IInputAlgorithmsOrchestrator(
    Generic[InputT, LoadedDataT, InputDtoT],
    ABC,
):
    """全 Input オーケストレーターが共有する共通契約。

    per-mode IF は本 IF を継承し、Generic 引数を特殊化することで、
    モード固有の入出力型に紐づいた契約として利用できる。インスタンス生成
    （``create``）はモード固有引数を伴うため per-mode IF 側で定義する。
    """

    @abstractmethod
    def build_input_dto(self, input_data: InputT) -> InputDtoT:
        """モード固有の入力データから ``InputDtoT`` を構築する。

        Args:
            input_data: モード固有の入力データ。

        Returns:
            構築・検証済みの ``InputDtoT``。

        Raises:
            ValueError: 検証に失敗した場合。
        """
        pass

    @abstractmethod
    def _validate_job_spec(self, input_data: InputT) -> None:
        """ロード前にジョブ spec のパスや必須フィールドを検証する。

        ``build_input_dto`` の内部から呼び出される。外部から直接呼ぶこと
        は想定しない。

        Args:
            input_data: モード固有の入力データ。

        Raises:
            ValueError: 検証に失敗した場合。
        """
        pass

    @abstractmethod
    def _load_data(self, input_data: InputT) -> LoadedDataT:
        """モード固有のロード処理を走らせ ``LoadedDataT`` を返す。

        ``build_input_dto`` の内部から呼び出される。外部から直接呼ぶこと
        は想定しない。

        ``LoadedDataT`` を作れない場合のみ raise する（ファイル読み取り
        不可、ヘッダ欠落、``float()`` 変換失敗、カタログキー未登録、
        ``LoadedDataT`` データクラスの ``__post_init__`` 違反など）。
        値レベルの契約は ``_assemble_input_dto`` 段の DTO
        ``__post_init__`` または ``_validate_input_dto`` で扱う。

        Args:
            input_data: モード固有の入力データ。

        Returns:
            ロード結果（特殊化された ``LoadedDataT`` 型）。
        """
        pass

    @abstractmethod
    def _assemble_input_dto(self, loaded_data: LoadedDataT) -> InputDtoT:
        """ロード結果から ``InputDtoT`` を組み立てる。

        ``build_input_dto`` の内部から呼び出される。外部から直接呼ぶこと
        は想定しない。

        ``InputDtoT`` を作れない場合のみ raise する。フィールド単体の
        契約（正値・有限性・単位など）と、1 つの DTO 内で閉じたキー集合
        の過不足（モデル係数名の不足・余分など）は各 DTO の
        ``__post_init__`` が担う。cross-field / 物理関係式の整合は
        ``_validate_input_dto`` に委ねる。

        Args:
            loaded_data: :meth:`_load_data` の戻り値。

        Returns:
            組み立てられた ``InputDtoT``。
        """
        pass

    @abstractmethod
    def _validate_input_dto(self, input_dto: InputDtoT) -> None:
        """与えられた ``InputDtoT`` を検証する。

        ``build_input_dto`` の内部から呼び出される。外部から直接呼ぶこと
        は想定しない。

        本ステップは意図的に重く、次を担う。

        - フィールド単体の ``__post_init__`` を超える DTO 契約（必須キー
          の存在、出現規則など）。
        - DTO を横断する SI 基本単位の整合。
        - cross-field / cross-DTO 整合（参照軸長さ、catalog vs candidate
          のシリーズ名整合など）。
        - 物理関係式の整合（T·ω と P など）。
        - 定格 vs supply 乖離 warning。

        Args:
            input_dto: 検証対象 DTO。

        Raises:
            ValueError: 検証に失敗した場合。
        """
        pass
