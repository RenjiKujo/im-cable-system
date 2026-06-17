"""IM ケーブルシステム Input 用・InputDto 組み立ての基底インターフェース。

カタログ等のファイル I/O はロード段階（:class:`IInputDataLoader`）で完結させ、
本契約の :meth:`assemble` は ``loaded_data`` のみで組み立てを行う。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from im_cable_system.engine.shared.dto.input import InputDto

LoadedDataForAssembleT = TypeVar("LoadedDataForAssembleT")


class IInputDtoAssembler(
    ABC,
    Generic[LoadedDataForAssembleT],
):
    """ロード結果から :class:`InputDto` を組み立てる契約。

    本 IF が抽象として要求するのは :meth:`assemble` のみ。
    :meth:`assemble` は ``loaded_data`` 1 件を入力に、:class:`InputDto`
    を 1 件返す。直積展開（複数 ``LoadedData`` から複数 ``InputDto`` を
    作る）が必要なケースの繰り返しはオーケストレータ層の責務であり、
    本 IF・具象アセンブラは常に「1 件 → 1 件」の単純契約を保つ
    （``orchestrate/estimate_params/estimate_params_input_orchestrator``
    の設計方針 docstring を参照）。
    カタログ YAML 等のファイル I/O はロード段階（:class:`IInputDataLoader`）
    で完結している前提。

    インスタンス生成（``create``）は IF の抽象に**含めない**:
        設計原則（インターフェース駆動・生成の分離）では
        「インスタンス生成はファクトリメソッドを通じて行う」ことを求めているが、
        ファクトリのシグネチャまでは IF レベルで揃えない方針とする。
        理由は以下:

        1. 具象ごとに **生成時に必要な情報が異なる**。例えば
           :class:`ForwardInputDtoAssembler` は ``reference_axes``（モードごと
           に異なる参照軸の並び）を生成時に受け取るが、
           :class:`EstimateParamsAssembler` は受け取らない。生成シグネチャを
           IF で揃えると、Forward 側に「形だけ揃えるためのデフォルト
           ``create()``」が生まれてしまい、嘘契約になる。
        2. ``create()`` は通常**具象クラス名から直接呼ばれる**（例:
           ``ForwardInputDtoAssembler.create(...)``）。orchestrate 層が IF
           として保持するのは生成済みインスタンスであり、生成自体を IF
           越しにポリモーフィックに呼ぶユースケースが現状ない。
        3. 結果として、ポリモーフィックに揃えるべきは ``assemble()`` だけ
           で十分である。

    具象クラスでの実装ガイドライン:
        - **必ず ``create()`` クラスメソッドを実装すること**
          （ファクトリメソッド経由でのみインスタンス生成を行う、という
          生成分離の原則を満たすため）。
        - ``create()`` のシグネチャは具象ごとに自由に定めてよい
          （例: Forward は ``reference_axes`` を受け取る、EstimateParams は
          受け取らない）。
        - 直接 ``__init__`` でのインスタンス生成は避け、必ず ``create()``
          を経由する。

    型パラメータ:
        - ``LoadedDataForAssembleT``: 具象が消費するロード結果型
          （例: ``ForwardInputLoadedData`` / ``EstimateParamsInputLoadedData``）。
          ``loaded_data`` の型はモードごとに異なるため Generic で切り出す。
          一方、組み立て結果は IF レベルで :class:`InputDto` に固定する
          （複数件をまとめた :class:`InputDtos` を返す具象は本 IF の対象外。
          複数件処理はオーケストレータ側の責務）。
    """

    @abstractmethod
    def assemble(
        self,
        loaded_data: LoadedDataForAssembleT,
    ) -> InputDto:
        """1 件のロード結果から 1 件の :class:`InputDto` を組み立てる。

        Args:
            loaded_data: :meth:`IInputDataLoader.load` の戻り値の 1 件分
                に相当。カタログ解決済みの DTO 群を含む想定。

        Returns:
            InputDto: 組み立て結果。各 DTO の ``__post_init__`` レベルの
                最小契約（型・必須キー・finite・enum 値など）は満たすが、
                SI 基本単位整合・cross-field 制約・参照軸直積点数といった
                組み立て後でないと判定できない契約は :mod:`...validate_input_dto`
                段に委ねる。複数件をまとめた :class:`InputDtos` を返す契約
                は本 IF の対象外（複数件処理はオーケストレータの責務）。

        Raises:
            ValueError: サポート外の入力の場合。
        """
        raise NotImplementedError
