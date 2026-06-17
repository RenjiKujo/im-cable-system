"""二次回路イミタンス（電流依存漏れ磁束飽和）。"""

from __future__ import annotations

import numpy as np

from im_cable_system.engine.algorithm.execute_algorithm.build_model.build_im_model.im_component_immittance.i_im_component_immittance_converter import (
    ISecondaryImmittanceConverter,
)
from im_cable_system.engine.algorithm.execute_algorithm.build_model.build_im_model.im_component_immittance.secondary.ensure_secondary_branch_for_immittance import (  # noqa: E501
    ensure_secondary_branch_for_immittance,
)
from im_cable_system.engine.domain.numerics import (
    create_extended_arrays,
)
from im_cable_system.engine.domain.physics.electrical import (
    admittance_from_impedance,
    combine_impedance_series,
    impedance_from_inductance_and_frequency,
    impedance_from_resistance_and_frequency,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ArrayKey,
    ArrayLayoutDto,
    ImSecondaryCageBranchType,
    ImSeriesDto,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexCurrentDto,
    ArrayComplexImpedanceDto,
    ArrayFrequencyDto,
    ArraySlipDto,
)
from im_cable_system.engine.shared.dto.itm import (
    ItmImSecondaryDto,
)
from im_cable_system.engine.shared.numerical_stability import (
    event_codes,
    record_numerical_stability_event,
)


