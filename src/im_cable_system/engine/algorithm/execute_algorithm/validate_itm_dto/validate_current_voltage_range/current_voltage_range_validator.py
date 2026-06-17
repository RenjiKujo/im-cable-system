"""電流・電圧レンジ検証の実装（im_cable_system）。

このモジュールは、電流・電圧が定格値や設計上の許容範囲に収まっているかを
検証するバリデータの実装を提供します。

注意:
    - IMの入力電圧・電流は「スター等価相」として保持される（結線に依らず）
    - 定格値（nameplate_voltage, nameplate_current）は通常、線間電圧・線電流で定義される
    - 定格値を常にスター基準で相換算（相電圧 = 線間 / √3、相電流 = 線電流）してから比較する
"""

from __future__ import annotations

import numpy as np

from im_cable_system.engine.algorithm.execute_algorithm.validate_itm_dto.validate_current_voltage_range.i_current_voltage_range_validator import (  # noqa: E501
    ICurrentVoltageRangeValidator,
)
from im_cable_system.engine.domain.validation import (
    validate_current_range,
    validate_voltage_range,
)
from im_cable_system.engine.shared.config import IConfig, ILogger, Severity
from im_cable_system.engine.shared.dto.itm import (
    ItmDto,
)

# √3の値（結線変換係数）
_SQRT_3: float = np.sqrt(3.0)


class CurrentVoltageRangeValidator(ICurrentVoltageRangeValidator):
    """電流・電圧レンジ検証の実装。

    IM 入力電圧・電流（スター等価相）が、定格値や設計上の許容範囲に
    収まっているかを検証する。ケーブル側の電圧・電流は本バリデータの対象外。
    """

    def __init__(self, config: IConfig, logger: ILogger) -> None:
        """インスタンスを初期化する。

        Args:
            config: 設定オブジェクト。
            logger: ロガーオブジェクト。
        """
        self._config: IConfig = config
        self._logger: ILogger = logger

        current_voltage_range_config = (
            config.validation_config.current_voltage_range
        )
        self._voltage_tolerance: float = (
            current_voltage_range_config.voltage_tolerance
        )
        self._current_tolerance: float = (
            current_voltage_range_config.current_tolerance
        )
        self._severity_level: Severity = current_voltage_range_config.severity

    @classmethod
    def create(
        cls, config: IConfig, logger: ILogger
    ) -> ICurrentVoltageRangeValidator:
        """バリデータのインスタンスを生成する。

        Args:
            config: 設定オブジェクト。
            logger: ロガーオブジェクト。

        Returns:
            ICurrentVoltageRangeValidator: 生成されたインスタンス。
        """
        return cls(config=config, logger=logger)

    def validate(self, itm_dto: ItmDto) -> None:
        """電流・電圧レンジを検証する。

        IM 入力電圧・電流（スター等価相）が、定格値や設計上の許容範囲に
        収まっているかを検証する。ケーブル側の電圧・電流は本バリデータの対象外。

        注意:
            - IMの入力電圧・電流は「スター等価相」として保持される（結線に依らず）
            - 定格値（nameplate_voltage, nameplate_current）は通常、線間電圧・線電流で定義される
            - 定格値を常にスター基準で相換算（相電圧 = 線間 / √3、相電流 = 線電流）してから比較する

        Args:
            itm_dto: 検証する中間DTO。

        Raises:
            ValueError: 検証に失敗した場合（重大度レベルがERRORの場合）。
        """
        if itm_dto.simulation_result is None:
            raise ValueError("simulation_resultがNoneのため、検証できません。")

        simulation_result = itm_dto.simulation_result
        model = itm_dto.model

        # IMの定格値を取得（通常は線間電圧・線電流で定義される）
        rated_voltage_line = model.im.nameplate_voltage.to_base_unit().value
        rated_current_line = model.im.nameplate_current.to_base_unit().value

        # 定格値をスター等価相の量に変換する。
        #
        # NOTE: Execute ステージは結線（STAR/DELTA）に依らず常に「スター等価相」
        #   で電圧・電流を計算する（`line_to_phase_voltage_star_balanced` を参照）。
        #   そのため検証対象の im_input_* もスター等価相であり、定格（線間値）も
        #   常にスター基準で相換算して比較する（結線で分岐しない）:
        #       相電圧 = 線間電圧 / √3、相電流 = 線電流
        #   実巻線相（デルタ等）での比較が必要な場合は Output ステージで巻線量を
        #   算出して別途行う。規約の正本は ItmImVoltageCurrentDto の docstring を参照。
        rated_voltage_phase = rated_voltage_line / _SQRT_3
        rated_current_phase = rated_current_line

        # IM入力電圧・電流を取得（相電圧・相電流）
        im_input_voltage = simulation_result.voltage_current.im_voltage_current.im_input_voltage
        im_input_current = simulation_result.voltage_current.im_voltage_current.im_input_current

        # 電圧レンジの検証（相電圧で比較）
        voltage_result = validate_voltage_range(
            voltage=im_input_voltage,
            rated_voltage=rated_voltage_phase,
            tolerance=self._voltage_tolerance,
        )

        if not voltage_result.is_valid:
            message = (
                f"電圧レンジの検証に失敗しました: {voltage_result.message}"
            )

            if self._severity_level is Severity.ERROR:
                raise ValueError(message)
            if self._severity_level is Severity.WARNING:
                self._logger.warning(message)
            else:
                # Severity.INFO: 情報ログで継続。
                self._logger.info(message)

        # 電流レンジの検証（相電流で比較）
        current_result = validate_current_range(
            current=im_input_current,
            rated_current=rated_current_phase,
            tolerance=self._current_tolerance,
        )

        if not current_result.is_valid:
            message = (
                f"電流レンジの検証に失敗しました: {current_result.message}"
            )

            if self._severity_level is Severity.ERROR:
                raise ValueError(message)
            if self._severity_level is Severity.WARNING:
                self._logger.warning(message)
            else:
                # Severity.INFO: 情報ログで継続。
                self._logger.info(message)
