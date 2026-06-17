"""電流電圧計算オーケストレーター実装。

このモジュールは、IM＋ケーブル系シミュレーションにおける電流電圧計算を
統括するオーケストレーターの実装を提供します。
"""

from __future__ import annotations

from im_cable_system.engine.algorithm.execute_algorithm.simulate.voltage_current.calculate_cable_voltage_current import (  # noqa: E501
    PieCableVoltageCurrentCalculator,
)
from im_cable_system.engine.algorithm.execute_algorithm.simulate.voltage_current.calculate_im_voltage_current import (  # noqa: E501
    ImVoltageCurrentCalculatorFactory,
)
from im_cable_system.engine.algorithm.execute_algorithm.simulate.voltage_current.i_voltage_current_calculation_orchestrator import (  # noqa: E501
    IVoltageCurrentCalculationOrchestrator,
)
from im_cable_system.engine.domain.numerics import (
    create_extended_arrays,
)
from im_cable_system.engine.shared.config import IConfig, ILogger, timer
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ArrayKey,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexVoltageDto,
)
from im_cable_system.engine.shared.dto.itm import (
    ItmCableVoltageCurrentDto,
    ItmImVoltageCurrentDto,
    ItmModelDto,
    ItmVoltageCurrentDto,
)


class VoltageCurrentCalculationOrchestrator(
    IVoltageCurrentCalculationOrchestrator
):
    """電流電圧計算オーケストレーター実装。

    各地点の電流電圧計算を統括します。
    """

    def __init__(
        self,
        config: IConfig,
        logger: ILogger,
    ) -> None:
        """電流電圧計算オーケストレーターのインスタンスを初期化する。

        Args:
            config: オーケストレーター生成に必要な設定。
            logger: ロガーオブジェクト。
        """
        self._config: IConfig = config
        self._logger: ILogger = logger

    @classmethod
    def create(
        cls, config: IConfig, logger: ILogger
    ) -> IVoltageCurrentCalculationOrchestrator:
        """電流電圧計算オーケストレーターのインスタンスを生成する。

        Args:
            config: オーケストレーター生成に必要な設定。
            logger: ロガーオブジェクト。

        Returns:
            IVoltageCurrentCalculationOrchestrator:
                生成されたオーケストレーターインスタンス。
        """
        return cls(config=config, logger=logger)

    # NOTE: 小さい入力だとミリ秒未満になりログがノイズ化しやすいため、
    # 一定時間以上の処理のみタイマーを出力する。
    @timer(logger=None, line="#", min_duration=0.01)
    def calculate(
        self,
        model_dto: ItmModelDto,
    ) -> ItmVoltageCurrentDto:
        """各地点の電流電圧を計算する。

        入力電流計算、ケーブル各地点の電流電圧計算、誘導電動機各地点の
        電流電圧計算を順次実行し、全ての結果を統合します。

        Args:
            model_dto: モデルDTO（`array_layout`, `im`, `cable`, `system`を含む）。

        Returns:
            ItmVoltageCurrentDto: 電圧・電流シミュレーション結果DTO。

        Raises:
            ValueError: 計算に失敗した場合。
        """
        cable_voltage_current = self._calculate_cable_voltage_current(
            model_dto=model_dto,
        )
        im_voltage_current = self._calculate_im_voltage_current(
            model_dto=model_dto,
            cable_voltage_current=cable_voltage_current,
        )
        return ItmVoltageCurrentDto(
            im_voltage_current=im_voltage_current,
            cable_voltage_current=cable_voltage_current,
        )

    def _calculate_cable_voltage_current(
        self,
        model_dto: ItmModelDto,
    ) -> ItmCableVoltageCurrentDto:
        """ケーブル各地点の電流電圧を計算する。"""
        array_layout = model_dto.array_layout

        # 入力線間電圧の取得とブロードキャスト
        input_line_voltage_key = ArrayKey.INPUT_LINE_VOLTAGE
        line_voltage_dto = array_layout.arrays[input_line_voltage_key]
        if not isinstance(line_voltage_dto, ArrayComplexVoltageDto):
            raise ValueError(
                f"array_layout.arrays['{input_line_voltage_key}']はArrayComplexVoltageDtoである必要があります。"
                f"実際の型: {type(line_voltage_dto)}"
            )
        extended_arrays = create_extended_arrays(array_layout=array_layout)
        input_line_voltage = ArrayComplexVoltageDto(
            value=extended_arrays[input_line_voltage_key],
            unit=line_voltage_dto.get_unit(),
        ).to_base_unit()

        # ケーブル計算器を生成（常に π 型）して計算
        cable_calculator = PieCableVoltageCurrentCalculator.create(
            config=self._config,
            logger=self._logger,
        )
        return cable_calculator.calculate(
            input_line_voltage=input_line_voltage,
            cable_model=model_dto.cable,
            system_model=model_dto.system,
        )

    def _calculate_im_voltage_current(
        self,
        model_dto: ItmModelDto,
        cable_voltage_current: ItmCableVoltageCurrentDto,
    ) -> ItmImVoltageCurrentDto:
        """誘導電動機各地点の電流電圧を計算する。"""
        # IM計算器を生成（かごの重数に基づく）
        #
        # build_model により各ノードのイミタンス（配列）は確定しているため、
        # 電圧・電流計算器の分岐軸は model type ではなく cage_multiplicity とする。
        cage_multiplicity = model_dto.im.secondary_model.cage_multiplicity
        im_calculator = ImVoltageCurrentCalculatorFactory.create(
            cage_multiplicity=cage_multiplicity,
            config=self._config,
            logger=self._logger,
        )
        return im_calculator.calculate(
            input_phase_voltage=cable_voltage_current.end_point_phase_voltage,
            input_phase_current=cable_voltage_current.end_point_phase_current,
            im_model=model_dto.im,
        )
