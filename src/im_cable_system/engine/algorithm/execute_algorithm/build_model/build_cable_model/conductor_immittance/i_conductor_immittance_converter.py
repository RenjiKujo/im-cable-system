"""導線イミタンス計算ストラテジーのインターフェース定義

OCPの原則に従い、表皮効果などの
異なる計算方法を拡張可能にするためのインターフェース。
"""

from __future__ import annotations

from abc import ABC, abstractmethod

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


class IConductorImmittanceConverter(ABC):
    """導線イミタンス計算のコンバーターインターフェース

    導線回路モデルと基準インピーダンス、およびオプションの周波数・電流を受け取り、
    1 区間の有効導線インピーダンスを計算する。

    生成時の契約:
        実装は ``create(config, logger)`` を通じて生成し、``IConfig`` と
        ``ILogger`` を保持すること。
    """

    @classmethod
    @abstractmethod
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
            IConductorImmittanceConverter: 導線イミタンス計算コンバーター。
        """
        pass

    @abstractmethod
    def convert(
        self,
        conductor_model: CableConductorModelDto,
        base_resistance_total: FloatResistanceDto,
        base_inductance_total: FloatInductanceDto,
        frequency: ArrayFrequencyDto | None = None,
        conductor_current: ArrayComplexCurrentDto | None = None,
    ) -> ArrayComplexImpedanceDto:
        """導線インピーダンスを計算する

        Args:
            conductor_model: 導線回路モデルDTO（モデルタイプとパラメータを含む）
            base_resistance_total: 区間全体の基準抵抗 [Ω]。
                例: 抵抗線密度 × 区間長で計算された R0。
            base_inductance_total: 区間全体の基準インダクタンス [H]。
                例: インダクタンス線密度 × 区間長で計算された L0。
            frequency: 周波数DTO（必要に応じて使用）。周波数依存・電流依存モデルでは必須。
            conductor_current: 導体電流DTO（必要に応じて使用）。電流依存モデルで参照する。
                未指定（None）の場合は周波数と同じ形状のゼロ電流として扱ってよい
                （初回ビルド・電流未設定時）。

        Returns:
            ArrayComplexImpedanceDto: 導線インピーダンスDTO（区間の有効インピーダンス）

        Note:
            ドメイン層計算・クランプ処理には
            ``config.numerical_guard_config.eps`` と ``max_mag = 1 / eps`` を用い、
            ドメイン関数の既定値に依存しないこと。
        """
        pass
