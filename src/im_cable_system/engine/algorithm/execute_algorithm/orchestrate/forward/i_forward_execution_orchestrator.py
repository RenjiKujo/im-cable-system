"""IM ケーブルシステム forward 実行オーケストレーターのインターフェース。

スリップが入力に含まれる順方向計算（forward）の契約を定義する。
親 IExecuteAlgorithmsOrchestrator（``execute`` のみを契約）を継承し、
forward 固有の実行手順（``_build_model`` / ``_simulate`` /
``_validate_itm_dto``）と、検証を省いた正規ルート
（``execute_without_validation``）を本 IF で契約化する。
IM / ケーブルのシリーズ詳細は InputDto に埋め込まれる前提とする。
"""

from __future__ import annotations

from abc import abstractmethod

from im_cable_system.engine.algorithm.execute_algorithm.i_execute_algorithms_orchestrator import (  # noqa: E501
    IExecuteAlgorithmsOrchestrator,
)
from im_cable_system.engine.shared.dto.input import (
    InputDto,
)
from im_cable_system.engine.shared.dto.itm import (
    ItmDto,
)


class IForwardExecutionOrchestrator(
    IExecuteAlgorithmsOrchestrator[InputDto, ItmDto]
):
    """IM ケーブルシステム forward 実行オーケストレーターのインターフェース。

    親（``create`` / ``execute``）に加え、本 IF は forward 実行の手順そのものを
    契約として固定する。すなわち ``execute`` が内部で
    ``_build_model → _simulate → _validate_itm_dto`` をこの順で呼ぶことを
    ``@abstractmethod`` として明示し、さらに ``execute_without_validation``
    （build_model とフル simulate まで行い ``_validate_itm_dto`` は呼ばない
    正規ルート）を定義する。

    設計メモ（実行手順を IF レベルで握る）:
        一般的な IF 設計では「外から呼べる public メソッドだけ」を契約とし、
        private は具象実装に閉じる。本 IF はこの一般則に反して
        ``_build_model`` / ``_simulate`` / ``_validate_itm_dto`` まで
        ``@abstractmethod`` として明示する。意図は「execute が何を順に呼ぶか」
        までを forward の契約として固定し、どの forward 具象実装
        （Direct / Iteration）でも
        ``build_model → simulate → validate_itm_dto`` という実行手順が
        崩れないことを型レベルで担保することにある。
        本プロジェクトのドメイン上、この手順を踏み外した forward 実装は
        許容できないため、IF を「処理の入口」ではなく
        「実行手順そのもの」として握る。
        手順を持たない実行モード（パラメータ推定）はこの契約を負わないよう、
        親 ``IExecuteAlgorithmsOrchestrator`` 側は ``execute`` のみに絞っている。

    設計メモ（``execute_without_validation`` を IF に置く理由）:
        ``EstimateParams`` のパラメータ推定ループ
        （``scipy.optimize.least_squares`` の残差評価）では、同一 forward を
        高頻度に呼び出すため、毎回 ``_validate_itm_dto`` まで実行すると
        計算コストが過大になる。一方で呼び出し側は Direct / Iteration を
        意識せず IF 越しに forward を扱うため、IF として「検証を省いた
        正規ルート」を契約化しておかないと、呼び出し側は private メソッド
        （``_build_model`` / ``_simulate``）を直接叩く規約違反に陥る。
        Direct 実装では中身が薄くなる（build + simulate の2 行）が、
        Iteration 実装では「電流反復後にフル simulate」という非自明な責務を
        まとめる単位になる。両実装で同じ契約を提供する利点を優先し、
        IF の対称性を保つ。

    Note:
        BuildModel は反復時もフル実行する。イミタンスがスリップ・電流に依存するため、
        ItmDto の「変わらない部分だけ保持」で計算時間はあまり削減できない。
    """

    @abstractmethod
    def execute_without_validation(self, input_dto: InputDto) -> ItmDto:
        """1本の InputDto に対して build_model とフル simulate まで実行する。

        ``execute`` と同様に電力・特性値まで計算するが、
        ``_validate_itm_dto`` は呼ばない。パラメータ推定の残差評価のように
        同一入力に対する試行を高頻度で繰り返す場合に用いる
        （契約として IF に置く理由はクラス docstring「設計メモ」参照）。

        Args:
            input_dto: 単一の入力 DTO。

        Returns:
            ItmDto: モデル構築とフルシミュレーション済みの中間 DTO。
                ``simulation_result`` に voltage_current / power / characteristic が
                設定される想定（Direct は1回の build+simulate、Iteration は
                電流反復後にフル simulate 1回）。
        """
        pass

    @abstractmethod
    def _build_model(self, input_dto: InputDto) -> ItmDto:
        """単一の入力 DTO から物理モデルを構築し、中間 DTO（simulation_result は未設定）を返す。

        execute が内部で呼ぶ。外部からは直接呼ばない想定。

        Args:
            input_dto: 単一の入力 DTO。

        Returns:
            ItmDto: モデル構築済みの単一の中間 DTO。
        """
        pass

    @abstractmethod
    def _simulate(self, itm_dto: ItmDto) -> ItmDto:
        """単一の中間 DTO に対してシミュレーションを実行し、結果を付与した中間 DTO を返す。

        execute が内部で呼ぶ。外部からは直接呼ばない想定。

        Args:
            itm_dto: モデル構築済みの単一の中間 DTO。

        Returns:
            ItmDto: シミュレーション結果が付与された単一の中間 DTO。
        """
        pass

    @abstractmethod
    def _validate_itm_dto(self, itm_dto: ItmDto) -> None:
        """単一の中間 DTO の妥当性を検証する。

        execute が内部で呼ぶ。外部からは直接呼ばない想定。

        Args:
            itm_dto: 検証対象の単一の中間 DTO。

        Raises:
            ValueError: 検証に失敗した場合。
        """
        pass
