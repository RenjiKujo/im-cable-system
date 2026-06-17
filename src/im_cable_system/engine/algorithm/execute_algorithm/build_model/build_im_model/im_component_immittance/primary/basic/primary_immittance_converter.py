"""一次回路イミタンス計算コンバーターの実装クラス（基本モデル）"""

from __future__ import annotations

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
    ArrayFrequencyDto,
)
from im_cable_system.engine.shared.dto.itm import (
    ItmImPrimaryDto,
)


class BasicPrimaryImmittanceConverter(IPrimaryImmittanceConverter):
    """基本の一次回路イミタンス計算コンバーター

    一次抵抗（R1）と一次インダクタンス（L1）の直列接続として計算する。

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
            model_array_layout: 配列レイアウトDTO

        Returns:
            ItmImPrimaryDto: 一次側モデル情報DTO
        """
        eps = self._config.numerical_guard_config.eps
        max_mag = 1.0 / eps
        # ブロードキャストされた拡張配列を取得
        extended_arrays = create_extended_arrays(model_array_layout)
        frequency_key = ArrayKey.FREQUENCY
        # 周波数DTOを作成（基本単位に変換）
        freq_nd_dto = ArrayFrequencyDto(
            value=extended_arrays[frequency_key],
            unit=model_array_layout.arrays[frequency_key].get_unit(),
        ).to_base_unit()

        # 一次抵抗からインピーダンスを計算（基本単位に変換）
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
