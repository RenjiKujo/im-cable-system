"""ケーブル電圧電流計算器のインターフェース定義。

本プロジェクトの IM cable system シミュレーションにおけるケーブル回路は
現状 **π 型（pie cable）に固定**されているため、IM 側のように
「モデル種別に応じて実装を切り替える」ファクトリークラスを必須にはしていません。

一方で、計算器自体は :class:`ICableVoltageCurrentCalculator` としてインターフェース化し、
オーケストレーター側は IF を保持します。これにより、将来ケーブル回路モデルが追加された場合
（例：T 型ケーブルや別の等価回路表現）でも、呼び出し側の依存を最小限にしたまま
実装の差し替え・拡張が可能です。
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexVoltageDto,
)
from im_cable_system.engine.shared.dto.itm import (
    ItmCableModelDto,
    ItmCableVoltageCurrentDto,
    ItmSystemModelDto,
)


class ICableVoltageCurrentCalculator(ABC):
    """ケーブル電圧電流計算器のインターフェース。

    ケーブルの各地点の電圧・電流を計算し、`ItmCableVoltageCurrentDto`を構築する処理の契約を定義します。
    """

    @classmethod
    @abstractmethod
    def create(
        cls, config: IConfig, logger: ILogger
    ) -> ICableVoltageCurrentCalculator:
        """ケーブル電圧電流計算器のインスタンスを生成するファクトリーメソッド。

        Args:
            config: 計算器生成に必要な設定。
            logger: ロガーオブジェクト。

        Returns:
            ICableVoltageCurrentCalculator: 生成された計算器インスタンス。
        """
        pass

    @abstractmethod
    def calculate(
        self,
        input_line_voltage: ArrayComplexVoltageDto,
        cable_model: ItmCableModelDto,
        system_model: ItmSystemModelDto,
    ) -> ItmCableVoltageCurrentDto:
        """ケーブル各地点の電圧・電流を計算し、`ItmCableVoltageCurrentDto`を構築する。

        入力線間電圧とケーブルモデル、システムモデルから、
        ケーブル各地点の電圧・電流を計算し、`ItmCableVoltageCurrentDto`を構築します。
        計算器内部で、入力線間電圧から相電圧への変換、およびシステムアドミタンスから
        入力相電流の計算を行います。

        Args:
            input_line_voltage: 入力線間電圧DTO
                （配列形状は`ItmModelDto.array_layout`で定義）。
            cable_model: ケーブルモデルDTO（`cable_immittance`を含む）。
            system_model: システムモデルDTO（`system_phase_impedance`, `system_phase_admittance`を含む）。

        Returns:
            ItmCableVoltageCurrentDto: ケーブル各地点の電圧・電流DTO
                （`input_line_voltage`, `input_line_current`, `input_phase_voltage`,
                `input_phase_current`, `conductor_*`, `ground_*`, `end_point_phase_*`を含む）。

        Raises:
            ValueError: 計算に失敗した場合。
        """
        pass
