"""全体実行オーケストレーターの親インターフェース。

このモジュールは、どのシミュレーションでも共通となる
「1 本の InputDto を受け取り、1 本の ItmDto を返す」という最小契約を定義します。
内部でどのコンポーネントをどの順で呼ぶか（build_model → simulate →
validate_itm_dto を自前で踏むか、フィットを挟んでから forward に委譲するか等）は
実装側・サブインターフェースの責務とし、本 IF では規定しません。
execute_algorithm/__init__.py からは再エクスポートしない（責務記載のみの方針）。
層外（processor 等）からは ``execute_algorithm.orchestrate`` の公開窓口を使う。
同一 execute_algorithm ツリー内の I/F 定義モジュールとして、orchestrate サブパッケージから参照してよい。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from im_cable_system.engine.shared.config import IConfig, ILogger

InputDtoT = TypeVar("InputDtoT")
ItmDtoT = TypeVar("ItmDtoT")


class IExecuteAlgorithmsOrchestrator(Generic[InputDtoT, ItmDtoT], ABC):
    """全体実行オーケストレーターの共通インターフェース。

    入出力: 単一の InputDto を受け取り、単一の ItmDto を返す（execute(input_dto) -> ItmDto）。
    1 本の InputDto から 1 本の ItmDto を生成する計算を統括する責務だけを契約する。
    内部でどのコンポーネント（build_model / simulate / validate_itm_dto 等）を
    どの順で呼ぶかは実装の詳細であり、本 IF では規定しない。

    メソッドの並び（呼び出し順）: create(config, logger, ...) → execute。
    create は config と logger を必ず受け取る。
    それ以外の引数はサブクラスで追加する（例: im_series_dtos, cable_series_dtos）。

    Note:
        **設計ポリシー: 契約は execute（入口）に限定する**

        本 IF はあえて「外から呼べる入口」である ``execute`` のみを契約とする。
        forward（Direct / Iteration）のように
        ``build_model → simulate → validate_itm_dto`` の手順を自前で踏む実装も、
        パラメータ推定のようにフィットを挟んでから forward に委譲する実装も、
        同じ「InputDto → ItmDto」という最上位契約の下に並べられるようにするため。

        「execute が何を順に呼ぶか」という実行手順そのものを型で固定したいのは
        forward 系に固有の要求であり、その契約
        （``_build_model`` / ``_simulate`` / ``_validate_itm_dto``）は
        :class:`IForwardExecutionOrchestrator` 側に置く。本 IF にそれらを置くと、
        手順を持たない実装（パラメータ推定）が空実装を強いられ、契約と実装が
        食い違うため、最上位は ``execute`` のみに絞る。

        **設計ポリシー: Generic 化は将来拡張のための保険**

        現状の継承先（``IForwardExecutionOrchestrator`` /
        ``IEstimateParamsExecutionOrchestrator``）はいずれも
        ``IExecuteAlgorithmsOrchestrator[InputDto, ItmDto]`` を具体化しており、
        ``InputDtoT`` / ``ItmDtoT`` の Generic としての表現力を現時点で
        活用しているわけではない。

        それでも Generic 化を維持しているのは、将来別 DTO 型を扱う実行モード
        （例: 別系統の入力 DTO / 別形式の中間 DTO）が追加された場合に、
        本 IF を継承しつつ型をすげ替えられる拡張余地を残しておくため。
        現状の継承先だけを見ると Generic は冗長だが、共通 IF の責務を
        「あらゆる実行モードの最上位契約」と位置づける以上の保険として
        意図的に残している。
    """

    @classmethod
    @abstractmethod
    def create(
        cls,
        config: IConfig,
        logger: ILogger,
    ) -> IExecuteAlgorithmsOrchestrator[InputDtoT, ItmDtoT]:
        """config と logger を受け取り、自身のインスタンスを生成する。

        サブクラスでは第3引数以降を追加してよい（例: im_series_dtos, cable_series_dtos）。

        Args:
            config: 設定オブジェクト。
            logger: ロガーオブジェクト。

        Returns:
            IExecuteAlgorithmsOrchestrator[InputDtoT, ItmDtoT]: 生成されたオーケストレーター。
        """
        pass

    @abstractmethod
    def execute(self, input_dto: InputDtoT) -> ItmDtoT:
        """1 本の InputDto を処理し、1 本の ItmDto を返す。

        InputDto から ItmDto を生成する計算全体を統括する。具体的な手順
        （モデル構築・シミュレーション・検証の有無や順序、フィットの有無）は
        実装の責務であり、本契約では規定しない。

        Args:
            input_dto: 単一の入力 DTO。

        Returns:
            ItmDtoT: 処理を完了した単一の中間 DTO。
        """
        pass
