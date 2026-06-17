"""二重かご型IM電圧電流計算器実装。

このモジュールは、二重かご型IM（cage_multiplicity = DOUBLE_CAGE）における
各地点の電圧・電流を計算する処理を提供します。
"""

from __future__ import annotations

from im_cable_system.engine.algorithm.execute_algorithm.simulate.voltage_current.calculate_im_voltage_current.i_im_voltage_current_calculator import (  # noqa: E501
    IImVoltageCurrentCalculator,
)
from im_cable_system.engine.domain.physics.electrical import (
    calculate_current_from_voltage_and_admittance,
    calculate_voltage_from_current_and_impedance,
    combine_admittance_parallel,
    impedance_from_admittance,
    solve_kirchhoff_current,
    solve_kirchhoff_voltage,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ImCircuitType,
    ImSecondaryCageBranchType,
    expected_branch_keys_for_cage_multiplicity,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexAdmittanceDto,
    ArrayComplexCurrentDto,
    ArrayComplexImpedanceDto,
    ArrayComplexVoltageDto,
)
from im_cable_system.engine.shared.dto.itm import (
    ItmImModelDto,
    ItmImSecondaryDto,
    ItmImVoltageCurrentDto,
)

_DOUBLE_CAGE_BRANCHES = frozenset(
    {
        ImSecondaryCageBranchType.INNER,
        ImSecondaryCageBranchType.OUTER,
    }
)


