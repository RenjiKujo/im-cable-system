"""二次回路イミタンス計算コンバーターの実装クラス（基本モデル）"""

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


class BasicSecondaryImmittanceConverter(ISecondaryImmittanceConverter):
    """基本の二次回路イミタンス計算コンバーター（表皮効果なし）

    表皮効果を考慮しない基本的なモデルを実装する。
    二次抵抗（R2）と二次インダクタンス（L2）の直列接続として計算する。

    想定モデル:
        - 全範囲: R2/s + jωL2（スリップ依存の抵抗とインダクタンスの合成）
        - 基本部分: R2 + jωL2（全範囲から負荷依存部分を除いた部分）
        - 負荷依存: R2(1-s)/s（純抵抗、スリップ依存の負荷抵抗）

    計算特性:
        - 抵抗: 一定値（R2）
        - インダクタンス: 一定値（L2）
        - スリップ値が0や1に近い場合、計算結果が極端になる可能性あり

    数値安定性:
        - DTO側（インピーダンス/アドミタンス）でクランプ処理を実施
        - slip 近接ゼロ（`<= eps`）は本コンバーターで検出・クランプし、
          数値安定化イベントを記録する

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
    ) -> ISecondaryImmittanceConverter:
        """二次回路イミタンス計算コンバーターを生成する。

        Args:
            config: 計算に必要な設定。
            logger: ロガーオブジェクト。

        Returns:
            ISecondaryImmittanceConverter: 生成されたコンバーター。
        """
        return cls(config=config, logger=logger)

    def convert(
        self,
        src: ImSeriesDto,
        model_array_layout: ArrayLayoutDto,
        *,
        secondary_cage_branch_type: ImSecondaryCageBranchType = (
            ImSecondaryCageBranchType.SINGLE
        ),
        secondary_current: ArrayComplexCurrentDto | None = None,
    ) -> ItmImSecondaryDto:
        """二次回路イミタンスを計算する

        Args:
            src: モーターシリーズDTO（必要な情報は全て含まれている）
            model_array_layout: 配列レイアウトDTO
            secondary_cage_branch_type: 計算対象の二次枝。
            secondary_current: 未使用（互換のため受け取るのみ）

        Returns:
            ItmImSecondaryDto: 二次側モデル情報DTO
        """
        eps = self._config.numerical_guard_config.eps
        max_mag = 1.0 / eps
        _ = secondary_current
        ensure_secondary_branch_for_immittance(
            src,
            secondary_cage_branch_type,
        )
        sc = secondary_cage_branch_type
        # ブロードキャストされた拡張配列を取得し、周波数・スリップ配列を取得
        extended_arrays = create_extended_arrays(model_array_layout)
        frequency_key = ArrayKey.FREQUENCY
        slip_key = ArrayKey.SLIP
        # 周波数DTOを作成（基本単位に変換）
        freq_nd_dto = ArrayFrequencyDto(
            value=extended_arrays[frequency_key],
            unit=model_array_layout.arrays[frequency_key].get_unit(),
        ).to_base_unit()

        # スリップ配列のDTO作成（基本単位に変換）
        slip_nd_dto = ArraySlipDto(
            value=extended_arrays[slip_key],
            unit=model_array_layout.arrays[slip_key].get_unit(),
        ).to_base_unit()
        slip_nd_array = slip_nd_dto.get_value()

        # スリップ非依存のインピーダンス計算（R2 + jωL2）
        # 抵抗成分からインピーダンスを計算（基本単位に変換）
        z_r2_nd_base_dto = impedance_from_resistance_and_frequency(
            resistance=src.secondary_resistances[sc],
            frequency=freq_nd_dto,
            eps=eps,
            max_mag=max_mag,
        ).to_base_unit()

        # リアクタンス成分からインピーダンスを計算（基本単位に変換）
        z_x2_nd_base_dto = impedance_from_inductance_and_frequency(
            inductance=src.secondary_inductances[sc],
            frequency=freq_nd_dto,
            eps=eps,
            max_mag=max_mag,
        ).to_base_unit()

        # 複素インピーダンスの合成（直列合成）
        z_nd_base_dto = combine_impedance_series(
            z_r2_nd_base_dto,
            z_x2_nd_base_dto,
            eps=eps,
            max_mag=max_mag,
        )
        y_nd_base_dto = admittance_from_impedance(
            z_nd_base_dto, eps=eps, max_mag=max_mag
        )

        # 負荷依存のインピーダンス計算（R2(1-s)/s、純抵抗）
        # スリップが極小の場合のマスク処理
        # NOTE: slip クランプおよび domain 呼び出しの eps/max_mag は
        #   Config(numerical_guard.eps)由来の eps / max_mag に統一済み。
        #   残論点: slip しきい値(無次元)と eps(Ω)の分離、max_mag=1/eps の逆数結合。
        slip_too_small = slip_nd_array <= eps
        if np.any(slip_too_small):
            record_numerical_stability_event(
                event_codes.SLIP_NEAR_ZERO_SECONDARY_LOAD_IMM,
            )

        # 安全なスリップ値で計算
        slip_nd_safe = np.where(slip_too_small, eps, slip_nd_array)
        z_r2_nd_base_real_part = z_r2_nd_base_dto.get_real_part()
        with np.errstate(divide="ignore", invalid="ignore"):
            z_nd_load_real_part = (
                (z_r2_nd_base_real_part * (1.0 - slip_nd_safe)) / slip_nd_safe
            ).astype(np.float64)

        # 極小スリップの場合はmax_magを直接設定
        z_nd_load_real_part = np.where(
            slip_too_small, max_mag, z_nd_load_real_part
        )

        # インピーダンスDTO作成
        z_nd_load_dto = ArrayComplexImpedanceDto(
            value=z_nd_load_real_part.astype(np.complex128), unit="Ω"
        )
        y_nd_load_dto = admittance_from_impedance(
            z_nd_load_dto, eps=eps, max_mag=max_mag
        )

        # 全範囲インピーダンス計算（R2/s + jωL2）
        # スリップが極小の場合のマスク処理
        slip_too_small_total = slip_nd_array <= eps
        if np.any(slip_too_small_total):
            record_numerical_stability_event(
                event_codes.SLIP_NEAR_ZERO_SECONDARY_TOTAL_IMM,
            )

        # 安全なスリップ値で計算
        slip_nd_safe_total = np.where(slip_too_small_total, eps, slip_nd_array)
        z_r2_nd_base_real_part = z_r2_nd_base_dto.get_real_part()
        with np.errstate(divide="ignore", invalid="ignore"):
            z_nd_total_real_part = (
                z_r2_nd_base_real_part / slip_nd_safe_total
            ).astype(np.float64)

        # 極小スリップの場合はmax_magを直接設定
        z_nd_total_real_part = np.where(
            slip_too_small_total, max_mag, z_nd_total_real_part
        )

        # 抵抗成分（実部）
        z_r2_total_dto = ArrayComplexImpedanceDto(
            value=z_nd_total_real_part.astype(np.complex128), unit="Ω"
        )

        # リアクタンス成分（虚部）は基本部分と同じ
        z_x2_total_dto = z_x2_nd_base_dto

        # 複素インピーダンスの合成（直列合成）
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
            models={sc: src.secondary_models[sc]},
            impedances={sc: z_nd_total_dto},
            admittances={sc: y_nd_total_dto},
            base_impedances={sc: z_nd_base_dto},
            base_admittances={sc: y_nd_base_dto},
            load_impedances={sc: z_nd_load_dto},
            load_admittances={sc: y_nd_load_dto},
        )
