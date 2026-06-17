"""IM ケーブルシステム全体実行オーケストレーターの Iteration 実装（forward）。

電流依存イミタンスがある場合に使用。同一 InputDto に対して
_build_model ↔ _simulate（電流電圧のみ）を繰り返し、設定された収束基準
（線電流・相電流・マージ後電流全体のいずれか）の相対変化が閾値未満となった
時点でモデルを確定する。反復上限・閾値・基準は
``calculation.execute.current_estimation.iteration``（``IConfig.current_estimation_config``）
で指定する。

確定後の ``_validate_itm_dto`` では電流・電圧レンジ検証を除き、
エネルギー保存・特性一貫性のみ検証する（スリップ格子全体では定格レンジを満たさない点があるため）。

設計メモ（``execute`` と ``execute_without_validation`` の関係）:
    本クラスでは ``execute`` を ``execute_without_validation`` のラッパーにせず、
    ``execute`` 側で「電流反復 → フル simulate → validate」を明示的に展開する。
    ``execute`` は本実装の正規ルートであり、ラッパー経由にすると
    「主要パス」と「最適化用パス」の主従が逆転して読みづらくなるため。

    一方 ``execute_without_validation`` は IF（:class:`IForwardExecutionOrchestrator`）
    の契約として保持する。``EstimateParams`` のパラメータ推定ループ
    （``scipy.optimize.least_squares`` の残差評価）で **高頻度に呼ばれるため
    検証コストを払いたくない** ケースに使う正規ルートである。
    Iteration 実装では「電流反復後にフル simulate を 1 回」という非自明な
    責務単位をこのメソッドにまとめている点が Direct と異なる。

設計メモ（設定値の検証は Config 側で済んでいる前提）:
    収束基準（``ConvergenceCriterion``）・収束失敗時重大度（``Severity``）の
    値域検証、``max_iterations`` / ``convergence_tolerance`` の正値検証は
    すべて :class:`Config` 構築時の ``ConfigSnapshotFactory`` で完了している。
    本クラスは attribute アクセスで値を受け取り、フォールバックや値域チェック
    を再実装しない。
"""

from __future__ import annotations

from dataclasses import replace

import numpy as np

from im_cable_system.engine.algorithm.execute_algorithm.build_model import (  # noqa: E501
    IImCableModelBuildOrchestrator,
)
from im_cable_system.engine.algorithm.execute_algorithm.build_model.orchestrate import (  # noqa: E501
    ImCableModelBuildOrchestrator,
)
from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.forward.i_forward_execution_orchestrator import (  # noqa: E501
    IForwardExecutionOrchestrator,
)
from im_cable_system.engine.algorithm.execute_algorithm.simulate import (  # noqa: E501
    ISimulationOrchestrator,
)
from im_cable_system.engine.algorithm.execute_algorithm.simulate.orchestrate import (  # noqa: E501
    SimulationOrchestrator,
    take_simulation_numerical_stability_report,
)
from im_cable_system.engine.algorithm.execute_algorithm.validate_itm_dto import (  # noqa: E501
    IItmValidationOrchestrator,
)
from im_cable_system.engine.algorithm.execute_algorithm.validate_itm_dto.orchestrate import (  # noqa: E501
    ItmValidationOrchestrator,
)
from im_cable_system.engine.shared.config import (
    ConvergenceCriterion,
    IConfig,
    ILogger,
    Severity,
    timer,
)
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ArrayKey,
    ArrayLayoutDto,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexCurrentDto,
)
from im_cable_system.engine.shared.dto.input import (
    InputDto,
)
from im_cable_system.engine.shared.dto.itm import (
    ItmDto,
)
from im_cable_system.engine.shared.numerical_stability import (
    numerical_stability_scope,
)

# 相対変化計算でゼロ割を避けるための分母下限
_RELATIVE_CHANGE_DENOM_FLOOR = 1.0e-12

