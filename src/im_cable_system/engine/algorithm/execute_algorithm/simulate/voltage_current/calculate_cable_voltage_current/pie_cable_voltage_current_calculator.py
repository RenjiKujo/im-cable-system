"""π型ケーブル電圧電流計算器実装。

このモジュールは、π型ケーブル回路における各地点（上流、下流）の
電圧・電流を計算する処理を提供します。
"""

from __future__ import annotations

import numpy as np

from im_cable_system.engine.algorithm.execute_algorithm.simulate.voltage_current.calculate_cable_voltage_current.i_cable_voltage_current_calculator import (  # noqa: E501
    ICableVoltageCurrentCalculator,
)
from im_cable_system.engine.domain.physics.electrical import (
    calculate_current_from_voltage_and_admittance,
    calculate_voltage_from_current_and_impedance,
    line_to_phase_voltage_star_balanced,
    phase_to_line_current_star,
    solve_kirchhoff_current,
    solve_kirchhoff_voltage,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    PieCableConductorKey,
    PieCableGroundKey,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexCurrentDto,
    ArrayComplexVoltageDto,
)
from im_cable_system.engine.shared.dto.itm import (
    ItmCableImmittanceDto,
    ItmCableModelDto,
    ItmCableVoltageCurrentDto,
    ItmSystemModelDto,
)


