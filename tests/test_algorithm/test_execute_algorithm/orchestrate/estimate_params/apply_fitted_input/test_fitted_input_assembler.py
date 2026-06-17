"""FittedInputAssembler の単体テスト。"""

from __future__ import annotations

import numpy as np

from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.apply_fitted_input import (  # noqa: E501
    FittedInputAssembler,
    IFittedInputAssembler,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.input import InputDto, InputDtos


def _first_input_without_cable(inputs: InputDtos) -> InputDto:
    """ケーブル無しの InputDto を 1 件返す。"""
    for dto in inputs.get_all():
        if dto.cable is None:
            return dto
    raise AssertionError("ケーブル無しの InputDto が見つかりません。")


def _first_input_with_single_section_cable(inputs: InputDtos) -> InputDto:
    """1 セクションのケーブルを持つ InputDto を 1 件返す。"""
    for dto in inputs.get_all():
        if dto.cable is not None and len(dto.cable.sections.get_all()) == 1:
            return dto
    raise AssertionError(
        "1 セクションのケーブルを持つ InputDto が見つかりません。"
    )


class TestFittedInputAssembler:
    """フィット結果反映アセンブラの生成と契約を確認する。"""

    def test_create_returns_interface(
        self,
        config: IConfig,
        logger: ILogger,
    ) -> None:
        """create がインターフェース型を返す。"""
        assembler = FittedInputAssembler.create(config=config, logger=logger)
        assert isinstance(assembler, IFittedInputAssembler)

    def test_assemble_without_cable_roundtrips(
        self,
        config: IConfig,
        logger: ILogger,
        input_im_cable_system_dtos: InputDtos,
    ) -> None:
        """記述子が無い（IM のみ）ケーブル無し入力をそのまま再構成できる。"""
        assembler = FittedInputAssembler.create(config=config, logger=logger)
        input_dto = _first_input_without_cable(input_im_cable_system_dtos)

        result = assembler.assemble(
            input_dto=input_dto,
            descriptors=[],
            x=np.array([], dtype=float),
            im_count=0,
        )
        assert result.cable is None
        assert result.name.get_value() == input_dto.name.get_value()

    def test_assemble_with_cable_preserves_series(
        self,
        config: IConfig,
        logger: ILogger,
        input_im_cable_system_dtos: InputDtos,
    ) -> None:
        """記述子が無くてもケーブル付き入力を同一シリーズで再構成できる。"""
        assembler = FittedInputAssembler.create(config=config, logger=logger)
        input_dto = _first_input_with_single_section_cable(
            input_im_cable_system_dtos
        )

        result = assembler.assemble(
            input_dto=input_dto,
            descriptors=[],
            x=np.array([], dtype=float),
            im_count=0,
        )
        assert result.cable is not None
        assert input_dto.cable is not None
        expected_name = input_dto.cable.sections.get_all()[
            0
        ].series.name.get_value()
        actual_name = result.cable.sections.get_all()[0].series.name.get_value()
        assert actual_name == expected_name
