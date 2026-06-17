"""単一かご向け: 総合イミタンス合成（L型・T型）。

二次側は :class:`ItmImSecondaryDto` の枝辞書 ``SINGLE`` をそのまま用いて、
一次・励磁と合成する。
"""

from __future__ import annotations

from im_cable_system.engine.algorithm.execute_algorithm.build_model.build_im_model.im_total_immittance.i_im_total_immittance_synthesizer import (  # noqa: E501
    IImTotalImmittanceSynthesizer,
)
from im_cable_system.engine.domain.physics.electrical import (
    admittance_from_impedance,
    combine_admittance_parallel,
    combine_impedance_series,
    impedance_from_admittance,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ImCircuitType,
    ImSecondaryCageBranchType,
)
from im_cable_system.engine.shared.dto.itm import (
    ItmImExcitationDto,
    ItmImPrimaryDto,
    ItmImSecondaryDto,
    ItmImTotalDto,
)


class LTypeSingleCageImTotalImmittanceSynthesizer(
    IImTotalImmittanceSynthesizer
):
    """L型回路の総合イミタンス合成（単一かごの等価二次を想定）

    L型等価回路: Z_total = 1 / (1 / Zm + 1 / (Z1 + Z2))
    励磁回路と一次側・二次側の直列合成を並列合成した形。
    """

    def __init__(self, config: IConfig, logger: ILogger) -> None:
        self._config: IConfig = config
        self._logger: ILogger = logger

    @classmethod
    def create(
        cls,
        config: IConfig,
        logger: ILogger,
    ) -> IImTotalImmittanceSynthesizer:
        """L型単一かご総合イミタンス合成ストラテジーを生成する。

        Args:
            config: 計算に必要な設定。
            logger: ロガーオブジェクト。

        Returns:
            IImTotalImmittanceSynthesizer: L型単一かご合成ストラテジー。
        """
        return cls(config=config, logger=logger)

    def synthesize(
        self,
        primary_model: ItmImPrimaryDto,
        excitation_model: ItmImExcitationDto,
        secondary_model: ItmImSecondaryDto,
    ) -> ItmImTotalDto:
        """L型回路の総合イミタンスを合成する

        Args:
            primary_model: 一次側モデル情報DTO（インピーダンス、アドミタンスを含む）
            excitation_model: 励磁モデル情報DTO（インピーダンス、アドミタンスを含む）
            secondary_model: 二次側モデル情報DTO（枝辞書）

        Returns:
            ItmImTotalDto: 総合モデル情報DTO（総合インピーダンス、総合アドミタンスを含む）

        Note:
            合成方法: Z_total = 1 / (1 / Zm + 1 / (Z1 + Z2))
        """
        branch = ImSecondaryCageBranchType.SINGLE
        if branch not in secondary_model.impedances:
            raise ValueError(
                "単一かごの総合二次合成には SINGLE 枝が必要です。"
                f" 実際のキー: {sorted(b.value for b in secondary_model.impedances)}"
            )
        eps = self._config.numerical_guard_config.eps
        max_mag = 1.0 / eps
        sec_z = secondary_model.impedances[branch]
        series_impedance = combine_impedance_series(
            primary_model.impedance,
            sec_z,
            eps=eps,
            max_mag=max_mag,
        )
        series_admittance = admittance_from_impedance(
            series_impedance,
            eps=eps,
            max_mag=max_mag,
        )

        total_admittance = combine_admittance_parallel(
            excitation_model.admittance,
            series_admittance,
            eps=eps,
            max_mag=max_mag,
        )
        total_impedance = impedance_from_admittance(
            total_admittance,
            eps=eps,
            max_mag=max_mag,
        )

        return ItmImTotalDto(
            impedance=total_impedance,
            admittance=total_admittance,
        )


