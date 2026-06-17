"""フィット結果を InputDto へ反映するアセンブラの実装。"""

from __future__ import annotations

import numpy as np

from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.apply_fitted_input.i_fitted_input_assembler import (  # noqa: E501
    IFittedInputAssembler,
)
from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.support.descriptor import (  # noqa: E501
    FittableParamDescriptor,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    CableDto,
)
from im_cable_system.engine.shared.dto.input import (
    InputDto,
)

from .collect_apply_residual import apply_fitted_params


class FittedInputAssembler(IFittedInputAssembler):
    """フィット記述子と試行ベクトルを ``InputDto`` に埋め込む実装。"""

    def __init__(self, config: IConfig, logger: ILogger) -> None:
        """インスタンスを初期化する。"""
        self._config: IConfig = config
        self._logger: ILogger = logger

    @classmethod
    def create(
        cls,
        config: IConfig,
        logger: ILogger,
    ) -> IFittedInputAssembler:
        """config と logger を受け取り、自身のインスタンスを生成する。"""
        return cls(config=config, logger=logger)

    def assemble(
        self,
        input_dto: InputDto,
        descriptors: list[FittableParamDescriptor],
        x: np.ndarray,
        im_count: int,
    ) -> InputDto:
        """記述子とベクトル x を反映した ``InputDto`` を返す。"""
        base_im_series = input_dto.im.im_series
        if base_im_series is None:
            raise ValueError(
                "ImSeriesDto is not embedded in input_dto.im. "
                "Please set ImDto.im_series."
            )
        fitted_im_series, fitted_cable_dto = apply_fitted_params(
            base_im_series,
            input_dto.cable,
            descriptors,
            x,
            im_count,
        )
        new_im_dto = type(input_dto.im)(
            name=input_dto.im.name,
            im_series=fitted_im_series,
        )

        if input_dto.cable is None:
            return InputDto(
                name=input_dto.name,
                array_layout=input_dto.array_layout,
                im=new_im_dto,
                cable=None,
                im_pc_catalogs=input_dto.im_pc_catalogs,
            )

        if fitted_cable_dto is None:
            raise ValueError(
                "ケーブル入力があるのに fitted_cable_dto が None です。"
            )
        fitted_sections = fitted_cable_dto.sections.get_all()
        if len(fitted_sections) != 1:
            raise ValueError(
                "Parameter fit expects exactly one cable section in fitted "
                "result."
            )
        # フィット後のケーブルは元入力と同一シリーズへの差し替えであることを保証する
        # （シリーズ名は元の input_dto.cable から導出する）。
        expected_cable_series_name = self._expected_cable_series_name(
            input_dto.cable
        )
        actual_name = fitted_sections[0].series.name.get_value()
        if (
            expected_cable_series_name is not None
            and actual_name != expected_cable_series_name
        ):
            raise ValueError(
                "Cable series name mismatch for replacement: "
                f"expected={expected_cable_series_name}, "
                f"actual={actual_name}"
            )
        return InputDto(
            name=input_dto.name,
            array_layout=input_dto.array_layout,
            im=new_im_dto,
            cable=fitted_cable_dto,
            im_pc_catalogs=input_dto.im_pc_catalogs,
        )

    @staticmethod
    def _expected_cable_series_name(cable_dto: CableDto) -> str | None:
        """元入力ケーブルから照合用シリーズ名を取り出す。

        Returns:
            先頭セクションのシリーズ名。セクションまたはシリーズが無い場合は
            None（照合をスキップする）。
        """
        sections = cable_dto.sections.get_all()
        if not sections or sections[0].series is None:
            return None
        return sections[0].series.name.get_value()
