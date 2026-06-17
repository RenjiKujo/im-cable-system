"""電流・電圧レンジ検証バリデータのテスト。

手組みの正解 ItmDto に対し、IM 入力電圧電流や結線方式を変えて、検証器が
定格→相換算（STAR/DELTA）を行ったうえで範囲逸脱を検出することを確認する
（シミュレーション不実行）。
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from im_cable_system.engine.algorithm.execute_algorithm.validate_itm_dto.validate_current_voltage_range import (  # noqa: E501
    CurrentVoltageRangeValidator,
    ICurrentVoltageRangeValidator,
)
from im_cable_system.engine.shared.config import IConfig, ILogger, Severity
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ImConnectionType,
)
from im_cable_system.engine.shared.dto.itm import ItmDto
from tests.test_algorithm.test_execute_algorithm.validate_itm_dto.itm_dto_builders import (  # noqa: E501
    build_valid_itm_dto,
    override_validation_config,
)


class TestCurrentVoltageRangeValidator:
    """CurrentVoltageRangeValidator のテストクラス。"""

    def test_create_returns_interface(
        self,
        config: IConfig,
        logger: ILogger,
    ) -> None:
        """create がインターフェイス実装を返すことを確認する。"""
        validator = CurrentVoltageRangeValidator.create(
            config=config,
            logger=logger,
        )
        assert isinstance(validator, ICurrentVoltageRangeValidator)

    def test_validate_passes_with_valid_star_data(
        self,
        config: IConfig,
        logger: ILogger,
        valid_itm_dto: ItmDto,
    ) -> None:
        """STAR の定格相換算で範囲内の正解データが通ることを確認する。"""
        validator = CurrentVoltageRangeValidator.create(
            config=config,
            logger=logger,
        )
        validator.validate(itm_dto=valid_itm_dto)

    def test_validate_passes_with_valid_delta_data(
        self,
        config: IConfig,
        logger: ILogger,
    ) -> None:
        """DELTA の定格相換算で範囲内の正解データが通ることを確認する。"""
        itm_dto = build_valid_itm_dto(connection_type=ImConnectionType.DELTA)
        validator = CurrentVoltageRangeValidator.create(
            config=config,
            logger=logger,
        )
        validator.validate(itm_dto=itm_dto)

    def test_validate_raises_on_voltage_under_range(
        self,
        config: IConfig,
        logger: ILogger,
    ) -> None:
        """相電圧が定格-許容を下回るとエラーを吐くことを確認する。"""
        # ベース設定の cv severity は INFO のため ERROR に上書きする
        error_config = override_validation_config(
            config,
            cv={"severity": Severity.ERROR},
        )
        # STAR 定格相電圧 ~115.5V に対し 50V は -10% 下限を割る
        itm_dto = build_valid_itm_dto(im_input_voltage=50.0 + 0.0j)
        validator = CurrentVoltageRangeValidator.create(
            config=error_config,
            logger=logger,
        )
        with pytest.raises(
            ValueError,
            match="電圧レンジの検証に失敗しました",
        ):
            validator.validate(itm_dto=itm_dto)

    def test_validate_raises_on_current_over_range(
        self,
        config: IConfig,
        logger: ILogger,
    ) -> None:
        """相電流が定格×(1+許容)を超えるとエラーを吐くことを確認する。"""
        # ベース設定の cv severity は INFO のため ERROR に上書きする
        error_config = override_validation_config(
            config,
            cv={"severity": Severity.ERROR},
        )
        # 電圧は範囲内のまま、電流のみ過大にする
        itm_dto = build_valid_itm_dto(im_input_current=1000.0 + 0.0j)
        validator = CurrentVoltageRangeValidator.create(
            config=error_config,
            logger=logger,
        )
        with pytest.raises(
            ValueError,
            match="電流レンジの検証に失敗しました",
        ):
            validator.validate(itm_dto=itm_dto)

    def test_validation_is_connection_independent(
        self,
        config: IConfig,
        logger: ILogger,
    ) -> None:
        """検証は結線方式に依存しない（Execute は常にスター等価相）。

        Execute ステージは結線（STAR/DELTA）に依らずスター等価相で計算するため、
        検証器も定格を常にスター基準で相換算する。よって同じスター等価相電圧なら
        STAR でも DELTA でも判定（合否）は一致する。

        - スター等価の定格相電圧 200/√3 ≈ 115.5V は両結線で範囲内（合格）。
        - 範囲外の値 50V は両結線でエラーになる。
        """
        error_config = override_validation_config(
            config,
            cv={"severity": Severity.ERROR},
        )
        phase_voltage = 200.0 / (3.0**0.5)
        validator = CurrentVoltageRangeValidator.create(
            config=error_config,
            logger=logger,
        )

        # スター等価相 115.5V は結線に依らず範囲内（例外を出さない）。
        for connection_type in (
            ImConnectionType.STAR,
            ImConnectionType.DELTA,
        ):
            in_range_dto = build_valid_itm_dto(
                connection_type=connection_type,
                im_input_voltage=complex(phase_voltage, 0.0),
            )
            validator.validate(itm_dto=in_range_dto)

        # 範囲外（50V）は結線に依らずエラーになる。
        for connection_type in (
            ImConnectionType.STAR,
            ImConnectionType.DELTA,
        ):
            out_of_range_dto = build_valid_itm_dto(
                connection_type=connection_type,
                im_input_voltage=50.0 + 0.0j,
            )
            with pytest.raises(
                ValueError,
                match="電圧レンジの検証に失敗しました",
            ):
                validator.validate(itm_dto=out_of_range_dto)

    def test_validate_warns_on_voltage_out_of_range_when_warning(
        self,
        config: IConfig,
    ) -> None:
        """severity=WARNING なら範囲逸脱でも raise せず警告ログを出す。"""
        warning_config = override_validation_config(
            config,
            cv={"severity": Severity.WARNING},
        )
        itm_dto = build_valid_itm_dto(im_input_voltage=50.0 + 0.0j)
        logger = MagicMock(spec=ILogger)
        validator = CurrentVoltageRangeValidator.create(
            config=warning_config,
            logger=logger,
        )
        validator.validate(itm_dto=itm_dto)
        logger.warning.assert_called_once()
        assert (
            "電圧レンジの検証に失敗しました" in logger.warning.call_args.args[0]
        )
