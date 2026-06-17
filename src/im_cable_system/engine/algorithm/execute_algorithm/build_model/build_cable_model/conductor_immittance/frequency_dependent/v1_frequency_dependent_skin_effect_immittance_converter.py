"""周波数依存導線イミタンス計算コンバーター群（表皮効果モデル, PIE型, V1）"""

from __future__ import annotations

import numpy as np

from im_cable_system.engine.algorithm.execute_algorithm.build_model.build_cable_model.conductor_immittance.i_conductor_immittance_converter import (  # noqa: E501
    IConductorImmittanceConverter,
)
from im_cable_system.engine.domain.physics.electrical import (
    combine_impedance_series,
    impedance_from_inductance_and_frequency,
    impedance_from_resistance_and_frequency,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    CableConductorModelDto,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexCurrentDto,
    ArrayComplexImpedanceDto,
    ArrayFrequencyDto,
    FloatInductanceDto,
    FloatResistanceDto,
)

# NOTE: 基準周波数は現状モジュール定数で固定（利用予定がないため config 化しない）。
_REFERENCE_FREQUENCY: float = 50.0


class FrequencyDependentSkinEffectConductorImmittanceConverterV1(
    IConductorImmittanceConverter
):
    """周波数依存の表皮効果を考慮した導線イミタンス計算コンバーター（PIE型, V1）"""

    def __init__(
        self,
        config: IConfig,
        logger: ILogger,
    ) -> None:
        """周波数依存表皮効果コンバーターを初期化する。

        Args:
            config: 計算に必要な設定。
            logger: ロガーオブジェクト。
        """
        self._config: IConfig = config
        self._logger: ILogger = logger

    @classmethod
    def create(
        cls,
        config: IConfig,
        logger: ILogger,
    ) -> IConductorImmittanceConverter:
        """導線イミタンス計算コンバーターを生成する。

        Args:
            config: 計算に必要な設定。
            logger: ロガーオブジェクト。

        Returns:
            IConductorImmittanceConverter: 生成されたコンバーター。
        """
        return cls(config=config, logger=logger)

    def convert(
        self,
        conductor_model: CableConductorModelDto,
        base_resistance_total: FloatResistanceDto,
        base_inductance_total: FloatInductanceDto,
        frequency: ArrayFrequencyDto | None = None,
        conductor_current: ArrayComplexCurrentDto | None = None,  # noqa: ARG002
    ) -> ArrayComplexImpedanceDto:
        """導線インピーダンスを計算する。

        Args:
            conductor_model: 導線回路モデルDTO（パラメータを含む）。
            base_resistance_total: 区間全体の基準抵抗 [Ω]。
            base_inductance_total: 区間全体の基準インダクタンス [H]。
            frequency: 周波数DTO（必須）。
            conductor_current: 導体電流DTO（未使用）。

        Returns:
            ArrayComplexImpedanceDto: 導線インピーダンスDTO。

        Raises:
            ValueError: 必要なパラメータがNoneの場合。
        """
        if conductor_model.params is None:
            raise ValueError("conductor_model.paramsが必要ですが、Noneです。")

        alpha_r = conductor_model.params.get_by_name("alpha_conductor_r")
        beta_r = conductor_model.params.get_by_name("beta_conductor_r")
        alpha_x = conductor_model.params.get_by_name("alpha_conductor_x")
        beta_x = conductor_model.params.get_by_name("beta_conductor_x")

        if alpha_r is None:
            raise ValueError("alpha_conductor_rが必要ですが、Noneです。")
        if beta_r is None:
            raise ValueError("beta_conductor_rが必要ですが、Noneです。")
        if alpha_x is None:
            raise ValueError("alpha_conductor_xが必要ですが、Noneです。")
        if beta_x is None:
            raise ValueError("beta_conductor_xが必要ですが、Noneです。")

        if frequency is None:
            raise ValueError("frequency は None ではいけません。")

        eps = self._config.numerical_guard_config.eps
        max_mag = 1.0 / eps

        freq_nd_dto = frequency.to_base_unit()
        freq_nd_array = freq_nd_dto.get_value()

        frequency_ratio = np.where(
            _REFERENCE_FREQUENCY > 0,
            freq_nd_array / _REFERENCE_FREQUENCY,
            freq_nd_array,
        )

        resistance_dto = base_resistance_total.to_base_unit()
        z_r_base_dto = impedance_from_resistance_and_frequency(
            resistance=resistance_dto,
            frequency=freq_nd_dto,
            eps=eps,
            max_mag=max_mag,
        ).to_base_unit()
        z_r_base_real_part = z_r_base_dto.get_real_part()

        alpha_r_value = alpha_r.get_value()
        beta_r_value = beta_r.get_value()
        z_r_real_part = (
            z_r_base_real_part
            * (
                1.0
                + alpha_r_value
                * (1.0 - np.exp(-beta_r_value * frequency_ratio))
            )
        ).astype(np.float64)
        z_r_dto = ArrayComplexImpedanceDto(
            value=z_r_real_part.astype(np.complex128), unit="Ω"
        )

        inductance_dto = base_inductance_total.to_base_unit()
        z_x_base_dto = impedance_from_inductance_and_frequency(
            inductance=inductance_dto,
            frequency=freq_nd_dto,
            eps=eps,
            max_mag=max_mag,
        ).to_base_unit()
        z_x_base_imag_part = z_x_base_dto.get_imaginary_part()

        alpha_x_value = alpha_x.get_value()
        beta_x_value = beta_x.get_value()
        reactance_scale = (
            1.0
            - alpha_x_value * (1.0 - np.exp(-beta_x_value * frequency_ratio))
        ).astype(np.float64)
        z_x_imag_part = (z_x_base_imag_part * reactance_scale).astype(
            np.float64
        )
        z_x_dto = ArrayComplexImpedanceDto(
            value=(1j * z_x_imag_part).astype(np.complex128), unit="Ω"
        )

        return combine_impedance_series(
            z_r_dto,
            z_x_dto,
            eps=eps,
            max_mag=max_mag,
        )
