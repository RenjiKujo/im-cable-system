"""IM ケーブルシステム forward 実行オーケストレーター用ファクトリー。

入力条件に応じて、Direct（電流依存なし）または Iteration（電流依存あり）の
実装を選択する。電流依存は IM の二次・一次・励磁モデルおよびケーブルの導体モデルが対象。

選択ルールはシンプルで、**判定対象のモデルのうち電流依存モデルが
1 つでも含まれていれば Iteration、すべて電流非依存なら Direct** を返す。
具体的には、IM の一次・二次・励磁モデル、およびケーブルの導体モデルの
いずれか 1 つでも電流依存型であれば Iteration が選ばれる。

Note:
    本ファクトリーの責務はあくまで「どの実装クラスを用いるかを判定し、
    そのインスタンスを生成して返す」ことに限定する。

    「IM／ケーブルが電流依存モデルを含むか」というドメイン判定そのものは
    :mod:`im_cable_system.engine.domain.predicate` の述語に委譲し、本モジュール
    は「電流依存モデルが 1 つでもあれば Iteration」という
    forward 実行の実行パス選択ルールだけを担う。
"""

from __future__ import annotations

from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.forward.direct_forward_execution_orchestrator import (  # noqa: E501
    DirectForwardExecutionOrchestrator,
)
from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.forward.i_forward_execution_orchestrator import (  # noqa: E501
    IForwardExecutionOrchestrator,
)
from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.forward.iteration_forward_execution_orchestrator import (  # noqa: E501
    IterationForwardExecutionOrchestrator,
)
from im_cable_system.engine.domain.predicate import (
    has_current_dependent_conductor_model,
    has_current_dependent_immittance_model,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    CableDto,
    ImDto,
)


class ForwardExecutionOrchestratorFactory:
    """forward 用 ``IForwardExecutionOrchestrator`` の生成を担当するファクトリー。"""

    @staticmethod
    def create(
        config: IConfig,
        logger: ILogger,
        im_dto: ImDto,
        cable: CableDto | None,
    ) -> IForwardExecutionOrchestrator:
        """ImDto / CableDto から forward 実装を選択して生成する。

        分岐ルール:
            判定対象（IM の一次・二次・励磁モデル、ケーブルの導体モデル）のうち、
            **電流依存モデルが 1 つでも含まれていれば**
            :class:`IterationForwardExecutionOrchestrator` を返す。
            すべてが電流非依存である場合のみ
            :class:`DirectForwardExecutionOrchestrator` を返す。
            ``cable`` が ``None`` の場合（ケーブル無し）はケーブル側の判定対象から外し、
            IM 側の判定結果のみで分岐する。

        設計原則（ファクトリ引数設計）上は「分岐軸だけ（列挙値リスト）を引数に取る」
        ことが第1優先だが、
        本ファクトリーでは以下の理由から第2優先（DTO から分岐条件を導出する）を採用する。

        - IM の一次・励磁・二次モデルとケーブル導体モデルの電流依存判定ロジックが、
          forward 実装やパラメータ推定オーケストレーターなど
          複数箇所で重複しやすいため。
        - DTO 側からモデルタイプを取り出す処理を本ファクトリーに集約することで、
          「どの実装クラスを返すか」の判定ロジックを 1 箇所に閉じ込め、
          テスト容易性と保守性を高めるため。

        そのため、呼び出し側は ImDto / CableDto を渡すだけでよく、
        circuit_model_type_list / cable_conductor_model_type_list の構築は
        本ファクトリー内部の責務とする。

        Args:
            config: 設定オブジェクト。
            logger: ロガーオブジェクト。
            im_dto: 入力の :class:`ImDto`（``im_series`` が埋め込まれている前提）。
            cable: 入力のケーブル DTO。None の場合（ケーブル無し）は電流依存無し扱い。

        Returns:
            IForwardExecutionOrchestrator: 生成されたオーケストレーター。

        Raises:
            ValueError: ``im_dto.im_series`` が埋め込まれていない場合。
        """
        if im_dto.im_series is None:
            raise ValueError(
                "ImSeriesDto is not embedded in im_dto. "
                "Please set ImDto.im_series."
            )
        if has_current_dependent_immittance_model(im_dto=im_dto) or (
            cable is not None
            and has_current_dependent_conductor_model(cable_dto=cable)
        ):
            return IterationForwardExecutionOrchestrator.create(
                config=config,
                logger=logger,
            )
        return DirectForwardExecutionOrchestrator.create(
            config=config,
            logger=logger,
        )
