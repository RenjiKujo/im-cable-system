"""一次回路イミタンス計算コンバーターの実装クラス（電流依存漏れ磁束飽和モデル）"""

from __future__ import annotations

import numpy as np

from im_cable_system.engine.algorithm.execute_algorithm.build_model.build_im_model.im_component_immittance.i_im_component_immittance_converter import (
    IPrimaryImmittanceConverter,
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
    ImSeriesDto,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexCurrentDto,
    ArrayComplexImpedanceDto,
    ArrayFrequencyDto,
)
from im_cable_system.engine.shared.dto.itm import (
    ItmImPrimaryDto,
)


class CurrentDependentPrimaryLeakageSaturationImmittanceConverterV1(
    IPrimaryImmittanceConverter
):
    """電流依存の漏れ磁束飽和を考慮した一次回路イミタンス計算コンバーター

    一次漏れリアクタンスが一次電流に依存して減少するモデルを実装する。
    高電流時に漏れ磁束路が飽和し、漏れリアクタンスが低下する。

    想定モデル:
        R1 = R1_0（一定）
        X1 = X1_0 * (1 - alpha_primary_leakage_x * tanh(beta_primary_leakage_x * |I1|/I1_0))
        ここで、I1_0は基準電流（通常は定格電流）

    必要なパラメータ:
        - alpha_primary_leakage_x: 漏れリアクタンス飽和係数
        - beta_primary_leakage_x: 漏れリアクタンス飽和スケール係数

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
    ) -> IPrimaryImmittanceConverter:
        """一次回路イミタンス計算コンバーターを生成する。

        Args:
            config: 計算に必要な設定。
            logger: ロガーオブジェクト。

        Returns:
            IPrimaryImmittanceConverter: 生成されたコンバーター。
        """
        return cls(config=config, logger=logger)

    def convert(
        self,
        src: ImSeriesDto,
        model_array_layout: ArrayLayoutDto,
    ) -> ItmImPrimaryDto:
        """一次側イミタンスを計算する

        Args:
            src: モーターシリーズDTO（必要な情報は全て含まれている）
            model_array_layout: 配列レイアウトDTO。
            im_primary_currentが無い場合は参照形状のゼロ配列で計算する（初回ビルド用）。

        Returns:
            ItmImPrimaryDto: 一次側モデル情報DTO

        Raises:
            ValueError: 必要なオプションパラメータがNoneの場合。
        """
        eps = self._config.numerical_guard_config.eps
        max_mag = 1.0 / eps
        # オプションパラメータの存在確認
        if src.primary_model.params is None:
            raise ValueError("primary_model.paramsが必要ですが、Noneです。")

        alpha_leakage_x = src.primary_model.params.get_by_name(
            "alpha_primary_leakage_x"
        )
        beta_leakage_x = src.primary_model.params.get_by_name(
            "beta_primary_leakage_x"
        )

        if alpha_leakage_x is None:
            raise ValueError("alpha_primary_leakage_xが必要ですが、Noneです。")
        if beta_leakage_x is None:
            raise ValueError("beta_primary_leakage_xが必要ですが、Noneです。")

        # ブロードキャストされた拡張配列を取得
        extended_arrays = create_extended_arrays(model_array_layout)
        frequency_key = ArrayKey.FREQUENCY
        primary_current_key = ArrayKey.IM_PRIMARY_CURRENT
        # 一次電流: 無ければ参照形状のゼロで計算（初回ビルド・電流未設定時）
        ref_shape = model_array_layout.get_reference_shape()
        if primary_current_key in extended_arrays:
            primary_current_dto = ArrayComplexCurrentDto(
                value=extended_arrays[primary_current_key],
                unit=model_array_layout.arrays[primary_current_key].get_unit(),
            ).to_base_unit()
        else:
            primary_current_dto = ArrayComplexCurrentDto(
                value=np.zeros(ref_shape, dtype=np.complex128),
                unit="A",
            ).to_base_unit()
        primary_current_array = primary_current_dto.get_value()

        # 周波数DTOを作成（基本単位に変換）
        freq_nd_dto = ArrayFrequencyDto(
            value=extended_arrays[frequency_key],
            unit=model_array_layout.arrays[frequency_key].get_unit(),
        ).to_base_unit()

        # 一次電流の大きさを計算（基準電流は定格電流を使用）
        primary_current_magnitude = np.abs(primary_current_array)
        nameplate_current_value = (
            src.nameplate_current.to_base_unit().get_value()
        )
        # 基準電流に対する正規化（0除算を避ける）
        current_ratio = np.where(
            nameplate_current_value > 0,
            primary_current_magnitude / nameplate_current_value,
            primary_current_magnitude,
        )

        # 一次抵抗からインピーダンスを計算（基本単位に変換、電流依存なし）
        z_r1_nd_base_dto = impedance_from_resistance_and_frequency(
            resistance=src.primary_resistance,
            frequency=freq_nd_dto,
            eps=eps,
            max_mag=max_mag,
        ).to_base_unit()

        # 一次インダクタンスからインピーダンスを計算（基本単位に変換）
        z_x1_nd_base_dto = impedance_from_inductance_and_frequency(
            inductance=src.primary_inductance,
            frequency=freq_nd_dto,
            eps=eps,
            max_mag=max_mag,
        ).to_base_unit()
        z_x1_nd_base_imag_part = z_x1_nd_base_dto.get_imaginary_part()

        # 漏れ磁束飽和補正係数: 1 - alpha_leakage_x * tanh(beta_leakage_x * |I1|/I1_0)
        alpha_leakage_x_value = alpha_leakage_x.get_value()
        beta_leakage_x_value = beta_leakage_x.get_value()
        leakage_saturation_factor = (
            1.0
            - alpha_leakage_x_value
            * np.tanh(beta_leakage_x_value * current_ratio)
        ).astype(np.float64)

        # 補正後の漏れリアクタンス
        z_x1_nd_base_imag_part = (
            z_x1_nd_base_imag_part * leakage_saturation_factor
        ).astype(np.float64)

        # 純虚数のインピーダンスDTOを作成（実部=0, 虚部=リアクタンス）
        z_x1_nd_base_dto = ArrayComplexImpedanceDto(
            value=(1j * z_x1_nd_base_imag_part).astype(np.complex128), unit="Ω"
        )

        # 直列合成
        z_nd_total_dto = combine_impedance_series(
            z_r1_nd_base_dto,
            z_x1_nd_base_dto,
            eps=eps,
            max_mag=max_mag,
        )
        y_nd_total_dto = admittance_from_impedance(
            z_nd_total_dto, eps=eps, max_mag=max_mag
        )

        return ItmImPrimaryDto(
            model=src.primary_model,
            resistance=src.primary_resistance,
            inductance=src.primary_inductance,
            impedance=z_nd_total_dto,
            admittance=y_nd_total_dto,
            params=src.primary_model.params,
        )
