"""効率計算器（システム・IM・ケーブル）。

ItmPowerDto の有効電力から、ドメイン層の効率計算を用いて
システム全体・IM・ケーブル各段の効率 DTO を算出する。
"""

from __future__ import annotations

import numpy as np

from im_cable_system.engine.algorithm.execute_algorithm.simulate.characteristic.calculate_efficiency.i_efficiency_calculator import (  # noqa: E501
    IEfficiencyCalculator,
)
from im_cable_system.engine.domain.physics import (
    calculate_efficiency,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayActivePowerDto,
    ArrayComplexPowerDto,
    ArrayEfficiencyDto,
)
from im_cable_system.engine.shared.dto.itm import (
    ItmEfficiencyDto,
    ItmPowerDto,
)


class EfficiencyCalculator(IEfficiencyCalculator):
    """効率計算器実装（im_cable_system）。

    system / im / cable の各効率を ``P_out / P_in`` で計算する。

    本プロジェクトでは複素電力の符号が「電流の向きの定義」に依存し、
    active power が負になり得る。効率はエネルギー変換の“割合”として
    扱うため、有効電力の大きさ（絶対値）で評価する。
    ただし ``P_out > P_in`` は物理不整合として扱い、domain の
    :func:`calculate_efficiency` が ``ValueError`` を送出する。

    絶対値評価は「入力と出力で有効電力の符号が反転している」ケース
    （逆潮流の可能性）も丸めてしまうため、符号反転を検出した場合は
    効率計算を続行しつつ ``logger.warning`` で表面化する（黙殺しない）。

    NOTE: 入力点は相量（スター等価）ベースの ``input_phase_power`` /
        ``end_point_phase_power`` を使う。balanced 規約では
        ``system_total_input_power``（線量ベース）も位相補正なしで相量ベースと
        複素一致するが、ここでは規約に依存せず相量を直接使うことを明示する。
    """

    def __init__(self, config: IConfig, logger: ILogger) -> None:
        self._config: IConfig = config
        self._logger: ILogger = logger

    @classmethod
    def create(cls, config: IConfig, logger: ILogger) -> IEfficiencyCalculator:
        return cls(config=config, logger=logger)

    def calculate(self, *, power_dto: ItmPowerDto) -> ItmEfficiencyDto:
        """効率を計算する。"""
        eps = self._config.numerical_guard_config.eps

        cable_input = self._active_power_array(
            power_dto.cable_power.input_phase_power, eps=eps
        )
        cable_end = self._active_power_array(
            power_dto.cable_power.end_point_phase_power, eps=eps
        )
        im_input = self._active_power_array(
            power_dto.im_power.input_power, eps=eps
        )
        im_output = self._active_power_array(
            power_dto.im_power.output_power, eps=eps
        )

        # 逆潮流（入出力で有効電力の符号が反転）の検出。絶対値で評価する前に
        # 各効率ペアの符号整合を確認し、不整合があれば warning で表面化する。
        self._warn_if_reversed_flow(
            label="system",
            input_active=cable_input,
            output_active=im_output,
            eps=eps,
        )
        self._warn_if_reversed_flow(
            label="im", input_active=im_input, output_active=im_output, eps=eps
        )
        self._warn_if_reversed_flow(
            label="cable",
            input_active=cable_input,
            output_active=cable_end,
            eps=eps,
        )

        system_efficiency = self._calculate_one(
            input_active=cable_input,
            output_active=im_output,
            eps=eps,
        )
        im_efficiency = self._calculate_one(
            input_active=im_input,
            output_active=im_output,
            eps=eps,
        )
        cable_efficiency = self._calculate_one(
            input_active=cable_input,
            output_active=cable_end,
            eps=eps,
        )

        return ItmEfficiencyDto(
            system_efficiency=system_efficiency,
            im_efficiency=im_efficiency,
            cable_efficiency=cable_efficiency,
        )

    @staticmethod
    def _active_power_array(
        power: ArrayComplexPowerDto, *, eps: float
    ) -> np.ndarray:
        """複素電力を有効電力配列（符号つき）に変換する。

        近接ゼロ（``abs(P) <= eps``）の要素は 0 に丸める。符号は逆潮流検出に
        用いるため、ここでは絶対値化しない。
        """
        active = power.to_active_power_array(unit="W").to_base_unit()
        value = active.get_value()
        return np.where(np.abs(value) <= eps, 0.0, value)

    def _warn_if_reversed_flow(
        self,
        *,
        label: str,
        input_active: np.ndarray,
        output_active: np.ndarray,
        eps: float,
    ) -> None:
        """入出力の有効電力の符号反転（逆潮流の可能性）を検出して警告する。

        両者が有意（``abs(P) > eps``）かつ符号が異なる要素を逆潮流の疑いと
        みなす。効率自体は絶対値で計算を続行するが、黙殺せず警告で残す。

        Args:
            label: 対象（system / im / cable）。
            input_active: 入力有効電力配列（符号つき）。
            output_active: 出力有効電力配列（符号つき）。
            eps: 近接ゼロ判定のしきい値。
        """
        both_significant = (np.abs(input_active) > eps) & (
            np.abs(output_active) > eps
        )
        sign_mismatch = both_significant & (
            np.sign(input_active) != np.sign(output_active)
        )
        if np.any(sign_mismatch):
            mismatch_count = int(np.sum(sign_mismatch))
            total_count = int(input_active.size)
            self._logger.warning(
                f"{label} の効率計算で有効電力の符号反転（逆潮流の可能性）を"
                f"検出しました。入力と出力で電力方向が一致しない要素数: "
                f"{mismatch_count}/{total_count}。"
                f"効率は有効電力の大きさ（絶対値）で評価します。"
            )

    def _calculate_one(
        self,
        *,
        input_active: np.ndarray,
        output_active: np.ndarray,
        eps: float,
    ) -> ArrayEfficiencyDto:
        """1 種類の効率を domain の効率計算関数で計算する。

        有効電力は大きさ（絶対値）に変換してから domain 関数に渡す。
        """
        return calculate_efficiency(
            input_active_power=ArrayActivePowerDto(
                value=np.abs(input_active), unit="W"
            ),
            output_active_power=ArrayActivePowerDto(
                value=np.abs(output_active), unit="W"
            ),
            eps=eps,
        )
