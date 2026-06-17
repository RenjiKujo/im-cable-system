"""エネルギー保存則検証の実装（im_cable_system）。

このモジュールは、エネルギー保存則の検証を行うバリデータの
実装を提供します。
"""

from __future__ import annotations

from im_cable_system.engine.algorithm.execute_algorithm.validate_itm_dto.validate_energy_conservation.i_energy_conservation_validator import (  # noqa: E501
    IEnergyConservationValidator,
)
from im_cable_system.engine.domain.physics.electrical import (
    add_power,
)
from im_cable_system.engine.domain.validation import (
    validate_energy_conservation,
)
from im_cable_system.engine.shared.config import IConfig, ILogger, Severity
from im_cable_system.engine.shared.dto.itm import (
    ItmDto,
)


class EnergyConservationValidator(IEnergyConservationValidator):
    """エネルギー保存則検証の実装。

    電力における入出力と損失のバランスが、許容誤差内でエネルギー保存則を
    満たしているかを検証する。
    """

    def __init__(self, config: IConfig, logger: ILogger) -> None:
        """インスタンスを初期化する。

        Args:
            config: 設定オブジェクト。
            logger: ロガーオブジェクト。
        """
        self._config: IConfig = config
        self._logger: ILogger = logger

        energy_conservation_config = (
            config.validation_config.energy_conservation
        )
        self._tolerance: float = energy_conservation_config.tolerance
        self._severity_level: Severity = energy_conservation_config.severity

    @classmethod
    def create(
        cls, config: IConfig, logger: ILogger
    ) -> IEnergyConservationValidator:
        """バリデータのインスタンスを生成する。

        Args:
            config: 設定オブジェクト。
            logger: ロガーオブジェクト。

        Returns:
            IEnergyConservationValidator: 生成されたインスタンス。
        """
        return cls(config=config, logger=logger)

    def validate(self, itm_dto: ItmDto) -> None:
        """エネルギー保存則を検証する。

        入力電力 = 出力電力 + 損失電力 が許容誤差内で成り立つことを検証する。

        Args:
            itm_dto: 検証する中間DTO。

        Raises:
            ValueError: 検証に失敗した場合（重大度レベルがERRORの場合）。
        """
        if itm_dto.simulation_result is None:
            raise ValueError("simulation_resultがNoneのため、検証できません。")

        simulation_result = itm_dto.simulation_result
        if simulation_result.power is None:
            raise ValueError(
                "simulation_result.powerがNoneのため、エネルギー保存検証できません。"
                "電流電圧のみの結果では検証を行いません。"
            )

        # 入力電力: ケーブル入力点の相量ベース電力（位相基準を統一するため）  # noqa: ERA001
        # NOTE: system_total_input_power は線量ベースで計算するが、balanced 規約
        # では位相補正なしで input_phase_power と複素一致する。ここでは位相基準を
        # 相量（スター等価）に明示的にそろえる意図で input_phase_power を使用する。
        input_power = simulation_result.power.cable_power.input_phase_power

        # 出力電力: IM出力電力  # noqa: ERA001
        output_power = simulation_result.power.im_power.output_power

        # 損失電力: ケーブル損失 + IM損失  # noqa: ERA001
        loss_power_cable = simulation_result.power.cable_power.total_loss_power
        loss_power_im = simulation_result.power.im_power.total_loss_power

        # 損失電力の合計（ドメインの power 加算ヘルパーで単位を統一して加算する）
        loss_power = add_power(
            power1=loss_power_cable,
            power2=loss_power_im,
        )

        # Domain層の検証関数を呼び出し
        result = validate_energy_conservation(
            input_power=input_power,
            output_power=output_power,
            loss_power=loss_power,
            tolerance=self._tolerance,
            eps=self._config.numerical_guard_config.eps,
        )

        if not result.is_valid:
            message = f"エネルギー保存則の検証に失敗しました: {result.message}"

            if self._severity_level is Severity.ERROR:
                raise ValueError(message)
            if self._severity_level is Severity.WARNING:
                self._logger.warning(message)
            else:
                # Severity.INFO: 情報ログで継続。
                self._logger.info(message)
