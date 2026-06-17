"""基本導線イミタンス計算コンバーター群（PIE型）

basic モデルに対する導線イミタンス計算を提供する。
"""

from __future__ import annotations

from im_cable_system.engine.algorithm.execute_algorithm.build_model.build_cable_model.conductor_immittance.i_conductor_immittance_converter import (
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


class BasicConductorImmittanceConverter(IConductorImmittanceConverter):
    """基本の導線イミタンス計算コンバーター（PIE型）

    抵抗線密度とインダクタンス線密度から導線インピーダンスを計算する。
    表皮効果は考慮しない。
    """

    def __init__(
        self,
        config: IConfig,
        logger: ILogger,
    ) -> None:
        """コンバーターを初期化する。

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
        conductor_model: CableConductorModelDto,  # noqa: ARG002
        base_resistance_total: FloatResistanceDto,
        base_inductance_total: FloatInductanceDto,
        frequency: ArrayFrequencyDto | None = None,
        conductor_current: ArrayComplexCurrentDto | None = None,  # noqa: ARG002
    ) -> ArrayComplexImpedanceDto:
        """導線インピーダンスを計算する。

        Args:
            conductor_model: 導線回路モデルDTO（未使用、BASICモデルではパラメータ不要）。
            base_resistance_total: 区間全体の基準抵抗 [Ω]。
            base_inductance_total: 区間全体の基準インダクタンス [H]。
            frequency: 周波数DTO（必須）。
            conductor_current: 導体電流DTO（未使用）。

        Returns:
            ArrayComplexImpedanceDto: 導線インピーダンスDTO。

        Raises:
            ValueError: frequency が None の場合。
        """
        if frequency is None:
            raise ValueError("frequency は None ではいけません。")

        eps = self._config.numerical_guard_config.eps
        max_mag = 1.0 / eps

        freq_nd_dto = frequency.to_base_unit()

        # 抵抗成分のインピーダンス
        z_r_dto = impedance_from_resistance_and_frequency(
            resistance=base_resistance_total,
            frequency=freq_nd_dto,
            eps=eps,
            max_mag=max_mag,
        ).to_base_unit()

        # リアクタンス成分のインピーダンス
        z_x_dto = impedance_from_inductance_and_frequency(
            inductance=base_inductance_total,
            frequency=freq_nd_dto,
            eps=eps,
            max_mag=max_mag,
        ).to_base_unit()

        # 複素インピーダンスの合成（直列合成）
        return combine_impedance_series(
            z_r_dto,
            z_x_dto,
            eps=eps,
            max_mag=max_mag,
        )