class PieCableVoltageCurrentCalculator(ICableVoltageCurrentCalculator):
    """π型ケーブル電圧電流計算器実装。

    π型ケーブル回路における各地点（上流、下流）の電圧・電流を計算します。
    回路構成: [上流] --[Y_up]--[Z_c]--[Y_down]--[下流]

    計算手順:
    1. 上流地点: 入力電流・電圧
    2. 上流地絡電流: I_ground_up = V_up * Y_up
    3. 導線電流: I_conductor = I_in - I_ground_up
    4. 導線電圧: V_conductor = I_conductor * Z_c
    5. 下流地点電圧: V_down = V_up - V_conductor
    6. 下流地絡電流: I_ground_down = V_down * Y_down
    7. ケーブル端子電流: I_cable_end_point = I_conductor - I_ground_down

    NOTE: 特殊ケースの扱い。
        - 完全絶縁 (``is_ground_insulated``) と理想導体 (``is_conductor_ideal``)
          は、地絡電流 0・導線電圧降下 0 を厳密に出すため専用分岐を持つ。
        - 地絡 (``is_ground_shorted``) は専用分岐を持たない。build_model 側で
          地絡枝を有限大アドミタンス (``Y=1/eps``) として既に数値表現しているため、
          一般ケース (`_calculate_general`) の式にそのまま流せば短絡的挙動が
          得られる（0 ではなく有限近似のため一般式で表現できる）。
    """

    def __init__(self, config: IConfig, logger: ILogger) -> None:
        """π型ケーブル電圧電流計算器のインスタンスを初期化する。

        Args:
            config: 計算器生成に必要な設定。
            logger: ロガーオブジェクト。
        """
        self._config: IConfig = config
        self._logger: ILogger = logger

    @classmethod
    def create(
        cls, config: IConfig, logger: ILogger
    ) -> ICableVoltageCurrentCalculator:
        """π型ケーブル電圧電流計算器のインスタンスを生成するファクトリーメソッド。

        Args:
            config: 計算器生成に必要な設定。
            logger: ロガーオブジェクト。

        Returns:
            ICableVoltageCurrentCalculator: 生成された計算器インスタンス。
        """
        return cls(config=config, logger=logger)

    def calculate(
        self,
        input_line_voltage: ArrayComplexVoltageDto,
        cable_model: ItmCableModelDto,
        system_model: ItmSystemModelDto,
    ) -> ItmCableVoltageCurrentDto:
        """ケーブル各地点の電圧・電流を計算し、`ItmCableVoltageCurrentDto`を構築する。

        π型ケーブル回路における各地点（上流地絡、導線、下流地絡、
        ケーブル終端）の電圧・電流を計算します。
        ItmCableImmittanceDto に定義されたフラグ
        (完全絶縁・地絡・理想導体) に応じて、理想的な振る舞いに
        近づけた電圧・電流を計算します。

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
        if not isinstance(cable_model, ItmCableModelDto):
            raise ValueError(
                f"cable_modelはItmCableModelDtoである必要があります: "
                f"{type(cable_model)}"
            )
        if not isinstance(system_model, ItmSystemModelDto):
            raise ValueError(
                f"system_modelはItmSystemModelDtoである必要があります: "
                f"{type(system_model)}"
            )

        # 数値安定化しきい値はドメイン固有値ではなく config に統一する
        eps = self._config.numerical_guard_config.eps
        max_mag = 1.0 / eps

        # 1. 入力線間電圧から相電圧への変換（スター結線・balanced 規約）
        #    平衡 per-phase 規約のため大きさのみ 1/√3 にし、30° の位相回転は
        #    付与しない（線間電圧と相電圧は同位相）。規約の正本は
        #    ItmImVoltageCurrentDto のクラス docstring を参照。
        input_phase_voltage = line_to_phase_voltage_star_balanced(
            line_voltage_dto=input_line_voltage,
            eps=eps,
            max_mag=max_mag,
        )

        # 2. 入力相電流の計算: システムイミタンスから入力相電流を計算
        input_phase_current = calculate_current_from_voltage_and_admittance(
            voltage=input_phase_voltage,
            admittance=system_model.system_phase_admittance,
            eps=eps,
            max_mag=max_mag,
        )

        immittance = cable_model.cable_immittance

        # 3. 内部計算メソッドを呼び出して各地点の電圧・電流を取得
        if immittance.is_ground_insulated and immittance.is_conductor_ideal:
            (
                conductor_voltage,
                conductor_current,
                ground_voltage,
                ground_current,
                end_point_phase_voltage,
                end_point_phase_current,
            ) = self._calculate_for_insulated_ideal_conductor(
                input_phase_voltage=input_phase_voltage,
                input_phase_current=input_phase_current,
            )
        elif immittance.is_ground_insulated:
            (
                conductor_voltage,
                conductor_current,
                ground_voltage,
                ground_current,
                end_point_phase_voltage,
                end_point_phase_current,
            ) = self._calculate_for_insulated(
                input_phase_voltage=input_phase_voltage,
                input_phase_current=input_phase_current,
                immittance=immittance,
                eps=eps,
                max_mag=max_mag,
            )
        elif immittance.is_conductor_ideal:
            (
                conductor_voltage,
                conductor_current,
                ground_voltage,
                ground_current,
                end_point_phase_voltage,
                end_point_phase_current,
            ) = self._calculate_for_ideal_conductor(
                input_phase_voltage=input_phase_voltage,
                input_phase_current=input_phase_current,
                immittance=immittance,
                eps=eps,
                max_mag=max_mag,
            )
        else:
            (
                conductor_voltage,
                conductor_current,
                ground_voltage,
                ground_current,
                end_point_phase_voltage,
                end_point_phase_current,
            ) = self._calculate_general(
                input_phase_voltage=input_phase_voltage,
                input_phase_current=input_phase_current,
                immittance=immittance,
                eps=eps,
                max_mag=max_mag,
            )

        # 4. input_line_currentの計算: 相電流から線電流への変換
        input_line_current = phase_to_line_current_star(
            phase_current_dto=input_phase_current,
            eps=eps,
            max_mag=max_mag,
        )

        return ItmCableVoltageCurrentDto(
            input_line_voltage=input_line_voltage,
            input_line_current=input_line_current,
            input_phase_voltage=input_phase_voltage,
            input_phase_current=input_phase_current,
            conductor_voltage={PieCableConductorKey.SINGLE: conductor_voltage},
            conductor_current={PieCableConductorKey.SINGLE: conductor_current},
            ground_voltage=ground_voltage,
            ground_current=ground_current,
            end_point_phase_voltage=end_point_phase_voltage,
            end_point_phase_current=end_point_phase_current,
        )

    def _calculate_general(
        self,
        input_phase_voltage: ArrayComplexVoltageDto,
        input_phase_current: ArrayComplexCurrentDto,
        immittance: ItmCableImmittanceDto,
        eps: float,
        max_mag: float,
    ) -> tuple[
        ArrayComplexVoltageDto,  # conductor_voltage
        ArrayComplexCurrentDto,  # conductor_current
        dict[PieCableGroundKey, ArrayComplexVoltageDto],  # ground_voltage
        dict[PieCableGroundKey, ArrayComplexCurrentDto],  # ground_current
        ArrayComplexVoltageDto,  # end_point_phase_voltage
        ArrayComplexCurrentDto,  # end_point_phase_current
    ]:
        """一般ケースのケーブル各地点の電圧・電流を計算する。

        既存実装と同じく、π型回路の一般式で計算する。
        地絡 (``is_ground_shorted``) もこの一般式で扱う（build_model 側で
        地絡枝が ``Y=1/eps`` の有限大アドミタンスとして表現済みのため）。

        Args:
            input_phase_voltage: 入力相電圧DTO。
            input_phase_current: 入力相電流DTO。
            immittance: ケーブルイミタンスDTO。
            eps: 近接ゼロ判定のしきい値（設定由来）。
            max_mag: 最大の大きさ（設定由来、1/eps）。

        Returns:
            tuple: (conductor_voltage, conductor_current, ground_voltage,
                   ground_current, end_point_phase_voltage, end_point_phase_current)
        """
        ground_current_up = calculate_current_from_voltage_and_admittance(
            voltage=input_phase_voltage,
            admittance=immittance.ground_admittance[PieCableGroundKey.UPSTREAM],
            eps=eps,
            max_mag=max_mag,
        )

        conductor_current = solve_kirchhoff_current(
            solve_for="remaining_downstream",
            upstream_currents=[input_phase_current],
            downstream_currents=[ground_current_up],
            eps=eps,
            max_mag=max_mag,
        )

        conductor_voltage = calculate_voltage_from_current_and_impedance(
            current=conductor_current,
            impedance=immittance.conductor_impedance[
                PieCableConductorKey.SINGLE
            ],
            eps=eps,
            max_mag=max_mag,
        )

        downstream_voltage = solve_kirchhoff_voltage(
            solve_for="remaining",
            total_voltage=input_phase_voltage,
            remaining_voltages=[conductor_voltage],
            eps=eps,
            max_mag=max_mag,
        )

        ground_current_down = calculate_current_from_voltage_and_admittance(
            voltage=downstream_voltage,
            admittance=immittance.ground_admittance[
                PieCableGroundKey.DOWNSTREAM
            ],
            eps=eps,
            max_mag=max_mag,
        )

        cable_end_point_current = solve_kirchhoff_current(
            solve_for="remaining_downstream",
            upstream_currents=[conductor_current],
            downstream_currents=[ground_current_down],
            eps=eps,
            max_mag=max_mag,
        )

        return (
            conductor_voltage,
            conductor_current,
            {
                PieCableGroundKey.UPSTREAM: input_phase_voltage,
                PieCableGroundKey.DOWNSTREAM: downstream_voltage,
            },
            {
                PieCableGroundKey.UPSTREAM: ground_current_up,
                PieCableGroundKey.DOWNSTREAM: ground_current_down,
            },
            downstream_voltage,
            cable_end_point_current,
        )

    def _calculate_for_insulated(
        self,
        input_phase_voltage: ArrayComplexVoltageDto,
        input_phase_current: ArrayComplexCurrentDto,
        immittance: ItmCableImmittanceDto,
        eps: float,
        max_mag: float,
    ) -> tuple[
        ArrayComplexVoltageDto,  # conductor_voltage
        ArrayComplexCurrentDto,  # conductor_current
        dict[PieCableGroundKey, ArrayComplexVoltageDto],  # ground_voltage
        dict[PieCableGroundKey, ArrayComplexCurrentDto],  # ground_current
        ArrayComplexVoltageDto,  # end_point_phase_voltage
        ArrayComplexCurrentDto,  # end_point_phase_current
    ]:
        """完全絶縁ケースの電圧・電流を計算する。

        完全絶縁ではアースへの漏れ電流は理想的には 0 とみなす。
        そのため上流・下流地絡電流はゼロ配列とし、
        導線電流は常に入力電流と等しくなる。

        Args:
            input_phase_voltage: 入力相電圧DTO。
            input_phase_current: 入力相電流DTO。
            immittance: ケーブルイミタンスDTO。
            eps: 近接ゼロ判定のしきい値（設定由来）。
            max_mag: 最大の大きさ（設定由来、1/eps）。

        Returns:
            tuple: (conductor_voltage, conductor_current, ground_voltage,
                   ground_current, end_point_phase_voltage, end_point_phase_current)
        """
        zero_current = self._create_zero_current_like(input_phase_voltage)

        ground_current_up = zero_current

        conductor_current = input_phase_current

        conductor_voltage = calculate_voltage_from_current_and_impedance(
            current=conductor_current,
            impedance=immittance.conductor_impedance[
                PieCableConductorKey.SINGLE
            ],
            eps=eps,
            max_mag=max_mag,
        )

        downstream_voltage = solve_kirchhoff_voltage(
            solve_for="remaining",
            total_voltage=input_phase_voltage,
            remaining_voltages=[conductor_voltage],
            eps=eps,
            max_mag=max_mag,
        )

        ground_current_down = zero_current

        cable_end_point_current = conductor_current

        return (
            conductor_voltage,
            conductor_current,
            {
                PieCableGroundKey.UPSTREAM: input_phase_voltage,
                PieCableGroundKey.DOWNSTREAM: downstream_voltage,
            },
            {
                PieCableGroundKey.UPSTREAM: ground_current_up,
                PieCableGroundKey.DOWNSTREAM: ground_current_down,
            },
            downstream_voltage,
            cable_end_point_current,
        )

    def _calculate_for_ideal_conductor(
        self,
        input_phase_voltage: ArrayComplexVoltageDto,
        input_phase_current: ArrayComplexCurrentDto,
        immittance: ItmCableImmittanceDto,
        eps: float,
        max_mag: float,
    ) -> tuple[
        ArrayComplexVoltageDto,  # conductor_voltage
        ArrayComplexCurrentDto,  # conductor_current
        dict[PieCableGroundKey, ArrayComplexVoltageDto],  # ground_voltage
        dict[PieCableGroundKey, ArrayComplexCurrentDto],  # ground_current
        ArrayComplexVoltageDto,  # end_point_phase_voltage
        ArrayComplexCurrentDto,  # end_point_phase_current
    ]:
        """理想導体ケースの電圧・電流を計算する。

        理想導体では導線インピーダンスは 0 とみなし、
        導線電圧降下は常に 0、上流電圧と下流電圧は等しいとする。
        電流分配自体は一般ケースと同じKCL式に従う。

        Args:
            input_phase_voltage: 入力相電圧DTO。
            input_phase_current: 入力相電流DTO。
            immittance: ケーブルイミタンスDTO。
            eps: 近接ゼロ判定のしきい値（設定由来）。
            max_mag: 最大の大きさ（設定由来、1/eps）。

        Returns:
            tuple: (conductor_voltage, conductor_current, ground_voltage,
                   ground_current, end_point_phase_voltage, end_point_phase_current)
        """
        ground_current_up = calculate_current_from_voltage_and_admittance(
            voltage=input_phase_voltage,
            admittance=immittance.ground_admittance[PieCableGroundKey.UPSTREAM],
            eps=eps,
            max_mag=max_mag,
        )

        conductor_current = solve_kirchhoff_current(
            solve_for="remaining_downstream",
            upstream_currents=[input_phase_current],
            downstream_currents=[ground_current_up],
            eps=eps,
            max_mag=max_mag,
        )

        conductor_voltage = ArrayComplexVoltageDto(
            value=np.zeros_like(input_phase_voltage.get_value()),
            unit=input_phase_voltage.get_unit(),
        )

        downstream_voltage = input_phase_voltage

        ground_current_down = calculate_current_from_voltage_and_admittance(
            voltage=downstream_voltage,
            admittance=immittance.ground_admittance[
                PieCableGroundKey.DOWNSTREAM
            ],
            eps=eps,
            max_mag=max_mag,
        )

        cable_end_point_current = solve_kirchhoff_current(
            solve_for="remaining_downstream",
            upstream_currents=[conductor_current],
            downstream_currents=[ground_current_down],
            eps=eps,
            max_mag=max_mag,
        )

        return (
            conductor_voltage,
            conductor_current,
            {
                PieCableGroundKey.UPSTREAM: input_phase_voltage,
                PieCableGroundKey.DOWNSTREAM: downstream_voltage,
            },
            {
                PieCableGroundKey.UPSTREAM: ground_current_up,
                PieCableGroundKey.DOWNSTREAM: ground_current_down,
            },
            downstream_voltage,
            cable_end_point_current,
        )

    def _calculate_for_insulated_ideal_conductor(
        self,
        input_phase_voltage: ArrayComplexVoltageDto,
        input_phase_current: ArrayComplexCurrentDto,
    ) -> tuple[
        ArrayComplexVoltageDto,  # conductor_voltage
        ArrayComplexCurrentDto,  # conductor_current
        dict[PieCableGroundKey, ArrayComplexVoltageDto],  # ground_voltage
        dict[PieCableGroundKey, ArrayComplexCurrentDto],  # ground_current
        ArrayComplexVoltageDto,  # end_point_phase_voltage
        ArrayComplexCurrentDto,  # end_point_phase_current
    ]:
        """完全絶縁かつ理想導体ケースの電圧・電流を計算する。

        - 完全絶縁: 上流・下流ともアースへの漏れ電流は 0。
        - 理想導体: 導線インピーダンス 0、電圧降下 0（V_down = V_up）。

        よって:
        - ground_current_up = ground_current_down = 0
        - conductor_current = cable_end_point_current = upstream_current
        - conductor_voltage = 0
        - downstream_voltage = upstream_voltage

        Returns:
            tuple: (conductor_voltage, conductor_current, ground_voltage,
                   ground_current, end_point_phase_voltage, end_point_phase_current)
        """
        zero_current = self._create_zero_current_like(input_phase_voltage)

        ground_current_up = zero_current
        ground_current_down = zero_current

        conductor_current = input_phase_current

        conductor_voltage = ArrayComplexVoltageDto(
            value=np.zeros_like(input_phase_voltage.get_value()),
            unit=input_phase_voltage.get_unit(),
        )

        downstream_voltage = input_phase_voltage

        cable_end_point_current = input_phase_current

        return (
            conductor_voltage,
            conductor_current,
            {
                PieCableGroundKey.UPSTREAM: input_phase_voltage,
                PieCableGroundKey.DOWNSTREAM: downstream_voltage,
            },
            {
                PieCableGroundKey.UPSTREAM: ground_current_up,
                PieCableGroundKey.DOWNSTREAM: ground_current_down,
            },
            downstream_voltage,
            cable_end_point_current,
        )

    @staticmethod
    def _create_zero_current_like(
        voltage_dto: ArrayComplexVoltageDto,
    ) -> ArrayComplexCurrentDto:
        """電圧DTOと同じ形状のゼロ電流DTOを生成するヘルパー。"""
        zero_array = np.zeros_like(voltage_dto.get_value(), dtype=np.complex128)
        return ArrayComplexCurrentDto(value=zero_array, unit="A")
