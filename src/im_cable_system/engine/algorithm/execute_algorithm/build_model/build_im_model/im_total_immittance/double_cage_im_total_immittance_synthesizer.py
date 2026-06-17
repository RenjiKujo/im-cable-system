"""二重かご向け: 総合イミタンス合成（L型・T型）。

二次側は INNER/OUTER のアドミタンス並列合成で等価二次 Z/Y を得てから、
一次・励磁と合成する。

Note:
    ``_equivalent_secondary_immittance_for_double_cage_total_synthesis`` は
    本モジュール内の合成器が用いる内部ヘルパーであり、パッケージ外の公開
    API ではない（``__all__`` 非掲載）。公開入口は
    ``DoubleCageImTotalImmittanceSynthesizerFactory`` と各 Synthesizer。
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
    expected_branch_keys_for_cage_multiplicity,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexAdmittanceDto,
    ArrayComplexImpedanceDto,
)
from im_cable_system.engine.shared.dto.itm import (
    ItmImExcitationDto,
    ItmImPrimaryDto,
    ItmImSecondaryDto,
    ItmImTotalDto,
)


def _equivalent_secondary_immittance_for_double_cage_total_synthesis(
    secondary_model: ItmImSecondaryDto,
    *,
    eps: float,
    max_mag: float,
) -> tuple[ArrayComplexImpedanceDto, ArrayComplexAdmittanceDto]:
    """二重かごの L/T 総合合成に用いる等価二次 Z/Y を返す。

    Args:
        secondary_model: 二次側モデル情報DTO（INNER/OUTER の枝辞書を期待）。
        eps: 近接ゼロ判定のしきい値（Config 由来）。
        max_mag: 最大の大きさ（``1 / eps``）。

    Returns:
        tuple[ArrayComplexImpedanceDto, ArrayComplexAdmittanceDto]:
            等価二次インピーダンスと等価二次アドミタンス。

    Raises:
        ValueError: INNER/OUTER が揃っていない場合。
    """
    expected = expected_branch_keys_for_cage_multiplicity(
        secondary_model.cage_multiplicity
    )
    keys = frozenset(secondary_model.admittances.keys())
    if keys != expected:
        raise ValueError(
            "二重かごの総合二次合成には INNER と OUTER の両枝が必要です。"
            f" 実際のキー: {sorted(b.value for b in keys)}"
        )
    inner_branch = ImSecondaryCageBranchType.INNER
    outer_branch = ImSecondaryCageBranchType.OUTER
    equivalent_admittance = combine_admittance_parallel(
        secondary_model.admittances[inner_branch],
        secondary_model.admittances[outer_branch],
        eps=eps,
        max_mag=max_mag,
    )
    equivalent_impedance = impedance_from_admittance(
        equivalent_admittance,
        eps=eps,
        max_mag=max_mag,
    )
    return equivalent_impedance, equivalent_admittance


class LTypeDoubleCageImTotalImmittanceSynthesizer(
    IImTotalImmittanceSynthesizer
):
    """L型回路の総合イミタンス合成（二重かごの等価二次を想定）

    二重かごの等価二次は、INNER/OUTER の二次アドミタンスを並列合成して得る。

    - 等価二次（double cage）:
        Y2_eq = Y2_inner + Y2_outer
        Z2_eq = 1 / Y2_eq

    - L型等価回路（単一かごと同型、Z2 を Z2_eq に置換）:
        Z_total = 1 / (1 / Zm + 1 / (Z1 + Z2_eq))
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
        """L型二重かご総合イミタンス合成ストラテジーを生成する。

        Args:
            config: 計算に必要な設定。
            logger: ロガーオブジェクト。

        Returns:
            IImTotalImmittanceSynthesizer: L型二重かご合成ストラテジー。
        """
        return cls(config=config, logger=logger)

    def synthesize(
        self,
        primary_model: ItmImPrimaryDto,
        excitation_model: ItmImExcitationDto,
        secondary_model: ItmImSecondaryDto,
    ) -> ItmImTotalDto:
        """L型回路の総合イミタンスを合成する（二重かご）。

        Args:
            primary_model: 一次側モデル情報DTO。
            excitation_model: 励磁モデル情報DTO。
            secondary_model: 二次側モデル情報DTO（INNER/OUTER の枝辞書）。

        Returns:
            ItmImTotalDto: 総合モデル情報DTO。

        Note:
            合成方法:
                Y2_eq = Y2_inner + Y2_outer
                Z2_eq = 1 / Y2_eq
                Z_total = 1 / (1 / Zm + 1 / (Z1 + Z2_eq))
        """
        eps = self._config.numerical_guard_config.eps
        max_mag = 1.0 / eps
        sec_z, _ = (
            _equivalent_secondary_immittance_for_double_cage_total_synthesis(
                secondary_model,
                eps=eps,
                max_mag=max_mag,
            )
        )
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
            impedance=total_impedance, admittance=total_admittance
        )


class TTypeDoubleCageImTotalImmittanceSynthesizer(
    IImTotalImmittanceSynthesizer
):
    """T型回路の総合イミタンス合成（二重かごの等価二次を想定）

    二重かごの等価二次は、INNER/OUTER の二次アドミタンスを並列合成して得る。

    - 等価二次（double cage）:
        Y2_eq = Y2_inner + Y2_outer
        Z2_eq = 1 / Y2_eq

    - T型等価回路（単一かごと同型、Z2 を Z2_eq に置換）:
        Z_total = Z1 + 1 / (1 / Zm + 1 / Z2_eq)
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
        """T型二重かご総合イミタンス合成ストラテジーを生成する。

        Args:
            config: 計算に必要な設定。
            logger: ロガーオブジェクト。

        Returns:
            IImTotalImmittanceSynthesizer: T型二重かご合成ストラテジー。
        """
        return cls(config=config, logger=logger)

    def synthesize(
        self,
        primary_model: ItmImPrimaryDto,
        excitation_model: ItmImExcitationDto,
        secondary_model: ItmImSecondaryDto,
    ) -> ItmImTotalDto:
        """T型回路の総合イミタンスを合成する（二重かご）。

        Args:
            primary_model: 一次側モデル情報DTO。
            excitation_model: 励磁モデル情報DTO。
            secondary_model: 二次側モデル情報DTO（INNER/OUTER の枝辞書）。

        Returns:
            ItmImTotalDto: 総合モデル情報DTO。

        Note:
            合成方法:
                Y2_eq = Y2_inner + Y2_outer
                Z2_eq = 1 / Y2_eq
                Z_total = Z1 + 1 / (1 / Zm + 1 / Z2_eq)
        """
        eps = self._config.numerical_guard_config.eps
        max_mag = 1.0 / eps
        _, sec_y = (
            _equivalent_secondary_immittance_for_double_cage_total_synthesis(
                secondary_model,
                eps=eps,
                max_mag=max_mag,
            )
        )
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
            impedance=total_impedance, admittance=total_admittance
        )


class DoubleCageImTotalImmittanceSynthesizerFactory:
    """二重かご用総合イミタンス合成ファクトリ。"""

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
            return LTypeDoubleCageImTotalImmittanceSynthesizer.create(
                config=config, logger=logger
            )
        if topology == ImCircuitType.T:
            return TTypeDoubleCageImTotalImmittanceSynthesizer.create(
                config=config, logger=logger
            )
        raise ValueError(f"未対応の回路トポロジーです: {topology}")
