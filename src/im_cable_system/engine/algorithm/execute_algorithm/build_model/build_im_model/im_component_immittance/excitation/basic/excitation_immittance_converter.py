"""励磁回路イミタンス計算コンバーターの実装クラス（基本モデル）"""

from __future__ import annotations

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
    ArrayFrequencyDto,
)
from im_cable_system.engine.shared.dto.itm import (
    ItmImExcitationDto,
)


class BasicExcitationImmittanceConverter(IExcitationImmittanceConverter):
    """基本の励磁回路イミタンス計算コンバーター（飽和効果なし）

    励磁飽和を考慮しない基本的なモデルを実装する。
    抵抗（R）とインダクタンス（L）の並列接続（R // jωL）として計算する。

    想定モデル:
        - 抵抗: 一定値（スリップ非依存）
        - インダクタンス: 一定値（スリップ非依存）
        - 並列合成: アドミタンスの加算で計算

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
            model_array_layout: 配列レイアウトDTO

        Returns:
            ItmImExcitationDto: 励磁モデル情報DTO
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

        # 抵抗成分のインピーダンスからアドミタンスを計算（基本単位に変換）
        z_rm_nd_base_dto = impedance_from_resistance_and_frequency(
            resistance=src.excitation_resistance,
            frequency=freq_nd_dto,
            eps=eps,
            max_mag=max_mag,
        ).to_base_unit()
        y_rm_nd_base_dto = admittance_from_impedance(
            z_rm_nd_base_dto, eps=eps, max_mag=max_mag
        )

        # インダクタンス成分のアドミタンス（誘導性サセプタンス）を計算（基本単位に変換）
        z_xm_nd_base_dto = impedance_from_inductance_and_frequency(
            inductance=src.excitation_inductance,
            frequency=freq_nd_dto,
            eps=eps,
            max_mag=max_mag,
        ).to_base_unit()
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