# 反復収束状態: 単一配列（線電流・相電流）またはマージ電流のフラットキー別配列
ConvergenceState = np.ndarray | dict[str, np.ndarray]


class IterationForwardExecutionOrchestrator(IForwardExecutionOrchestrator):
    """電流依存イミタンス用の forward イテレーションオーケストレーター。

    同一 InputDto に対して _build_model → _simulate（電流電圧のみ）を繰り返し、
    設定（current_estimation.iteration）の収束基準を満たした時点で
    全計算 _simulate と _validate_itm_dto を実行して返す。
    初回は入力 DTO の array_layout をそのまま用いて build し、
    2回目以降は前回 simulate の全電流を array_layout に載せて build する。
    create / build_model / simulate / validate の実装は
    DirectForwardExecutionOrchestrator と同形同士。
    """

    def __init__(self, config: IConfig, logger: ILogger) -> None:
        """オーケストレーターを初期化する。"""
        self._config: IConfig = config
        self._logger: ILogger = logger

    @classmethod
    def create(
        cls,
        config: IConfig,
        logger: ILogger,
    ) -> IForwardExecutionOrchestrator:
        """config と logger を受け取り、自身のインスタンスを生成する。"""
        return cls(config=config, logger=logger)

    # NOTE: 小さい入力だとミリ秒未満になりログがノイズ化しやすいため、
    # 一定時間以上の処理のみタイマーを出力する。
    @timer(logger=None, line="#", min_duration=0.01)
    def execute(self, input_dto: InputDto) -> ItmDto:
        """1本の InputDto を処理する。build ↔ simulate を収束するまで繰り返す。

        本実装の正規ルート。``execute_without_validation`` を経由せず、
        ``_current_estimation_iterate → _simulate → _validate_itm_dto`` を
        直接展開する（理由はモジュール docstring「設計メモ」を参照）。
        """
        with numerical_stability_scope():
            itm_iterated = self._current_estimation_iterate(
                input_dto=input_dto,
                log_on_success=True,
            )
            itm_with_simulation = self._simulate(itm_iterated)
        self._validate_itm_dto(itm_with_simulation)
        return itm_with_simulation

    def execute_without_validation(self, input_dto: InputDto) -> ItmDto:
        """1本の InputDto を処理する。電流反復後にフル simulate のみ行い検証はしない。

        ``EstimateParams`` の残差評価ループのように、同一入力に対して高頻度に
        forward を呼び出す用途で、``_validate_itm_dto`` のコストを避けるための
        正規ルート。IF 契約として提供する（モジュール docstring「設計メモ」参照）。
        Direct と異なり、ここで実施する「電流反復後にフル simulate を 1 回」は
        Iteration 実装固有の非自明な責務単位となる。
        """
        with numerical_stability_scope():
            itm = self._current_estimation_iterate(
                input_dto=input_dto,
                log_on_success=True,
            )
            return self._simulate(itm)

    def _current_estimation_iterate(
        self,
        input_dto: InputDto,
        *,
        log_on_success: bool,
    ) -> ItmDto:
        """電流反復（VC only）を行い、ItmDto（simulation_result は VC のみ）を返す。"""
        iteration_config = self._config.current_estimation_config.iteration
        max_iter = iteration_config.max_iterations
        tol = iteration_config.convergence_tolerance
        criterion = iteration_config.convergence_criterion

        itm = self._build_model(input_dto)
        itm = self._simulate_voltage_current_only(itm)

        prev_state: ConvergenceState = self._extract_convergence_state(
            itm,
            criterion,
        )
        prev_for_diagnostic: ConvergenceState = prev_state
        solve_count = 1
        converged = False
        for _ in range(max_iter - 1):
            if itm.simulation_result is None:
                raise ValueError("simulation_result が None です。")

            voltage_current = itm.simulation_result.voltage_current
            cable_currents = voltage_current.cable_voltage_current.get_currents_for_array_layout()
            im_currents = voltage_current.im_voltage_current.get_currents_for_array_layout()
            merged_currents = {**cable_currents, **im_currents}

            next_input = self._merge_currents_into_layout(
                input_dto=input_dto,
                currents_dict=merged_currents,
            )

            itm = self._build_model(next_input)
            itm = self._simulate_voltage_current_only(itm)
            curr_state = self._extract_convergence_state(itm, criterion)
            solve_count += 1
            if self._convergence_states_converged(
                curr_state,
                prev_state,
                tol,
            ):
                converged = True
                break
            prev_for_diagnostic = prev_state
            prev_state = curr_state

        if not converged:
            self._handle_current_estimation_convergence_failure(
                input_name=str(input_dto.name),
                prev_convergence_state=prev_for_diagnostic,
                itm_dto=itm,
                current_solve_count=solve_count,
                max_iterations=max_iter,
                tolerance=tol,
                criterion=criterion,
            )
        elif log_on_success:
            self._logger.info(
                "電流反復が収束しました (input_name=%s, criterion=%s, "
                "iterations=%s)",
                input_dto.name,
                criterion.value,
                solve_count,
            )
        return itm

    def _build_model(self, input_dto: InputDto) -> ItmDto:
        """単一の入力 DTO から物理モデルを構築し、中間 DTO（simulation_result は未設定）を返す。

        Note:
            本メソッドは電流反復ループ内から毎回呼ばれ、その都度
            ``ImCableModelBuildOrchestrator`` を ``create`` する。構成
            インスタンスを反復間で使い回さないため一見無駄に見えるが、
            ``create`` および ``build`` 内の private メソッドによる
            ビルダー生成は属性セット中心の軽量処理であり（重い処理は
            ``build`` 内の数値計算側）、
            再生成コストは反復計算
            全体から見て誤差レベルに収まる。そのため構成の使い回しによる
            最適化は行わず、呼び出しの素直さ・コードの綺麗さを優先している。
        """
        build_orchestrator: IImCableModelBuildOrchestrator = (
            ImCableModelBuildOrchestrator.create(
                config=self._config,
                logger=self._logger,
            )
        )
        model_dto = build_orchestrator.build(input_dto)
        return ItmDto(
            name=input_dto.name,
            model=model_dto,
            simulation_result=None,
        )

    def _simulate(self, itm_dto: ItmDto) -> ItmDto:
        """単一の中間 DTO に対してシミュレーションを実行し、結果を付与した中間 DTO を返す。"""
        sim_orchestrator: ISimulationOrchestrator = (
            SimulationOrchestrator.create(
                config=self._config,
                logger=self._logger,
            )
        )
        simulation_dto = sim_orchestrator.calculate(model_dto=itm_dto.model)
        report = take_simulation_numerical_stability_report()
        return replace(
            itm_dto,
            simulation_result=simulation_dto,
            numerical_stability_report=report,
        )

    def _simulate_voltage_current_only(self, itm_dto: ItmDto) -> ItmDto:
        """電流電圧のみ計算し、結果を付与した中間 DTO を返す。

        電力・特性値計算・検証は行わない。反復中の収束判定には
        voltage_current のみ必要なため、計算時間短縮に用いる。

        Note:
            本メソッドは電流反復ループ内から毎回呼ばれ、その都度
            ``SimulationOrchestrator`` を ``create`` する。構成インスタンスを
            反復間で使い回さないため一見無駄に見えるが、``create`` および
            ``calculate_voltage_current_only`` 内の private メソッドによる
            計算器生成は属性セット中心の軽量処理であり
            （重い処理は同メソッド内の数値計算側）、
            再生成コストは反復計算全体から見て誤差レベルに収まる。
            そのため構成の使い回しによる最適化は行わず、呼び出しの素直さ・
            コードの綺麗さを優先している。
        """
        sim_orchestrator: ISimulationOrchestrator = (
            SimulationOrchestrator.create(
                config=self._config,
                logger=self._logger,
            )
        )
        simulation_dto = sim_orchestrator.calculate_voltage_current_only(
            model_dto=itm_dto.model
        )
        report = take_simulation_numerical_stability_report()
        return replace(
            itm_dto,
            simulation_result=simulation_dto,
            numerical_stability_report=report,
        )

    def _validate_itm_dto(self, itm_dto: ItmDto) -> None:
        """単一の中間 DTO の妥当性を検証する。"""
        validator: IItmValidationOrchestrator = (
            ItmValidationOrchestrator.create(
                config=self._config,
                logger=self._logger,
            )
        )
        validator.validate(itm_dto=itm_dto)

    def _merge_currents_into_layout(
        self,
        input_dto: InputDto,
        currents_dict: dict[ArrayKey, ArrayComplexCurrentDto],
    ) -> InputDto:
        """array_layout に電流 dict をマージした InputDto を返す。

        ``reference_axes`` には電流系キーが含まれない契約のため、本処理は
        実質的に電流 dict の全キーを ``array_layout.arrays`` に書き込む
        操作となる。``ref_axes_set`` に対するチェックは将来の契約変更や
        渡されたキー集合の取りこぼしを検知するための防御として残す。

        Returns:
            InputDto: ``array_layout`` の電流軸を更新したコピー。
        """
        new_arrays = dict(input_dto.array_layout.arrays)
        ref_axes_set = set(input_dto.array_layout.reference_axes)
        for key, dto in currents_dict.items():
            if key not in ref_axes_set:
                new_arrays[key] = dto
        new_layout = ArrayLayoutDto(
            arrays=new_arrays,
            reference_axes=input_dto.array_layout.reference_axes,
        )
        return InputDto(
            name=input_dto.name,
            array_layout=new_layout,
            im=input_dto.im,
            cable=input_dto.cable,
            im_pc_catalogs=input_dto.im_pc_catalogs,
        )

    def _extract_convergence_state(
        self,
        itm_dto: ItmDto,
        criterion: ConvergenceCriterion,
    ) -> ConvergenceState:
        """反復の収束判定に用いるスナップショットを itm から取り出す。"""
        if itm_dto.simulation_result is None:
            raise ValueError("simulation_result が None です。")
        vc = itm_dto.simulation_result.voltage_current
        if criterion is ConvergenceCriterion.LINE_CURRENT:
            return np.asarray(
                vc.cable_voltage_current.input_line_current.get_value(),
                dtype=np.complex128,
            )
        if criterion is ConvergenceCriterion.PHASE_CURRENT:
            return np.asarray(
                vc.cable_voltage_current.input_phase_current.get_value(),
                dtype=np.complex128,
            )
        # MAX_OVER_MERGED_CURRENTS
        merged = {
            **vc.cable_voltage_current.get_currents_for_array_layout(),
            **vc.im_voltage_current.get_currents_for_array_layout(),
        }
        return {
            key: np.asarray(dto.get_value(), dtype=np.complex128)
            for key, dto in merged.items()
        }

    def _convergence_states_converged(
        self,
        current: ConvergenceState,
        prev_current: ConvergenceState,
        tolerance: float,
    ) -> bool:
        """単一配列またはマージ電流辞書のペアが tolerance 基準で収束していれば True。"""
        if isinstance(prev_current, np.ndarray) and isinstance(
            current,
            np.ndarray,
        ):
            return self._arrays_converged(current, prev_current, tolerance)
        if isinstance(prev_current, dict) and isinstance(current, dict):
            if frozenset(prev_current.keys()) != frozenset(current.keys()):
                return False
            return all(
                self._arrays_converged(
                    current[key],
                    prev_current[key],
                    tolerance,
                )
                for key in sorted(prev_current.keys())
            )
        return False

    def _arrays_converged(
        self,
        current: np.ndarray,
        prev_current: np.ndarray,
        tolerance: float,
    ) -> bool:
        """2 複素配列の要素ごと相対変化がすべて tolerance 未満なら True。

        どちらかの要素数が 0 のときは比較なしで True（収束扱い）。
        """
        if current.size == 0 or prev_current.size == 0:
            return True
        if current.shape != prev_current.shape:
            return False
        return (
            self._compute_max_relative_change(prev_current, current) < tolerance
        )

    def _handle_current_estimation_convergence_failure(
        self,
        *,
        input_name: str,
        prev_convergence_state: ConvergenceState,
        itm_dto: ItmDto,
        current_solve_count: int,
        max_iterations: int,
        tolerance: float,
        criterion: ConvergenceCriterion,
    ) -> None:
        """電流反復が最大回数内で収束しなかった場合に設定に応じて例外・警告・ログで扱う。

        Args:
            input_name: 入力 DTO 名。
            prev_convergence_state: 最終比較の直前スナップショット（診断用）。
            itm_dto: 最終反復後の中間 DTO。
            current_solve_count: 実行した電流電圧計算（VC only）回数。
            max_iterations: 反復上限（初回 VC 含む）。
            tolerance: 相対変化の許容しきい値。
            criterion: 収束基準。

        Raises:
            ValueError: 重大度が ERROR の場合。
        """
        max_rel_change_str = ""
        if itm_dto.simulation_result is not None:
            curr_state = self._extract_convergence_state(itm_dto, criterion)
            max_rel_opt = self._max_relative_change_between_states(
                prev_convergence_state,
                curr_state,
            )
            if max_rel_opt is not None:
                max_rel_change_str = f", max_relative_change={max_rel_opt:.4e}"
        msg = (
            f"電流反復が最大回数({max_iterations})内で収束しませんでした "
            f"(criterion={criterion.value}, "
            f"current_solve_count={current_solve_count}, "
            f"max_current_solve_count={max_iterations}, "
            f"tolerance={tolerance:.2e}, "
            f"input_name={input_name}{max_rel_change_str})."
        )
        severity = (
            self._config.current_estimation_config.convergence_failure_severity
        )
        if severity is Severity.ERROR:
            raise ValueError(msg)
        if severity is Severity.WARNING:
            self._logger.warning("%s", msg)
            return
        # Severity.INFO
        self._logger.info("%s", msg)

    def _max_relative_change_between_states(
        self,
        prev: ConvergenceState,
        curr: ConvergenceState,
    ) -> float | None:
        """直前スナップショットと現在状態の最大相対変化（診断用）。比較不能時は None。"""
        if isinstance(prev, np.ndarray) and isinstance(curr, np.ndarray):
            return self._max_relative_change_arrays(prev, curr)
        if isinstance(prev, dict) and isinstance(curr, dict):
            if frozenset(prev.keys()) != frozenset(curr.keys()):
                return None
            values: list[float] = []
            for key in sorted(prev.keys()):
                arr_prev = prev[key]
                arr_curr = curr[key]
                if arr_prev.shape != arr_curr.shape:
                    return None
                if arr_prev.size == 0 or arr_curr.size == 0:
                    continue
                values.append(
                    self._compute_max_relative_change(arr_prev, arr_curr)
                )
            return max(values) if values else None
        return None

    def _max_relative_change_arrays(
        self,
        prev: np.ndarray,
        curr: np.ndarray,
    ) -> float | None:
        """2 配列の最大相対変化（診断用）。比較不能（shape 不一致・size 0）は None。"""
        if prev.shape != curr.shape or prev.size == 0 or curr.size == 0:
            return None
        return self._compute_max_relative_change(prev, curr)

    def _compute_max_relative_change(
        self,
        prev: np.ndarray,
        curr: np.ndarray,
    ) -> float:
        """2 配列の最大相対変化を計算するコアヘルパー。

        前提:
            ``prev.shape == curr.shape`` かつ ``prev.size > 0`` かつ
            ``curr.size > 0`` であること。前提を満たさない場合の判定は
            呼び出し側で行う。
        """
        denom = np.maximum(np.abs(prev), _RELATIVE_CHANGE_DENOM_FLOOR)
        return float(np.max(np.abs(curr - prev) / denom))
