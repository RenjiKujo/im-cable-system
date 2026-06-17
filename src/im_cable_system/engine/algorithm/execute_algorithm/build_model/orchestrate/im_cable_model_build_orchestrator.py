"""IMケーブルモデル構築オーケストレーターの実装。

このモジュールは、IMケーブルモデル構築処理を統括するオーケストレーターの
実装を提供します。
"""

from __future__ import annotations

from im_cable_system.engine.algorithm.execute_algorithm.build_model.build_cable_model import (  # noqa: E501
    PieCableModelBuilder,
)
from im_cable_system.engine.algorithm.execute_algorithm.build_model.build_im_model import (  # noqa: E501
    ImModelBuilderFactory,
)
from im_cable_system.engine.algorithm.execute_algorithm.build_model.build_system_model import (  # noqa: E501
    ImPieCableSystemModelBuilder,
)
from im_cable_system.engine.algorithm.execute_algorithm.build_model.i_im_cable_model_build_orchestrator import (  # noqa: E501
    IImCableModelBuildOrchestrator,
)
from im_cable_system.engine.shared.config import IConfig, ILogger, timer
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


class ImCableModelBuildOrchestrator(IImCableModelBuildOrchestrator):
    """IMケーブルモデル構築オーケストレーターの実装。

    IMケーブルモデル構築処理を統括するオーケストレーターの実装です。
    """

    def __init__(
        self,
        config: IConfig,
        logger: ILogger,
    ) -> None:
        """IMケーブルモデル構築オーケストレーターのインスタンスを初期化する。

        Args:
            config: 設定オブジェクト。
            logger: ロガーオブジェクト。
        """
        self._config: IConfig = config
        self._logger: ILogger = logger

    @classmethod
    def create(
        cls,
        config: IConfig,
        logger: ILogger,
    ) -> IImCableModelBuildOrchestrator:
        """IMケーブルモデル構築オーケストレーターのインスタンスを生成する。

        Args:
            config: 設定オブジェクト。
            logger: ロガーオブジェクト。

        Returns:
            IImCableModelBuildOrchestrator: 生成されたオーケストレーターインスタンス。
        """
        return cls(config=config, logger=logger)

    @timer(logger=None, line="#", min_duration=0.01)
    def build(self, input_dto: InputDto) -> ItmModelDto:
        """単一の入力 DTO から IM→Cable→System の順でモデルを構築する。

        実行順序（固定）:
            1. IM モデル構築
            2. ケーブルモデル構築
            3. システムモデル構築
            4. 統合モデル DTO の構築

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
            明示的に渡す（:class:`ISystemModelBuilder` 等と同方針）。
        """
        # ArrayLayoutDtoを直接使用（InputDto.array_layout をそのまま使用）
        model_array_layout = input_dto.array_layout

        itm_im_model_dto = self._build_im_model(
            input_dto=input_dto,
            model_array_layout=model_array_layout,
        )
        itm_cable_model_dto = self._build_cable_model(
            input_dto=input_dto,
            model_array_layout=model_array_layout,
        )
        itm_system_model_dto = self._build_system_model(
            itm_im_model_dto=itm_im_model_dto,
            itm_cable_model_dto=itm_cable_model_dto,
        )
        return self._build_output(
            input_dto=input_dto,
            model_array_layout=model_array_layout,
            itm_im_model_dto=itm_im_model_dto,
            itm_cable_model_dto=itm_cable_model_dto,
            itm_system_model_dto=itm_system_model_dto,
        )

    def _build_im_model(
        self,
        input_dto: InputDto,
        model_array_layout: ArrayLayoutDto,
    ) -> ItmImModelDto:
        """IMモデルを構築する。"""
        im_series_dto = input_dto.im.im_series
        if im_series_dto is None:
            raise ValueError(
                "ImSeriesDto is not embedded in input_dto.im. "
                "Please set ImDto.im_series."
            )

        builder = ImModelBuilderFactory.create(
            cage_multiplicity=im_series_dto.cage_multiplicity,
            config=self._config,
            logger=self._logger,
        )
        return builder.build(
            im_dto=input_dto.im,
            model_array_layout=model_array_layout,
        )

    def _build_cable_model(
        self,
        input_dto: InputDto,
        model_array_layout: ArrayLayoutDto,
    ) -> ItmCableModelDto:
        """ケーブルモデルを構築する。"""
        builder = PieCableModelBuilder.create(
            config=self._config,
            logger=self._logger,
        )
        return builder.build(
            cable_dto=input_dto.cable,
            model_array_layout=model_array_layout,
        )

    def _build_system_model(
        self,
        itm_im_model_dto: ItmImModelDto,
        itm_cable_model_dto: ItmCableModelDto,
    ) -> ItmSystemModelDto:
        """システムモデルを構築する。"""
        builder = ImPieCableSystemModelBuilder.create(
            config=self._config,
            logger=self._logger,
        )
        return builder.build(
            itm_im_model_dto=itm_im_model_dto,
            itm_cable_model_dto=itm_cable_model_dto,
        )

    def _build_output(
        self,
        input_dto: InputDto,
        model_array_layout: ArrayLayoutDto,
        itm_im_model_dto: ItmImModelDto,
        itm_cable_model_dto: ItmCableModelDto,
        itm_system_model_dto: ItmSystemModelDto,
    ) -> ItmModelDto:
        """統合モデルDTOを構築する。"""
        catalogs = input_dto.im_pc_catalogs
        return ItmModelDto(
            array_layout=model_array_layout,
            im=itm_im_model_dto,
            cable=itm_cable_model_dto,
            system=itm_system_model_dto,
            im_pc_catalogs=catalogs,
        )
