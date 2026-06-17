"""``calculation.execute.estimate_params`` セクションのスキーマと factory。

residual（重み・正規化）と optimizer（least_squares パラメータ）を保持する。
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

_DEFAULT_RESIDUAL_WEIGHT = 1.0
_DEFAULT_NORMALIZATION_EPS = 1.0e-12
_DEFAULT_OPTIMIZER_MAX_NFEV = 100
_DEFAULT_OPTIMIZER_TOL = 1.0e-8


class ResidualNormalizationMethod(str, Enum):
    """残差正規化方式。"""

    BY_CURVE_SCALE = "by_curve_scale"
    BY_REFERENCE = "by_reference"
    NONE = "none"


class ResidualNormalizationStatistic(str, Enum):
    """残差正規化に用いる代表統計量。"""

    MAX = "max"
    MEAN = "mean"
    P95 = "p95"
    STD = "std"


class OptimizerAlgorithm(str, Enum):
    """最適化アルゴリズム。"""

    LEAST_SQUARES = "least_squares"


@dataclass(frozen=True)
class ResidualWeightsConfig:
    """残差重み（current=|I|, power, power_factor, efficiency）。"""

    current: float
    power: float
    power_factor: float
    efficiency: float


@dataclass(frozen=True)
class ResidualNormalizationConfig:
    """残差正規化設定。

    named-nested YAML では ``method`` が選択子、同名ブロック
    （例: ``by_curve_scale``）が詳細設定を保持する。strategy 側では本
    dataclass の ``method`` / ``statistic`` / ``eps`` だけを参照する。
    """

    method: ResidualNormalizationMethod
    statistic: ResidualNormalizationStatistic
    eps: float


@dataclass(frozen=True)
class ResidualConfig:
    """残差ブロック全体。"""

    weights: ResidualWeightsConfig
    normalization: ResidualNormalizationConfig


@dataclass(frozen=True)
class LeastSquaresOptimizerConfig:
    """最適化器設定（``scipy.optimize.least_squares`` に渡す）。"""

    max_nfev: int
    ftol: float
    xtol: float
    gtol: float


@dataclass(frozen=True)
class OptimizerConfig:
    """最適化器選択と、選択先ごとの詳細設定。"""

    algorithm: OptimizerAlgorithm
    least_squares: LeastSquaresOptimizerConfig

    @property
    def max_nfev(self) -> int:
        """least_squares の最大評価回数（既存呼び出し互換用）。"""
        return self.least_squares.max_nfev

    @property
    def ftol(self) -> float:
        """least_squares の ftol（既存呼び出し互換用）。"""
        return self.least_squares.ftol

    @property
    def xtol(self) -> float:
        """least_squares の xtol（既存呼び出し互換用）。"""
        return self.least_squares.xtol

    @property
    def gtol(self) -> float:
        """least_squares の gtol（既存呼び出し互換用）。"""
        return self.least_squares.gtol


@dataclass(frozen=True)
class EstimateParamsConfig:
    """estimate_params セクション全体。"""

    residual: ResidualConfig
    optimizer: OptimizerConfig


class _ResidualWeightsFactory:
    """``residual.weights`` サブブロック factory。"""

    @staticmethod
    def create(raw: Any) -> ResidualWeightsConfig:
        block = parse_dict(
            raw,
            key_path="calculation.execute.estimate_params.residual.weights",
        )
        return ResidualWeightsConfig(
            current=parse_float(
                block.get("current"),
                key_path=(
                    "calculation.execute.estimate_params.residual.weights."
                    "current"
                ),
                default=_DEFAULT_RESIDUAL_WEIGHT,
                non_negative=True,
            ),
            power=parse_float(
                block.get("power"),
                key_path=(
                    "calculation.execute.estimate_params.residual.weights.power"
                ),
                default=_DEFAULT_RESIDUAL_WEIGHT,
                non_negative=True,
            ),
            power_factor=parse_float(
                block.get("power_factor"),
                key_path=(
                    "calculation.execute.estimate_params.residual.weights."
                    "power_factor"
                ),
                default=_DEFAULT_RESIDUAL_WEIGHT,
                non_negative=True,
            ),
            efficiency=parse_float(
                block.get("efficiency"),
                key_path=(
                    "calculation.execute.estimate_params.residual.weights."
                    "efficiency"
                ),
                default=_DEFAULT_RESIDUAL_WEIGHT,
                non_negative=True,
            ),
        )


class _ResidualNormalizationFactory:
    """``residual.normalization`` サブブロック factory。"""

    @staticmethod
    def create(raw: Any) -> ResidualNormalizationConfig:
        block = parse_dict(
            raw,
            key_path=(
                "calculation.execute.estimate_params.residual.normalization"
            ),
        )
        method = parse_enum(
            block.get("method"),
            ResidualNormalizationMethod,
            key_path=(
                "calculation.execute.estimate_params.residual."
                "normalization.method"
            ),
            default=ResidualNormalizationMethod.BY_CURVE_SCALE,
        )
        detail_block = _ResidualNormalizationFactory._detail_block(
            block=block,
            method=method,
        )
        return ResidualNormalizationConfig(
            method=method,
            statistic=parse_enum(
                detail_block.get("statistic"),
                ResidualNormalizationStatistic,
                key_path=(
                    "calculation.execute.estimate_params.residual."
                    f"normalization.{method.value}.statistic"
                ),
                default=ResidualNormalizationStatistic.STD,
            ),
            eps=parse_float(
                detail_block.get("eps"),
                key_path=(
                    "calculation.execute.estimate_params.residual."
                    f"normalization.{method.value}.eps"
                ),
                default=_DEFAULT_NORMALIZATION_EPS,
                positive=True,
            ),
        )

    @staticmethod
    def _detail_block(
        *,
        block: dict[str, Any],
        method: ResidualNormalizationMethod,
    ) -> dict[str, Any]:
        """named-nested 詳細ブロックを返す（旧 flat 形式も読み取り可）。"""
        nested = block.get(method.value)
        if nested is not None:
            return parse_dict(
                nested,
                key_path=(
                    "calculation.execute.estimate_params.residual."
                    f"normalization.{method.value}"
                ),
            )
        return block


class _ResidualFactory:
    """``residual`` サブブロック factory。"""

    @staticmethod
    def create(raw: Any) -> ResidualConfig:
        block = parse_dict(
            raw,
            key_path="calculation.execute.estimate_params.residual",
        )
        return ResidualConfig(
            weights=_ResidualWeightsFactory.create(block.get("weights")),
            normalization=_ResidualNormalizationFactory.create(
                block.get("normalization"),
            ),
        )


class _OptimizerFactory:
    """``optimizer`` サブブロック factory。"""

    @staticmethod
    def create(raw: Any) -> OptimizerConfig:
        block = parse_dict(
            raw,
            key_path="calculation.execute.estimate_params.optimizer",
        )
        algorithm = parse_enum(
            block.get("algorithm"),
            OptimizerAlgorithm,
            key_path=(
                "calculation.execute.estimate_params.optimizer.algorithm"
            ),
            default=OptimizerAlgorithm.LEAST_SQUARES,
        )
        return OptimizerConfig(
            algorithm=algorithm,
            least_squares=_LeastSquaresOptimizerFactory.create(
                _OptimizerFactory._detail_block(
                    block=block,
                    algorithm=algorithm,
                )
            ),
        )

    @staticmethod
    def _detail_block(
        *,
        block: dict[str, Any],
        algorithm: OptimizerAlgorithm,
    ) -> dict[str, Any]:
        """named-nested 詳細ブロックを返す（旧 flat 形式も読み取り可）。"""
        nested = block.get(algorithm.value)
        if nested is not None:
            return parse_dict(
                nested,
                key_path=(
                    "calculation.execute.estimate_params.optimizer."
                    f"{algorithm.value}"
                ),
            )
        return block


class _LeastSquaresOptimizerFactory:
    """``optimizer.least_squares`` サブブロック factory。"""

    @staticmethod
    def create(raw: Any) -> LeastSquaresOptimizerConfig:
        block = parse_dict(
            raw,
            key_path="calculation.execute.estimate_params.optimizer.least_squares",
        )
        return LeastSquaresOptimizerConfig(
            max_nfev=parse_int(
                block.get("max_nfev"),
                key_path=(
                    "calculation.execute.estimate_params.optimizer."
                    "least_squares.max_nfev"
                ),
                default=_DEFAULT_OPTIMIZER_MAX_NFEV,
                positive=True,
            ),
            ftol=parse_float(
                block.get("ftol"),
                key_path=(
                    "calculation.execute.estimate_params.optimizer."
                    "least_squares.ftol"
                ),
                default=_DEFAULT_OPTIMIZER_TOL,
                positive=True,
            ),
            xtol=parse_float(
                block.get("xtol"),
                key_path=(
                    "calculation.execute.estimate_params.optimizer."
                    "least_squares.xtol"
                ),
                default=_DEFAULT_OPTIMIZER_TOL,
                positive=True,
            ),
            gtol=parse_float(
                block.get("gtol"),
                key_path=(
                    "calculation.execute.estimate_params.optimizer."
                    "least_squares.gtol"
                ),
                default=_DEFAULT_OPTIMIZER_TOL,
                positive=True,
            ),
        )


class EstimateParamsConfigFactory:
    """``calculation.execute.estimate_params`` を dataclass に変換する。"""

    @staticmethod
    def create(raw: Any) -> EstimateParamsConfig:
        """YAML 由来の dict から :class:`EstimateParamsConfig` を組み立てる。

        Args:
            raw: ``calculation.execute.estimate_params`` の生 dict（``None`` 可）。

        Returns:
            EstimateParamsConfig: 補完・検証済みの dataclass。

        Raises:
            ValueError: dict 以外、または各値の制約違反。
        """
        block = parse_dict(
            raw,
            key_path="calculation.execute.estimate_params",
        )
        return EstimateParamsConfig(
            residual=_ResidualFactory.create(block.get("residual")),
            optimizer=_OptimizerFactory.create(block.get("optimizer")),
        )
