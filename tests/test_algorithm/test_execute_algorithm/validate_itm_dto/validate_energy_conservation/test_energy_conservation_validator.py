"""エネルギー保存則検証バリデータのテスト。

手組みの正解 ItmDto に対して、電力収支を崩した値を注入し、検証器が
重大度に応じてエラー／警告を出すことを確認する（シミュレーション不実行）。
"""

from __future__ import annotations

from dataclasses import replace
from unittest.mock import MagicMock

import pytest

from im_cable_system.engine.algorithm.execute_algorithm.validate_itm_dto.validate_energy_conservation import (  # noqa: E501
    EnergyConservationValidator,
    IEnergyConservationValidator,
)
from im_cable_system.engine.shared.config import IConfig, ILogger, Severity
from im_cable_system.engine.shared.dto.itm import ItmDto
from tests.test_algorithm.test_execute_algorithm.validate_itm_dto.itm_dto_builders import (  # noqa: E501
    build_valid_itm_dto,
    override_validation_config,
)


class TestEnergyConservationValidator:
    """EnergyConservationValidator のテストクラス。"""

    def test_create_returns_interface(
        self,
        config: IConfig,
        logger: ILogger,
    ) -> None:
        """create がインターフェイス実装を返すことを確認する。"""
        validator = EnergyConservationValidator.create(
            config=config,
            logger=logger,
        )
        assert isinstance(validator, IEnergyConservationValidator)

    def test_validate_passes_with_valid_data(
        self,
        config: IConfig,
        logger: ILogger,
        valid_itm_dto: ItmDto,
    ) -> None:
        """収支が成立する正解データで例外が出ないことを確認する。"""
        validator = EnergyConservationValidator.create(
            config=config,
            logger=logger,
        )
        validator.validate(itm_dto=valid_itm_dto)

    def test_validate_raises_if_simulation_result_is_none(
        self,
        config: IConfig,
        logger: ILogger,
        valid_itm_dto: ItmDto,
    ) -> None:
        """simulation_result が None ならエラーを吐くことを確認する。"""
        itm_dto = replace(valid_itm_dto, simulation_result=None)
        validator = EnergyConservationValidator.create(
            config=config,
            logger=logger,
        )
        with pytest.raises(ValueError, match="simulation_resultがNone"):
            validator.validate(itm_dto=itm_dto)

    def test_validate_raises_if_power_is_none(
        self,
        config: IConfig,
        logger: ILogger,
    ) -> None:
        """power が None（電流電圧のみ）ならエラーを吐くことを確認する。"""
        itm_dto = build_valid_itm_dto(with_power=False)
        validator = EnergyConservationValidator.create(
            config=config,
            logger=logger,
        )
        with pytest.raises(ValueError, match="powerがNone"):
            validator.validate(itm_dto=itm_dto)

    def test_validate_raises_on_energy_imbalance_when_error(
        self,
        config: IConfig,
        logger: ILogger,
    ) -> None:
        """収支を崩すと（severity=ERROR）エラーを吐くことを確認する。"""
        # 入力電力だけ過大にして 入力 = 出力 + 損失 を破る
        itm_dto = build_valid_itm_dto(cable_input_phase_power=100.0 + 2.0j)
        validator = EnergyConservationValidator.create(
            config=config,
            logger=logger,
        )
        with pytest.raises(
            ValueError,
            match="エネルギー保存則の検証に失敗しました",
        ):
            validator.validate(itm_dto=itm_dto)

    def test_validate_warns_on_energy_imbalance_when_warning(
        self,
        config: IConfig,
    ) -> None:
        """severity=WARNING なら収支違反でも raise せず警告ログを出す。"""
        warning_config = override_validation_config(
            config,
            energy={"severity": Severity.WARNING},
        )
        itm_dto = build_valid_itm_dto(cable_input_phase_power=100.0 + 2.0j)
        logger = MagicMock(spec=ILogger)
        validator = EnergyConservationValidator.create(
            config=warning_config,
            logger=logger,
        )
        validator.validate(itm_dto=itm_dto)
        logger.warning.assert_called_once()
        assert (
            "エネルギー保存則の検証に失敗しました"
            in logger.warning.call_args.args[0]
        )