class TTypeSingleCageImTotalImmittanceSynthesizer(
    IImTotalImmittanceSynthesizer
):
    """T型回路の総合イミタンス合成（単一かごの等価二次を想定）

    T型等価回路: Z_total = Z1 + 1 / (1 / Zm + 1 / Z2)
    励磁回路と二次側の並列合成と一次側を直列接続した形。
    """

    def __init__(self, config: IConfig, logger: ILogger) -> None:
        self._config: IConfig = config
        self._logger: ILogger = logger

    @classmethod
    def create(
        cls,
        config: IConfig,
        logger: ILogger,
    ) -> IImTotalImmittanceSynthesizer:
        """T型単一かご総合イミタンス合成ストラテジーを生成する。

        Args:
            config: 計算に必要な設定。
            logger: ロガーオブジェクト。

        Returns:
            IImTotalImmittanceSynthesizer: T型単一かご合成ストラテジー。
        """
        return cls(config=config, logger=logger)

    def synthesize(
        self,
        primary_model: ItmImPrimaryDto,
        excitation_model: ItmImExcitationDto,
        secondary_model: ItmImSecondaryDto,
    ) -> ItmImTotalDto:
        """T型回路の総合イミタンスを合成する

        Args:
            primary_model: 一次側モデル情報DTO（インピーダンス、アドミタンスを含む）
            excitation_model: 励磁モデル情報DTO（インピーダンス、アドミタンスを含む）
            secondary_model: 二次側モデル情報DTO（枝辞書）

        Returns:
            ItmImTotalDto: 総合モデル情報DTO（総合インピーダンス、総合アドミタンスを含む）

        Note:
            合成方法: Z_total = Z1 + 1 / (1 / Zm + 1 / Z2)
        """
        branch = ImSecondaryCageBranchType.SINGLE
        if branch not in secondary_model.admittances:
            raise ValueError(
                "単一かごの総合二次合成には SINGLE 枝が必要です。"
                f" 実際のキー: {sorted(b.value for b in secondary_model.admittances)}"
            )
        eps = self._config.numerical_guard_config.eps
        max_mag = 1.0 / eps
        sec_y = secondary_model.admittances[branch]
        parallel_admittance = combine_admittance_parallel(
            excitation_model.admittance,
            sec_y,
            eps=eps,
            max_mag=max_mag,
        )
        parallel_impedance = impedance_from_admittance(
            parallel_admittance,
            eps=eps,
            max_mag=max_mag,
        )

        total_impedance = combine_impedance_series(
            primary_model.impedance,
            parallel_impedance,
            eps=eps,
            max_mag=max_mag,
        )
        total_admittance = admittance_from_impedance(
            total_impedance,
            eps=eps,
            max_mag=max_mag,
        )

        return ItmImTotalDto(
            impedance=total_impedance,
            admittance=total_admittance,
        )


class SingleCageImTotalImmittanceSynthesizerFactory:
    """単一かご（等価二次解決込み）の総合イミタンス合成ストラテジーのファクトリ"""

    @staticmethod
    def create_synthesizer(
        topology: ImCircuitType,
        config: IConfig,
        logger: ILogger,
    ) -> IImTotalImmittanceSynthesizer:
        """回路トポロジーに応じた総合イミタンス合成ストラテジーを返す。

        Args:
            topology: 回路トポロジー（L/T）
            config: 計算に必要な設定。
            logger: ロガーオブジェクト。

        Returns:
            IImTotalImmittanceSynthesizer: 総合イミタンス合成ストラテジー

        Raises:
            ValueError: 未対応の回路トポロジーが指定された場合
        """
        if topology == ImCircuitType.L:
            return LTypeSingleCageImTotalImmittanceSynthesizer.create(
                config=config, logger=logger
            )
        if topology == ImCircuitType.T:
            return TTypeSingleCageImTotalImmittanceSynthesizer.create(
                config=config, logger=logger
            )
        raise ValueError(f"未対応の回路トポロジーです: {topology}")
