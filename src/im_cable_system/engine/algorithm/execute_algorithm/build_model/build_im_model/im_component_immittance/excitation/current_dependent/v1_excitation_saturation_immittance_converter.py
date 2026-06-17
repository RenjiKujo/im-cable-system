"""励磁回路イミタンス計算コンバーターの実装クラス（電流依存飽和モデル）"""

from __future__ import annotations

import numpy as np

from im_cable_system.engine.algorithm.execute_algorithm.build_model.build_im_model.im_component_immittance.i_im_component_immittance_converter import (
    IExcitationImmittanceConverter,
)
from im_cable_system.engine.domain.numerics import (
    create_extended_arrays,
)
from im_cable_system.engine.domain.physics.electrical import (
    admittance_from_impedance,
    combine_admittance_parallel,
    impedance_from_admittance,
    impedance_from_inductance_and_frequency,
    impedance_from_resistance_and_frequency,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ArrayKey,
    ArrayLayoutDto,
    ImSeriesDto,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexCurrentDto,
    ArrayComplexImpedanceDto,
    ArrayFrequencyDto,
)
from im_cable_system.engine.shared.dto.itm import (
    ItmImExcitationDto,
)


class CurrentDependentExcitationSaturationImmittanceConverterV1(
    IExcitationImmittanceConverter
):
    """電流依存の飽和効果を考慮した励磁回路イミタンス計算コンバーター

    励磁電流に依存して励磁リアクタンスが減少するモデルを実装する。
    高電流時に磁気飽和が進み、励磁リアクタンスが低下する。

    想定モデル:
        Rm = R * (1 + alpha_excitation_r * |Im|/Im_0)
        Xm = (2 * pi * f * L) * (1 - alpha_excitation_x * tanh(beta_excitation_x * |Im|/Im_0))
        これらインピーダンスの並列合成。

    必要なパラメータ:
        - alpha_excitation_r: 抵抗の電流依存係数
        - alpha_excitation_x: リアクタンスの飽和係数
        - beta_excitation_x: 飽和のスケール係数

    出力配列形状: model_array_layout.shapeと同じ形状
        （Slip、Frequency以外の軸が追加されても自動的に対応）
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
    ) -> IExcitationImmittanceConverter:
        """励磁回路イミタンス計算コンバーターを生成する。

        Args:
            config: 計算に必要な設定。
            logger: ロガーオブジェクト。

        Returns:
            IExcitationImmittanceConverter: 生成されたコンバーター。
        """
        return cls(config=config, logger=logger)

    def convert(
        self,
        src: ImSeriesDto,
        model_array_layout: ArrayLayoutDto,
    ) -> ItmImExcitationDto:
        """励磁回路イミタンスを計算する

        Args:
            src: モーターシリーズDTO（必要な情報は全て含まれている）
            model_array_layout: 配列レイアウトDTO。
                im_excitation_currentが無い場合は参照形状のゼロ配列で計算する（初回ビルド用）。

        Returns:
            ItmImExcitationDto: 励磁モデル情報DTO

        Raises:
            ValueError: 必要なオプションパラメータ（alpha_excitation_r,
                alpha_excitation_x, beta_excitation_x）がNoneの場合。
        """
        eps = self._config.numerical_guard_config.eps
        max_mag = 1.0 / eps
        # オプションパラメータの存在確認
        if src.excitation_model.params is None:
            raise ValueError("excitation_model.paramsが必要ですが、Noneです。")

        alpha_r = src.excitation_model.params.get_by_name("alpha_excitation_r")
        alpha_x = src.excitation_model.params.get_by_name("alpha_excitation_x")
        beta_x = src.excitation_model.params.get_by_name("beta_excitation_x")

        if alpha_r is None:
            raise ValueError("alpha_excitation_rが必要ですが、Noneです。")
        if alpha_x is None:
            raise ValueError("alpha_excitation_xが必要ですが、Noneです。")
        if beta_x is None:
            raise ValueError("beta_excitation_xが必要ですが、Noneです。")

        # ブロードキャストされた拡張配列を取得
        extended_arrays = create_extended_arrays(model_array_layout)
        frequency_key = ArrayKey.FREQUENCY
        excitation_current_key = ArrayKey.IM_EXCITATION_CURRENT
        # 励磁電流: 無ければ参照形状のゼロで計算（初回ビルド・電流未設定時）
        ref_shape = model_array_layout.get_reference_shape()
        if excitation_current_key in extended_arrays:
            excitation_current_dto = ArrayComplexCurrentDto(
                value=extended_arrays[excitation_current_key],
                unit=model_array_layout.arrays[
                    excitation_current_key
                ].get_unit(),
            ).to_base_unit()
        else:
            excitation_current_dto = ArrayComplexCurrentDto(
                value=np.zeros(ref_shape, dtype=np.complex128),
                unit="A",
            ).to_base_unit()
        excitation_current_array = excitation_current_dto.get_value()

        # 周波数DTOを作成（基本単位に変換）
        freq_nd_dto = ArrayFrequencyDto(
            value=extended_arrays[frequency_key],
            unit=model_array_layout.arrays[frequency_key].get_unit(),
        ).to_base_unit()

        # 励磁電流の大きさを計算（基準電流は定格電流を使用）
        excitation_current_magnitude = np.abs(excitation_current_array)
        nameplate_current_value = (
            src.nameplate_current.to_base_unit().get_value()
        )
        # 基準電流に対する正規化（0除算を避ける）
        current_ratio = np.where(
            nameplate_current_value > 0,
            excitation_current_magnitude / nameplate_current_value,
            excitation_current_magnitude,
        )

        # 抵抗成分のインピーダンス計算（Rm = R * (1 + alpha_r * |Im|/Im_0)）
        z_rm_nd_base_dto = impedance_from_resistance_and_frequency(
            resistance=src.excitation_resistance,
            frequency=freq_nd_dto,
            eps=eps,
            max_mag=max_mag,
        ).to_base_unit()
        # 電流依存の補正を適用（実部のみ）
        alpha_r_value = alpha_r.get_value()
        z_rm_nd_base_real_part = (
            z_rm_nd_base_dto.get_real_part()
            * (1.0 + alpha_r_value * current_ratio)
        ).astype(np.float64)
        z_rm_nd_base_dto = ArrayComplexImpedanceDto(
            value=z_rm_nd_base_real_part.astype(np.complex128), unit="Ω"
        )
        y_rm_nd_base_dto = admittance_from_impedance(
            z_rm_nd_base_dto, eps=eps, max_mag=max_mag
        )

        # リアクタンス成分のインピーダンス計算（電流依存の飽和効果を考慮）
        # 基本リアクタンスを計算
        z_xm_nd_base_dto = impedance_from_inductance_and_frequency(
            inductance=src.excitation_inductance,
            frequency=freq_nd_dto,
            eps=eps,
            max_mag=max_mag,
        ).to_base_unit()
        z_xm_nd_base_imag_part = z_xm_nd_base_dto.get_imaginary_part()

        # 飽和補正係数: 1 - alpha_x * tanh(beta_x * |Im|/Im_0)
        alpha_x_value = alpha_x.get_value()
        beta_x_value = beta_x.get_value()
        saturation_factor = (
            1.0 - alpha_x_value * np.tanh(beta_x_value * current_ratio)
        ).astype(np.float64)

        # 補正後のリアクタンス
        z_xm_nd_base_imag_part = (
            z_xm_nd_base_imag_part * saturation_factor
        ).astype(np.float64)

        # 純虚数のインピーダンスDTOを作成（実部=0, 虚部=リアクタンス）
        z_xm_nd_base_dto = ArrayComplexImpedanceDto(
            value=(1j * z_xm_nd_base_imag_part).astype(np.complex128), unit="Ω"
        )
        y_xm_nd_base_dto = admittance_from_impedance(
            z_xm_nd_base_dto, eps=eps, max_mag=max_mag
        )

        # 並列合成（アドミタンスは加算）
        y_nd_total_dto = combine_admittance_parallel(
            y_rm_nd_base_dto,
            y_xm_nd_base_dto,
            eps=eps,
            max_mag=max_mag,
        )
        # 等価インピーダンス
        z_nd_total_dto = impedance_from_admittance(
            y_nd_total_dto, eps=eps, max_mag=max_mag
        )

        return ItmImExcitationDto(
            model=src.excitation_model,
            resistance=src.excitation_resistance,
            inductance=src.excitation_inductance,
            impedance=z_nd_total_dto,
            admittance=y_nd_total_dto,
            params=src.excitation_model.params,
        )
