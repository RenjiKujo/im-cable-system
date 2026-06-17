"""単一かご型IM電圧電流計算器実装。

このモジュールは、単一かご型IM（L型/T型等価回路）における各地点の
電圧・電流を計算する処理を提供します。
"""

from __future__ import annotations

from im_cable_system.engine.algorithm.execute_algorithm.simulate.voltage_current.calculate_im_voltage_current.i_im_voltage_current_calculator import (  # noqa: E501
    IImVoltageCurrentCalculator,
)
from im_cable_system.engine.domain.physics.electrical import (
    calculate_current_from_voltage_and_admittance,
    calculate_voltage_from_current_and_impedance,
    solve_kirchhoff_current,
    solve_kirchhoff_voltage,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ImCircuitType,
    ImSecondaryCageBranchType,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexCurrentDto,
    ArrayComplexVoltageDto,
)
from im_cable_system.engine.shared.dto.itm import (
    ItmImModelDto,
    ItmImVoltageCurrentDto,
)

_SECONDARY_BRANCH_SINGLE = ImSecondaryCageBranchType.SINGLE


class SingleCageImVoltageCurrentCalculator(IImVoltageCurrentCalculator):
    """単一かご型IM電圧電流計算器実装。

    単一かご型IM（L型/T型等価回路）における各地点の電圧・電流を計算します。
    T型/L型等価回路の違いは内部でif文により分離します。

    計算式: I = V / Z または I = V * Y

    NOTE: 二次電圧の退化時挙動（二重かご・L型/T型と統一の仕様）。
        二次電流は KCL（I2 = I1 - I_m）で求め、二次電圧降下はそれに Z を
        掛けて導出する。そのため二次がほぼ開放（Y2→0、スリップ依存で
        同期速度付近など）になる退化要素では二次電流が ≈0 となり、
        二次電圧（枝電圧）も ≈0 に潰れる。これは仕様であり、電流支配で
        二次電力も ≈0 となるため power 計算等への影響はほぼ無い。
    """

    def __init__(self, config: IConfig, logger: ILogger) -> None:
        """単一かご型IM電圧電流計算器のインスタンスを初期化する。

        Args:
            config: 計算器生成に必要な設定。
            logger: ロガーオブジェクト。
        """
        self._config: IConfig = config
        self._logger: ILogger = logger

    @classmethod
    def create(
        cls, config: IConfig, logger: ILogger
    ) -> IImVoltageCurrentCalculator:
        """単一かご型IM電圧電流計算器のインスタンスを生成するファクトリーメソッド。

        Args:
            config: 計算器生成に必要な設定。
            logger: ロガーオブジェクト。

        Returns:
            IImVoltageCurrentCalculator: 生成された計算器インスタンス。
        """
        return cls(config=config, logger=logger)

    def calculate(
        self,
        input_phase_voltage: ArrayComplexVoltageDto,
        input_phase_current: ArrayComplexCurrentDto,
        im_model: ItmImModelDto,
    ) -> ItmImVoltageCurrentDto:
        """IM各地点の電圧・電流を計算し、`ItmImVoltageCurrentDto`を構築する。

        ケーブル終点の相電圧・相電流とIMモデル情報から、IM各地点の電圧・電流を計算し、
        `ItmImVoltageCurrentDto`を構築します。
        T型/L型等価回路の違いは内部でif文により分離します。

        Args:
            input_phase_voltage: 入力相電圧DTO（ケーブル終点の相電圧、
                `ItmCableVoltageCurrentDto.end_point_phase_voltage`、
                配列形状は`ItmModelDto.array_layout`で定義）。
            input_phase_current: 入力相電流DTO（ケーブル終点の相電流、
                `ItmCableVoltageCurrentDto.end_point_phase_current`、
                配列形状は`ItmModelDto.array_layout`で定義）。
            im_model: IMモデルDTO（`ItmModelDto.im`、
                `primary_model`, `excitation_model`, `secondary_model`を含む）。

        Returns:
            ItmImVoltageCurrentDto: IM各地点の電圧・電流DTO
                （`im_input_*`, `im_primary_*`, `im_excitation_*`, `im_secondary_*`を含む）。

        Raises:
            ValueError: 計算に失敗した場合。
        """
        if not isinstance(im_model, ItmImModelDto):
            raise ValueError(
                f"im_modelはItmImModelDtoである必要があります: {type(im_model)}"
            )

        # T型/L型等価回路の違いを内部でif文により分離
        circuit_type = im_model.circuit_type
        if circuit_type == ImCircuitType.T:
            return self._calculate_t_circuit(
                input_phase_voltage=input_phase_voltage,
                input_phase_current=input_phase_current,
                im_model=im_model,
            )
        if circuit_type == ImCircuitType.L:
            return self._calculate_l_circuit(
                input_phase_voltage=input_phase_voltage,
                input_phase_current=input_phase_current,
                im_model=im_model,
            )
        raise ValueError(
            f"未対応の回路タイプです: {circuit_type}. "
            "サポートされるのは'T'または'L'です。"
        )

    def _calculate_l_circuit(
        self,
        input_phase_voltage: ArrayComplexVoltageDto,
        input_phase_current: ArrayComplexCurrentDto,
        im_model: ItmImModelDto,
    ) -> ItmImVoltageCurrentDto:
        """L型等価回路の電圧・電流を計算する。

        計算手順:
        1. 入力電圧と励磁アドミタンスから励磁枝電流を計算: I_m = V_in * Ym
        2. KCLにより直列枝電流を計算: I_series = I_in - I_m
        3. 直列枝電流と各インピーダンスから、一次・二次および
           二次ベース/ロードの電圧降下を計算
        4. 以上の結果から、全体・一次・励磁・二次ベース/ロード/合成および
           端子の各地点の電圧・電流DTOを構築して返す。
        """
        # 数値安定化しきい値はドメイン固有値ではなく config に統一する
        eps = self._config.numerical_guard_config.eps
        max_mag = 1.0 / eps

        # 励磁枝電流: I_m = V_in * Ym  # noqa: ERA001
        excitation_current = calculate_current_from_voltage_and_admittance(
            voltage=input_phase_voltage,
            admittance=im_model.excitation_admittance,
            eps=eps,
            max_mag=max_mag,
        )

        # 直列枝電流: I_series = I_in - I_m  # noqa: ERA001
        series_current = solve_kirchhoff_current(
            solve_for="remaining_downstream",
            upstream_currents=[input_phase_current],
            downstream_currents=[excitation_current],
            eps=eps,
            max_mag=max_mag,
        )

        sec = im_model.secondary_model
        sc = _SECONDARY_BRANCH_SINGLE
        # 一次側電圧 V1
        primary_voltage = calculate_voltage_from_current_and_impedance(
            current=series_current,
            impedance=im_model.primary_impedance,
            eps=eps,
            max_mag=max_mag,
        )

        # 二次側ベース電流・ロード電流（I_series を共有）
        secondary_base_voltage = calculate_voltage_from_current_and_impedance(
            current=series_current,
            impedance=sec.base_impedances[sc],
            eps=eps,
            max_mag=max_mag,
        )
        secondary_load_voltage = calculate_voltage_from_current_and_impedance(
            current=series_current,
            impedance=sec.load_impedances[sc],
            eps=eps,
            max_mag=max_mag,
        )

        return ItmImVoltageCurrentDto(
            im_input_voltage=input_phase_voltage,
            im_input_current=input_phase_current,
            im_primary_voltage=primary_voltage,
            im_primary_current=series_current,
            im_excitation_voltage=input_phase_voltage,
            im_excitation_current=excitation_current,
            cage_multiplicity=sec.cage_multiplicity,
            secondary_base_voltage={sc: secondary_base_voltage},
            secondary_load_voltage={sc: secondary_load_voltage},
            secondary_branch_current={sc: series_current},
        )

    def _calculate_t_circuit(
        self,
        input_phase_voltage: ArrayComplexVoltageDto,
        input_phase_current: ArrayComplexCurrentDto,
        im_model: ItmImModelDto,
    ) -> ItmImVoltageCurrentDto:
        """T型等価回路の電圧・電流を計算する。

        計算手順:
        1. 一次側電圧降下を計算: dV1 = I1 * Z1
        2. 励磁枝の両端電圧を計算: V_m = V_in - dV1
        3. 励磁電流を計算: I_m = V_m * Ym
        4. KCLにより二次側電流を計算: I2 = I1 - I_m
        5. 二次側ベース電圧降下を計算: dV2_base = I2 * Z2_base
        6. 二次側ロード電圧降下を計算: dV2_load = I2 * Z2_load
        7. 以上の結果から、全体・一次・励磁・二次ベース/ロード/合成の
           各地点の電圧・電流DTOを構築して返す。
        """
        # 数値安定化しきい値はドメイン固有値ではなく config に統一する
        eps = self._config.numerical_guard_config.eps
        max_mag = 1.0 / eps

        # 一次側電圧降下 dV1 = I1 * Z1
        primary_voltage_drop = calculate_voltage_from_current_and_impedance(
            current=input_phase_current,
            impedance=im_model.primary_impedance,
            eps=eps,
            max_mag=max_mag,
        )

        # 励磁電圧: V_m = V - dV1  # noqa: ERA001
        excitation_voltage = solve_kirchhoff_voltage(
            solve_for="remaining",
            total_voltage=input_phase_voltage,
            remaining_voltages=[primary_voltage_drop],
            eps=eps,
            max_mag=max_mag,
        )

        # 励磁電流: I_m = V_m * Ym  # noqa: ERA001
        excitation_current = calculate_current_from_voltage_and_admittance(
            voltage=excitation_voltage,
            admittance=im_model.excitation_admittance,
            eps=eps,
            max_mag=max_mag,
        )

        # 二次側電流: I2 = I1 - I_m  # noqa: ERA001
        secondary_current = solve_kirchhoff_current(
            solve_for="remaining_downstream",
            upstream_currents=[input_phase_current],
            downstream_currents=[excitation_current],
            eps=eps,
            max_mag=max_mag,
        )

        sec = im_model.secondary_model
        sc = _SECONDARY_BRANCH_SINGLE
        # 二次側ベース電圧降下: dV2_base = I2 * Z2_base  # noqa: ERA001
        secondary_base_voltage_drop = (
            calculate_voltage_from_current_and_impedance(
                current=secondary_current,
                impedance=sec.base_impedances[sc],
                eps=eps,
                max_mag=max_mag,
            )
        )

        # 二次側ロード電圧降下: dV2_load = I2 * Z2_load  # noqa: ERA001
        secondary_load_voltage_drop = (
            calculate_voltage_from_current_and_impedance(
                current=secondary_current,
                impedance=sec.load_impedances[sc],
                eps=eps,
                max_mag=max_mag,
            )
        )

        return ItmImVoltageCurrentDto(
            im_input_voltage=input_phase_voltage,
            im_input_current=input_phase_current,
            im_primary_voltage=primary_voltage_drop,
            im_primary_current=input_phase_current,
            im_excitation_voltage=excitation_voltage,
            im_excitation_current=excitation_current,
            cage_multiplicity=sec.cage_multiplicity,
            secondary_base_voltage={sc: secondary_base_voltage_drop},
            secondary_load_voltage={sc: secondary_load_voltage_drop},
            secondary_branch_current={sc: secondary_current},
        )
