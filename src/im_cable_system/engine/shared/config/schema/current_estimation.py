"""``calculation.execute.current_estimation`` セクションのスキーマと factory。

電流依存イミタンスの反復解法（forward の Iteration 経路）で参照される
設定。max_iterations / convergence_tolerance / convergence_criterion /
convergence_failure_severity を保持する。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from im_cable_system.engine.shared.config.schema._parsers import (
    parse_dict,
    parse_enum,
    parse_float,
    parse_int,
)
from im_cable_system.engine.shared.config.schema.severity import Severity


class ConvergenceCriterion(str, Enum):
    """電流反復の収束判定基準。"""

    LINE_CURRENT = "line_current"
    PHASE_CURRENT = "phase_current"
    MAX_OVER_MERGED_CURRENTS = "max_over_merged_currents"


_DEFAULT_MAX_ITERATIONS = 20
_DEFAULT_CONVERGENCE_TOLERANCE = 1.0e-6


@dataclass(frozen=True)
class CurrentEstimationIterationConfig:
    """電流反復の停止条件と上限。"""

    max_iterations: int
    convergence_tolerance: float
    convergence_criterion: ConvergenceCriterion


@dataclass(frozen=True)
class CurrentEstimationConfig:
    """電流反復解法セクション全体。"""

    convergence_failure_severity: Severity
    iteration: CurrentEstimationIterationConfig


class _IterationFactory:
    """``iteration`` サブブロック factory。"""

    @staticmethod
    def create(raw: Any) -> CurrentEstimationIterationConfig:
        block = parse_dict(
            raw,
            key_path="calculation.execute.current_estimation.iteration",
        )
        return CurrentEstimationIterationConfig(
            max_iterations=parse_int(
                block.get("max_iterations"),
                key_path=(
                    "calculation.execute.current_estimation.iteration."
                    "max_iterations"
                ),
                default=_DEFAULT_MAX_ITERATIONS,
                positive=True,
            ),
            convergence_tolerance=parse_float(
                block.get("convergence_tolerance"),
                key_path=(
                    "calculation.execute.current_estimation.iteration."
                    "convergence_tolerance"
                ),
                default=_DEFAULT_CONVERGENCE_TOLERANCE,
                positive=True,
            ),
            convergence_criterion=parse_enum(
                block.get("convergence_criterion"),
                ConvergenceCriterion,
                key_path=(
                    "calculation.execute.current_estimation.iteration."
                    "convergence_criterion"
                ),
                default=ConvergenceCriterion.LINE_CURRENT,
            ),
        )


class CurrentEstimationConfigFactory:
    """``calculation.execute.current_estimation`` を dataclass に変換する。"""

    @staticmethod
    def create(raw: Any) -> CurrentEstimationConfig:
        """YAML 由来の dict から :class:`CurrentEstimationConfig` を組み立てる。

        Args:
            raw: ``calculation.execute.current_estimation`` の生 dict（``None`` 可）。

        Returns:
            CurrentEstimationConfig: 補完・検証済みの dataclass。

        Raises:
            ValueError: dict 以外、または各値の制約違反。
        """
        block = parse_dict(
            raw,
            key_path="calculation.execute.current_estimation",
        )
        return CurrentEstimationConfig(
            convergence_failure_severity=parse_enum(
                block.get("convergence_failure_severity"),
                Severity,
                key_path=(
                    "calculation.execute.current_estimation."
                    "convergence_failure_severity"
                ),
                default=Severity.WARNING,
            ),
            iteration=_IterationFactory.create(block.get("iteration")),
        )