class DoubleCageImVoltageCurrentCalculator(IImVoltageCurrentCalculator):
    """二重かご型IM電圧電流計算器実装。

    二重かご型IMは、二次回路が INNER / OUTER の2枝の並列として表現される。
    `ItmImVoltageCurrentDto` の形式に合わせ、枝ごとの電圧降下・枝電流を
    INNER/OUTER の両方のキーで構築して返す。

    NOTE: 二次電圧の退化時挙動（単一かご・L型/T型と統一の仕様）。
        二次合計電流は KCL（I2 = I1 - I_m）で求め、ノード電圧はそれを
        並列等価インピーダンスで戻して導出する。そのため二次がほぼ開放
        （Y2→0、スリップ依存で同期速度付近など）になる退化要素では
        二次電流が ≈0 となり、二次ノード電圧（枝電圧）も ≈0 に潰れる。
        これは仕様であり、整合領域では KCL 導出とオーム則導出
        （I2 = V_m·(Y_inner+Y_outer)）が一致する。退化時は電流支配で
        二次電力も ≈0 となるため、power 計算等への影響はほぼ無い。
    """

    def __init__(self, config: IConfig, logger: ILogger) -> None:
        """二重かご型IM電圧電流計算器のインスタンスを初期化する。

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
        """二重かご型IM電圧電流計算器のインスタンスを生成するファクトリーメソッド。

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

        Args:
            input_phase_voltage: 入力相電圧DTO。
            input_phase_current: 入力相電流DTO。
            im_model: IMモデルDTO。

        Returns:
            ItmImVoltageCurrentDto: IM各地点の電圧・電流DTO。

        Raises:
            ValueError: 計算に失敗した場合。
        """
        if not isinstance(im_model, ItmImModelDto):
            raise ValueError(
                f"im_modelはItmImModelDtoである必要があります: {type(im_model)}"
            )

        self._validate_secondary_branch_keys(im_model=im_model)

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

    def _validate_secondary_branch_keys(self, im_model: ItmImModelDto) -> None:
        """二重かご計算で参照する二次側辞書のキー集合を検証する。

        本計算器は INNER/OUTER の両枝が揃っていることを前提に、
        ``admittances`` / ``base_impedances`` / ``load_impedances`` を参照する。
        いずれかの辞書でキーが欠落していると ``KeyError`` で計算が中断するため、
        事前にどの辞書が不正かを明示した ``ValueError`` を送出する。

        Raises:
            ValueError: 二重かご以外、または参照対象辞書のキーが
                INNER/OUTER の集合と一致しない場合。
        """
        sec = im_model.secondary_model
        expected = expected_branch_keys_for_cage_multiplicity(
            sec.cage_multiplicity
        )
        if expected != _DOUBLE_CAGE_BRANCHES:
            raise ValueError(
                "DoubleCageImVoltageCurrentCalculator は二重かご専用です。"
                f" cage_multiplicity={sec.cage_multiplicity!s}"
            )
        for label, branch_map in (
            ("impedances", sec.impedances),
            ("admittances", sec.admittances),
            ("base_impedances", sec.base_impedances),
            ("load_impedances", sec.load_impedances),
        ):
            keys = frozenset(branch_map.keys())
            if keys != _DOUBLE_CAGE_BRANCHES:
                raise ValueError(
                    f"二重かごの二次側モデル辞書 {label} のキーが不正です。"
                    f" 期待={sorted(b.value for b in _DOUBLE_CAGE_BRANCHES)},"
                    f" 実際={sorted(b.value for b in keys)}"
                )

    def _calculate_parallel_equivalent_impedance(
        self,
        inner_admittance: ArrayComplexAdmittanceDto,
        outer_admittance: ArrayComplexAdmittanceDto,
        eps: float,
        max_mag: float,
    ) -> ArrayComplexImpedanceDto:
        """INNER/OUTER 枝アドミタンスから並列合成インピーダンスを導出する。"""
        total_admittance = combine_admittance_parallel(
            admittance1=inner_admittance,
            admittance2=outer_admittance,
            eps=eps,
            max_mag=max_mag,
        )
        return impedance_from_admittance(
            admittance=total_admittance,
            eps=eps,
            max_mag=max_mag,
        )

    def _build_secondary_branch_quantities(
        self,
        secondary_node_voltage: ArrayComplexVoltageDto,
        secondary_model: ItmImSecondaryDto,
        eps: float,
        max_mag: float,
    ) -> tuple[
        dict[ImSecondaryCageBranchType, ArrayComplexCurrentDto],
        dict[ImSecondaryCageBranchType, ArrayComplexVoltageDto],
        dict[ImSecondaryCageBranchType, ArrayComplexVoltageDto],
    ]:
        """二次側ノード電圧から枝電流・基本/負荷電圧降下を枝ごとに構築する。

        L 型・T 型で共通の計算（枝電流 = ノード電圧 × 枝アドミタンス、
        各電圧降下 = 枝電流 × 各インピーダンス）をまとめ、両回路で
        二次側計算ロジックの対称性を保つ。回路差は「二次並列ブロックに
        印加されるノード電圧」をどう作るかだけに集約する。

        Args:
            secondary_node_voltage: 二次並列ブロックに印加されるノード電圧。
                L 型では二次直列ブロック電圧、T 型では励磁ノード電圧。
            secondary_model: 二次側モデルDTO（枝ごとのアドミタンス・インピーダンス）。
            eps: 近接ゼロ判定のしきい値（設定由来）。
            max_mag: 最大の大きさ（設定由来、1/eps）。

        Returns:
            tuple: (枝電流, 基本電圧降下, 負荷電圧降下) の枝キー辞書の組。
        """
        branch_current: dict[
            ImSecondaryCageBranchType, ArrayComplexCurrentDto
        ] = {}
        base_voltage: dict[
            ImSecondaryCageBranchType, ArrayComplexVoltageDto
        ] = {}
        load_voltage: dict[
            ImSecondaryCageBranchType, ArrayComplexVoltageDto
        ] = {}
        for branch in (
            ImSecondaryCageBranchType.INNER,
            ImSecondaryCageBranchType.OUTER,
        ):
            current = calculate_current_from_voltage_and_admittance(
                voltage=secondary_node_voltage,
                admittance=secondary_model.admittances[branch],
                eps=eps,
                max_mag=max_mag,
            )
            branch_current[branch] = current
            base_voltage[branch] = calculate_voltage_from_current_and_impedance(
                current=current,
                impedance=secondary_model.base_impedances[branch],
                eps=eps,
                max_mag=max_mag,
            )
            load_voltage[branch] = calculate_voltage_from_current_and_impedance(
                current=current,
                impedance=secondary_model.load_impedances[branch],
                eps=eps,
                max_mag=max_mag,
            )
        return branch_current, base_voltage, load_voltage

    def _calculate_l_circuit(
        self,
        input_phase_voltage: ArrayComplexVoltageDto,
        input_phase_current: ArrayComplexCurrentDto,
        im_model: ItmImModelDto,
    ) -> ItmImVoltageCurrentDto:
        """L型等価回路（一次+二次直列、励磁並列）で二重かごの電圧・電流を計算する。"""
        # 数値安定化しきい値はドメイン固有値ではなく config に統一する
        eps = self._config.numerical_guard_config.eps
        max_mag = 1.0 / eps

        excitation_current = calculate_current_from_voltage_and_admittance(
            voltage=input_phase_voltage,
            admittance=im_model.excitation_admittance,
            eps=eps,
            max_mag=max_mag,
        )
        secondary_total_current = solve_kirchhoff_current(
            solve_for="remaining_downstream",
            upstream_currents=[input_phase_current],
            downstream_currents=[excitation_current],
            eps=eps,
            max_mag=max_mag,
        )

        sec = im_model.secondary_model
        z_secondary_eq = self._calculate_parallel_equivalent_impedance(
            inner_admittance=sec.admittances[ImSecondaryCageBranchType.INNER],
            outer_admittance=sec.admittances[ImSecondaryCageBranchType.OUTER],
            eps=eps,
            max_mag=max_mag,
        )

        primary_voltage = calculate_voltage_from_current_and_impedance(
            current=secondary_total_current,
            impedance=im_model.primary_impedance,
            eps=eps,
            max_mag=max_mag,
        )
        # L 型では二次直列ブロックに印加される電圧がノード電圧となる
        secondary_node_voltage = calculate_voltage_from_current_and_impedance(
            current=secondary_total_current,
            impedance=z_secondary_eq,
            eps=eps,
            max_mag=max_mag,
        )

        branch_current, secondary_base_voltage, secondary_load_voltage = (
            self._build_secondary_branch_quantities(
                secondary_node_voltage=secondary_node_voltage,
                secondary_model=sec,
                eps=eps,
                max_mag=max_mag,
            )
        )

        return ItmImVoltageCurrentDto(
            im_input_voltage=input_phase_voltage,
            im_input_current=input_phase_current,
            im_primary_voltage=primary_voltage,
            im_primary_current=secondary_total_current,
            im_excitation_voltage=input_phase_voltage,
            im_excitation_current=excitation_current,
            cage_multiplicity=sec.cage_multiplicity,
            secondary_base_voltage=secondary_base_voltage,
            secondary_load_voltage=secondary_load_voltage,
            secondary_branch_current=branch_current,
        )

    def _calculate_t_circuit(
        self,
        input_phase_voltage: ArrayComplexVoltageDto,
        input_phase_current: ArrayComplexCurrentDto,
        im_model: ItmImModelDto,
    ) -> ItmImVoltageCurrentDto:
        """T型等価回路（一次直列、励磁+二次並列）で二重かごの電圧・電流を計算する。

        二次合計電流は単一かご T 型と同じく KCL で直接求める（I2 = I1 - I_m）。
        枝分配は L 型と対称に、並列等価インピーダンスでノード電圧へ戻してから
        各枝アドミタンスへ配分する（``sum(branch) == 二次合計電流`` を保証する）。
        """
        # 数値安定化しきい値はドメイン固有値ではなく config に統一する
        eps = self._config.numerical_guard_config.eps
        max_mag = 1.0 / eps

        primary_voltage_drop = calculate_voltage_from_current_and_impedance(
            current=input_phase_current,
            impedance=im_model.primary_impedance,
            eps=eps,
            max_mag=max_mag,
        )
        excitation_voltage = solve_kirchhoff_voltage(
            solve_for="remaining",
            total_voltage=input_phase_voltage,
            remaining_voltages=[primary_voltage_drop],
            eps=eps,
            max_mag=max_mag,
        )
        excitation_current = calculate_current_from_voltage_and_admittance(
            voltage=excitation_voltage,
            admittance=im_model.excitation_admittance,
            eps=eps,
            max_mag=max_mag,
        )

        # 二次合計電流を KCL で直接求める（I2 = I1 - I_m）
        secondary_total_current = solve_kirchhoff_current(
            solve_for="remaining_downstream",
            upstream_currents=[input_phase_current],
            downstream_currents=[excitation_current],
            eps=eps,
            max_mag=max_mag,
        )

        sec = im_model.secondary_model
        # KCL で得た二次合計電流を並列等価インピーダンスでノード電圧へ戻し、
        # L 型と対称な枝分配を行う。
        z_secondary_eq = self._calculate_parallel_equivalent_impedance(
            inner_admittance=sec.admittances[ImSecondaryCageBranchType.INNER],
            outer_admittance=sec.admittances[ImSecondaryCageBranchType.OUTER],
            eps=eps,
            max_mag=max_mag,
        )
        secondary_node_voltage = calculate_voltage_from_current_and_impedance(
            current=secondary_total_current,
            impedance=z_secondary_eq,
            eps=eps,
            max_mag=max_mag,
        )
        branch_current, secondary_base_voltage, secondary_load_voltage = (
            self._build_secondary_branch_quantities(
                secondary_node_voltage=secondary_node_voltage,
                secondary_model=sec,
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
            secondary_base_voltage=secondary_base_voltage,
            secondary_load_voltage=secondary_load_voltage,
            secondary_branch_current=branch_current,
        )