class CurrentDependentSecondaryLeakageSaturationImmittanceConverterV1(
    ISecondaryImmittanceConverter
):
    """電流依存漏れ磁束飽和の二次イミタンス計算。"""

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
    ) -> ISecondaryImmittanceConverter:
        """二次回路イミタンス計算コンバーターを生成する。

        Args:
            config: 計算に必要な設定。
            logger: ロガーオブジェクト。

        Returns:
            ISecondaryImmittanceConverter: 生成されたコンバーター。
        """
        return cls(config=config, logger=logger)

    def convert(  # noqa: PLR0915
        self,
        src: ImSeriesDto,
        model_array_layout: ArrayLayoutDto,
        *,
        secondary_cage_branch_type: ImSecondaryCageBranchType = (
            ImSecondaryCageBranchType.SINGLE
        ),
        secondary_current: ArrayComplexCurrentDto | None = None,
    ) -> ItmImSecondaryDto:
        """二次回路イミタンスを計算する。

        Args:
            src: モーターシリーズDTO。
            model_array_layout: 配列レイアウトDTO。
            secondary_cage_branch_type: 計算対象の二次枝。
            secondary_current: 当該枝の二次相電流（基本単位）。必須。

        Returns:
            ItmImSecondaryDto: 二次側モデル情報DTO。

        Raises:
            ValueError: ``secondary_current`` が None の場合。
        """
        eps = self._config.numerical_guard_config.eps
        max_mag = 1.0 / eps
        if secondary_current is None:
            raise ValueError(
                "電流依存二次モデルでは secondary_current が必須です。"
            )
        ensure_secondary_branch_for_immittance(
            src,
            secondary_cage_branch_type,
        )
        sc = secondary_cage_branch_type
        sec_model = src.secondary_models[sc]
        if sec_model.params is None:
            raise ValueError("secondary_model.paramsが必要ですが、Noneです。")

        alpha_leakage_x = sec_model.params.get_by_name(
            "alpha_secondary_leakage_x"
        )
        beta_leakage_x = sec_model.params.get_by_name(
            "beta_secondary_leakage_x"
        )

        if alpha_leakage_x is None:
            raise ValueError(
                "alpha_secondary_leakage_xが必要ですが、Noneです。"
            )
        if beta_leakage_x is None:
            raise ValueError("beta_secondary_leakage_xが必要ですが、Noneです。")

        extended_arrays = create_extended_arrays(model_array_layout)
        frequency_key = ArrayKey.FREQUENCY
        slip_key = ArrayKey.SLIP
        secondary_current_array = secondary_current.get_value()

        freq_nd_dto = ArrayFrequencyDto(
            value=extended_arrays[frequency_key],
            unit=model_array_layout.arrays[frequency_key].get_unit(),
        ).to_base_unit()

        slip_nd_dto = ArraySlipDto(
            value=extended_arrays[slip_key],
            unit=model_array_layout.arrays[slip_key].get_unit(),
        ).to_base_unit()
        slip_nd_array = slip_nd_dto.get_value()

        secondary_current_magnitude = np.abs(secondary_current_array)
        nameplate_current_value = (
            src.nameplate_current.to_base_unit().get_value()
        )
        current_ratio = np.where(
            nameplate_current_value > 0,
            secondary_current_magnitude / nameplate_current_value,
            secondary_current_magnitude,
        )

        z_r2_nd_base_dto = impedance_from_resistance_and_frequency(
            resistance=src.secondary_resistances[sc],
            frequency=freq_nd_dto,
            eps=eps,
            max_mag=max_mag,
        ).to_base_unit()

        z_x2_nd_base_dto = impedance_from_inductance_and_frequency(
            inductance=src.secondary_inductances[sc],
            frequency=freq_nd_dto,
            eps=eps,
            max_mag=max_mag,
        ).to_base_unit()
        z_x2_nd_base_imag_part = z_x2_nd_base_dto.get_imaginary_part()

        alpha_leakage_x_value = alpha_leakage_x.get_value()
        beta_leakage_x_value = beta_leakage_x.get_value()
        leakage_saturation_factor = (
            1.0
            - alpha_leakage_x_value
            * np.tanh(beta_leakage_x_value * current_ratio)
        ).astype(np.float64)

        z_x2_nd_base_imag_part = (
            z_x2_nd_base_imag_part * leakage_saturation_factor
        ).astype(np.float64)

        z_x2_nd_base_dto = ArrayComplexImpedanceDto(
            value=(1j * z_x2_nd_base_imag_part).astype(np.complex128), unit="Ω"
        )

        z_nd_base_dto = combine_impedance_series(
            z_r2_nd_base_dto,
            z_x2_nd_base_dto,
            eps=eps,
            max_mag=max_mag,
        )
        y_nd_base_dto = admittance_from_impedance(
            z_nd_base_dto, eps=eps, max_mag=max_mag
        )

        # NOTE: slip クランプおよび domain 呼び出しの eps/max_mag は
        #   Config(numerical_guard.eps)由来の eps / max_mag に統一済み。
        #   残論点: slip しきい値(無次元)と eps(Ω)の分離、max_mag=1/eps の逆数結合。
        slip_too_small = slip_nd_array <= eps
        if np.any(slip_too_small):
            record_numerical_stability_event(
                event_codes.SLIP_NEAR_ZERO_SECONDARY_LEAKAGE_SAT_LOAD,
            )

        slip_nd_safe = np.where(slip_too_small, eps, slip_nd_array)
        z_r2_nd_base_real_part = z_r2_nd_base_dto.get_real_part()
        with np.errstate(divide="ignore", invalid="ignore"):
            z_nd_load_real_part = (
                (z_r2_nd_base_real_part * (1.0 - slip_nd_safe)) / slip_nd_safe
            ).astype(np.float64)

        z_nd_load_real_part = np.where(
            slip_too_small, max_mag, z_nd_load_real_part
        )

        z_nd_load_dto = ArrayComplexImpedanceDto(
            value=z_nd_load_real_part.astype(np.complex128), unit="Ω"
        )
        y_nd_load_dto = admittance_from_impedance(
            z_nd_load_dto, eps=eps, max_mag=max_mag
        )

        if np.any(slip_too_small):
            record_numerical_stability_event(
                event_codes.SLIP_NEAR_ZERO_SECONDARY_LEAKAGE_SAT_TOTAL,
            )

        with np.errstate(divide="ignore", invalid="ignore"):
            z_nd_total_real_part = (
                z_r2_nd_base_real_part / slip_nd_safe
            ).astype(np.float64)

        z_nd_total_real_part = np.where(
            slip_too_small, max_mag, z_nd_total_real_part
        )

        z_r2_total_dto = ArrayComplexImpedanceDto(
            value=z_nd_total_real_part.astype(np.complex128), unit="Ω"
        )

        z_x2_total_dto = z_x2_nd_base_dto

        z_nd_total_dto = combine_impedance_series(
            z_r2_total_dto,
            z_x2_total_dto,
            eps=eps,
            max_mag=max_mag,
        )
        y_nd_total_dto = admittance_from_impedance(
            z_nd_total_dto, eps=eps, max_mag=max_mag
        )

        return ItmImSecondaryDto(
            cage_multiplicity=src.cage_multiplicity,
            resistances={sc: src.secondary_resistances[sc]},
            inductances={sc: src.secondary_inductances[sc]},
            models={sc: sec_model},
            impedances={sc: z_nd_total_dto},
            admittances={sc: y_nd_total_dto},
            base_impedances={sc: z_nd_base_dto},
            base_admittances={sc: y_nd_base_dto},
            load_impedances={sc: z_nd_load_dto},
            load_admittances={sc: y_nd_load_dto},
        )
