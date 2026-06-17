"""IMケーブルモデル構築オーケストレーターのインターフェース定義。

このモジュールは、IMケーブルモデル構築処理を統括するオーケストレーターの
インターフェースを定義します。オーケストレーターの IF は、実装（および公開窓口）
が置かれる ``orchestrate`` サブパッケージの **親 Dir（build_model 直下）** に
配置する。

設計方針（execute_algorithm の最上位 IF と形態を揃える）:
    - ``create(config, logger)`` と公開実行メソッド ``build(input_dto)`` の
      2 メソッド構成とする。ビルダーの組み立ては ``build`` 内部の private 処理に
      閉じ、構成インスタンスを跨いで保持・再利用しない。
    - ``InputDto`` はインスタンス属性に保持せず、``build`` および各 private へ
      引数で渡す（再入・並列実行に安全）。
    - ``_build_im_model`` / ``_build_cable_model`` / ``_build_system_model``
      を ``@abstractmethod`` として明示し、「build が何を順に呼ぶか」を
      IF の契約として固定する（:class:`IExecuteAlgorithmsOrchestrator` と
      同じ「実行手順そのものを IF で握る」ポリシー）。
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ArrayLayoutDto,
)
from im_cable_system.engine.shared.dto.input import (
    InputDto,
)
from im_cable_system.engine.shared.dto.itm import (
    ItmCableModelDto,
    ItmImModelDto,
    ItmModelDto,
    ItmSystemModelDto,
)


class IImCableModelBuildOrchestrator(ABC):
    """IMケーブルモデル構築オーケストレーターのインターフェース。

    単一の ``InputDto`` を受け取り、単一の ``ItmModelDto`` を返す
    （``build(input_dto) -> ItmModelDto``）。``build`` は内部で
    ``_build_im_model → _build_cable_model → _build_system_model`` を
    この順に呼び、統合モデル DTO を構築する。
    各段の private には ``input_dto`` を明示的に渡す（インスタンス状態に載せない）。

    メソッドの並び（呼び出し順）: ``create(config, logger)`` → ``build``。
    """

    @classmethod
    @abstractmethod
    def create(
        cls,
        config: IConfig,
        logger: ILogger,
    ) -> IImCableModelBuildOrchestrator:
        """config と logger を受け取り、自身のインスタンスを生成する。

        Args:
            config: 設定オブジェクト。
            logger: ロガーオブジェクト。

        Returns:
            IImCableModelBuildOrchestrator: 生成されたオーケストレーター。
        """

    @abstractmethod
    def build(self, input_dto: InputDto) -> ItmModelDto:
        """単一の入力 DTO から IM→Cable→System の順でモデルを構築する。

        ``_build_im_model → _build_cable_model → _build_system_model`` を
        この順に実行し、各 private メソッド内で必要なビルダーを生成して
        統合モデル DTO を構築する。

        Args:
            input_dto: 入力 DTO。ビルダータイプの決定にも使用される。

        Returns:
            ItmModelDto: 構築されたモデル DTO。

        Raises:
            ValueError: ``input_dto.im.im_series`` が未設定の場合、または
                ビルドに失敗した場合。

        Note:
            下位ビルダー経由のドメイン計算では
            ``config.numerical_guard_config.eps`` と ``max_mag = 1 / eps`` を
            明示的に渡すこと（:class:`ISystemModelBuilder` 等と同方針）。
        """

    @abstractmethod
    def _build_im_model(
        self,
        input_dto: InputDto,
        model_array_layout: ArrayLayoutDto,
    ) -> ItmImModelDto:
        """IMモデルを構築する。

        build が内部で呼ぶ。外部からは直接呼ばない想定。

        Args:
            input_dto: 入力 DTO（IM 系列・ImDto を参照）。
            model_array_layout: 配列レイアウト DTO。

        Returns:
            ItmImModelDto: 構築された IM モデル DTO。

        Raises:
            ValueError: ``input_dto.im.im_series`` が未設定の場合。
        """

    @abstractmethod
    def _build_cable_model(
        self,
        input_dto: InputDto,
        model_array_layout: ArrayLayoutDto,
    ) -> ItmCableModelDto:
        """ケーブルモデルを構築する。

        build が内部で呼ぶ。外部からは直接呼ばない想定。

        Args:
            input_dto: 入力 DTO（ケーブル DTO を参照）。
            model_array_layout: 配列レイアウト DTO。

        Returns:
            ItmCableModelDto: 構築されたケーブルモデル DTO。
        """

    @abstractmethod
    def _build_system_model(
        self,
        itm_im_model_dto: ItmImModelDto,
        itm_cable_model_dto: ItmCableModelDto,
    ) -> ItmSystemModelDto:
        """システムモデルを構築する。

        build が内部で呼ぶ。外部からは直接呼ばない想定。

        Args:
            itm_im_model_dto: IM モデル DTO。
            itm_cable_model_dto: ケーブルモデル DTO。

        Returns:
            ItmSystemModelDto: 構築されたシステムモデル DTO。
        """
