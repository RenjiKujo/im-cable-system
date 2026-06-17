"""π型ケーブル電力計算器（im_cable_system）。"""

from __future__ import annotations

from im_cable_system.engine.algorithm.execute_algorithm.simulate.power.calculate_cable_power.i_cable_power_calculator import (  # noqa: E501
    ICablePowerCalculator,
)
from im_cable_system.engine.domain.physics.electrical import (
    add_power,
    three_phase_power_from_voltage_and_current_phase,
    to_three_phase_power_from_line,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.itm import (
    ItmCableModelDto,
    ItmCablePowerDto,
    ItmCableVoltageCurrentDto,
)

# NOTE: 線量ベース三相電力と相量ベース三相電力の位相整合について。
#
#   有名式 S_3φ = √3 · V_LL · conj(I_L) は皮相電力の大きさと力率をまとめた式で、
#   V_LL と I_L の位相差をインピーダンス角 θ に一致させることを暗黙に前提する。
#
#   本リポジトリの Execute ステージは平衡 per-phase の balanced 規約を採用し、
#   線間電圧と相電圧を「同位相」とみなして大きさだけ √3 倍異なる量として扱う
#   （`line_to_phase_voltage_star_balanced` を参照）。すなわち:
#       V_LL = √3 · V_φ,  I_L = I_φ
#   このとき有名式に複素フェーザのまま代入しても、
#       S_line = √3 · V_LL · conj(I_L) = √3 · (√3 · V_φ) · conj(I_φ)
#              = 3 · V_φ · conj(I_φ) = S_phase
#   となり、相量ベース三相電力 S_phase と**位相補正なしで複素一致**する。
#   よって system_total_input_power は線量式から直接得られ、力率・有効/無効の
#   分解も後段の相量ベース処理（効率計算・エネルギー保存検証など）と整合する。
#
#   HISTORY: 旧 rotation-aware 規約（V_LL = √3 · V_φ · e^{+jπ/6}）では線量式が
#       S_phase · e^{+jπ/6} となるため e^{-jπ/6} の位相補正が必要だった。balanced
#       規約への移行に伴い、この補正は不要となり撤去した。方向（位相）を厳密に
#       扱う場合は rotation-aware 変換と +30° 補正を併用すること。


class PieCablePowerCalculator(ICablePowerCalculator):
    """π型ケーブル回路の電力計算器。

    `ItmCableVoltageCurrentDto` の各地点の電圧・電流から、
    `ItmCablePowerDto` を構築する。
    """

    def __init__(self, config: IConfig, logger: ILogger) -> None:
        self._config: IConfig = config
        self._logger: ILogger = logger

    @classmethod
    def create(cls, config: IConfig, logger: ILogger) -> ICablePowerCalculator:
        return cls(config=config, logger=logger)

    def calculate(
        self,
        cable_model: ItmCableModelDto,  # noqa: ARG002
        cable_voltage_current: ItmCableVoltageCurrentDto,
    ) -> ItmCablePowerDto:
        """ケーブル電力DTOを構築する。

        ``system_total_input_power`` は「システム入力点（ケーブル上流端）の
        三相合計複素電力」である。入力線間電圧・線電流（= 線側の量）から
        ``to_three_phase_power_from_line`` で計算する。Execute ステージは平衡
        per-phase の balanced 規約（線間電圧と相電圧を同位相とみなす）を採用する
        ため、線量ベース三相電力は相量ベースの ``input_phase_power`` と
        位相補正なしで複素一致し、有効電力・無効電力（力率）の分解も後段の
        相量ベース処理（効率計算・エネルギー保存検証など）と整合する。詳細は
        モジュール冒頭の NOTE を参照。
        """
        # 線量ベースの三相電力を計算する。balanced 規約のため +30° 補正は不要。
        system_total_input_power = to_three_phase_power_from_line(
            line_voltage=cable_voltage_current.input_line_voltage,
            line_current=cable_voltage_current.input_line_current,
        )

        input_phase_power = three_phase_power_from_voltage_and_current_phase(
            voltage=cable_voltage_current.input_phase_voltage,
            current=cable_voltage_current.input_phase_current,
        )

        conductor_loss_power = {
            key: three_phase_power_from_voltage_and_current_phase(
                voltage=cable_voltage_current.conductor_voltage[key],
                current=cable_voltage_current.conductor_current[key],
            )
            for key in cable_voltage_current.conductor_voltage
        }
        ground_loss_power = {
            key: three_phase_power_from_voltage_and_current_phase(
                voltage=cable_voltage_current.ground_voltage[key],
                current=cable_voltage_current.ground_current[key],
            )
            for key in cable_voltage_current.ground_voltage
        }

        end_point_phase_power = (
            three_phase_power_from_voltage_and_current_phase(
                voltage=cable_voltage_current.end_point_phase_voltage,
                current=cable_voltage_current.end_point_phase_current,
            )
        )

        total_loss_power = None
        for power in list(conductor_loss_power.values()) + list(
            ground_loss_power.values()
        ):
            total_loss_power = (
                power
                if total_loss_power is None
                else add_power(power1=total_loss_power, power2=power)
            )
        if total_loss_power is None:
            raise ValueError("ケーブル損失電力の合計対象が空です。")

        return ItmCablePowerDto(
            system_total_input_power=system_total_input_power,
            input_phase_power=input_phase_power,
            conductor_loss_power=conductor_loss_power,
            ground_loss_power=ground_loss_power,
            end_point_phase_power=end_point_phase_power,
            total_loss_power=total_loss_power,
        )
