"""中間 DTO 検証オーケストレーターのテスト。

各検証器の数値的正しさは個別テストとドメイン層テストで担保済みのため、
ここでは「create」「simulation_result None の fail-closed（有効な検証があれば
ValueError、全無効なら何もしない）」「Config の enabled ゲーティング
（無効化した検証は発火しない）」という統括責務を確認する。
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from im_cable_system.engine.algorithm.execute_algorithm.validate_itm_dto import (  # noqa: E501
    IItmValidationOrchestrator,
)
from im_cable_system.engine.algorithm.execute_algorithm.validate_itm_dto.orchestrate import (  # noqa: E501
    ItmValidationOrchestrator,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.itm import ItmDto
from tests.test_algorithm.test_execute_algorithm.validate_itm_dto.itm_dto_builders import (  # noqa: E501
    build_valid_itm_dto,
    override_validation_config,
)


class TestItmValidationOrchestrator:
    """ItmValidationOrchestrator のテストクラス。"""

    def test_create_returns_interface(
        self,
        config: IConfig,
        logger: ILogger,
    ) -> None:
        """create がインターフェイス実装を返すことを確認する。"""
        orchestrator = ItmValidationOrchestrator.create(
            config=config,
            logger=logger,
        )
        assert isinstance(orchestrator, IItmValidationOrchestrator)

    def test_validate_passes_with_valid_data(
        self,
        config: IConfig,
        logger: ILogger,
        valid_itm_dto: ItmDto,
    ) -> None:
        """正解データで両検証ともパスすることを確認する。"""
        orchestrator = ItmValidationOrchestrator.create(
            config=config,
            logger=logger,
        )
        orchestrator.validate(itm_dto=valid_itm_dto)

    def test_validate_raises_when_simulation_result_is_none_and_enabled(
        self,
        config: IConfig,
        valid_itm_dto: ItmDto,
        logger: ILogger,
    ) -> None:
        """有効な検証がある状態で simulation_result が None なら raise する。"""
        itm_dto = replace(valid_itm_dto, simulation_result=None)
        orchestrator = ItmValidationOrchestrator.create(
            config=config,
            logger=logger,
        )
        with pytest.raises(ValueError, match="simulation_result"):
            orchestrator.validate(itm_dto=itm_dto)

    def test_validate_skips_when_simulation_result_is_none_all_disabled(
        self,
        config: IConfig,
        logger: ILogger,
        valid_itm_dto: ItmDto,
    ) -> None:
        """全検証が無効なら simulation_result が None でも raise しない。"""
        disabled_config = override_validation_config(
            config,
            energy={"enabled": False},
            cv={"enabled": False},
        )
        itm_dto = replace(valid_itm_dto, simulation_result=None)
        orchestrator = ItmValidationOrchestrator.create(
            config=disabled_config,
            logger=logger,
        )
        orchestrator.validate(itm_dto=itm_dto)

    def test_validate_raises_when_both_enabled_and_imbalanced(
        self,
        config: IConfig,
        logger: ILogger,
    ) -> None:
        """両検証 ERROR・有効時、収支違反でエラーを吐くことを確認する。"""
        itm_dto = build_valid_itm_dto(cable_input_phase_power=100.0 + 2.0j)
        orchestrator = ItmValidationOrchestrator.create(
            config=config,
            logger=logger,
        )
        with pytest.raises(ValueError, match="エネルギー保存則"):
            orchestrator.validate(itm_dto=itm_dto)

    def test_energy_gating_skips_when_disabled(
        self,
        config: IConfig,
        logger: ILogger,
    ) -> None:
        """energy_conservation を無効化すると収支違反でも発火しない。"""
        disabled_config = override_validation_config(
            config,
            energy={"enabled": False},
        )
        # 収支は崩すが、電流電圧は範囲内に保つ
        itm_dto = build_valid_itm_dto(cable_input_phase_power=100.0 + 2.0j)
        orchestrator = ItmValidationOrchestrator.create(
            config=disabled_config,
            logger=logger,
        )
        orchestrator.validate(itm_dto=itm_dto)

    def test_current_voltage_gating_skips_when_disabled(
        self,
        config: IConfig,
        logger: ILogger,
    ) -> None:
        """current_voltage_range を無効化すると範囲逸脱でも発火しない。"""
        disabled_config = override_validation_config(
            config,
            cv={"enabled": False},
        )
        # 電圧は範囲外にするが、電力収支は成立させる
        itm_dto = build_valid_itm_dto(im_input_voltage=50.0 + 0.0j)
        orchestrator = ItmValidationOrchestrator.create(
            config=disabled_config,
            logger=logger,
        )
        orchestrator.validate(itm_dto=itm_dto)
