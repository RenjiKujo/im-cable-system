"""``calculation.execute.validation`` セクションのスキーマと factory。

中間 DTO に対する検証（エネルギー保存／電流電圧レンジ）の
有効・無効、重大度、許容誤差を保持する。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from im_cable_system.engine.shared.config.schema._parsers import (
    parse_bool,
    parse_dict,
    parse_enum,
    parse_float,
)
from im_cable_system.engine.shared.config.schema.severity import Severity

_DEFAULT_ENABLED = True
_DEFAULT_ENERGY_TOLERANCE = 1.0e-6
_DEFAULT_VOLTAGE_TOLERANCE = 0.1
_DEFAULT_CURRENT_TOLERANCE = 6.0


@dataclass(frozen=True)
class EnergyConservationValidationConfig:
    """エネルギー保存則検証の設定。"""

    enabled: bool
    severity: Severity
    tolerance: float


@dataclass(frozen=True)
class CurrentVoltageRangeValidationConfig:
    """電流・電圧レンジ検証の設定。"""

    enabled: bool
    severity: Severity
    voltage_tolerance: float
    current_tolerance: float


@dataclass(frozen=True)
class ValidationConfig:
    """中間 DTO 検証セクション全体。"""

    energy_conservation: EnergyConservationValidationConfig
    current_voltage_range: CurrentVoltageRangeValidationConfig


class _EnergyConservationFactory:
    """``energy_conservation`` サブブロック factory。"""

    @staticmethod
    def create(raw: Any) -> EnergyConservationValidationConfig:
        block = parse_dict(
            raw,
            key_path="calculation.execute.validation.energy_conservation",
        )
        return EnergyConservationValidationConfig(
            enabled=parse_bool(
                block.get("enabled"),
                key_path=(
                    "calculation.execute.validation.energy_conservation.enabled"
                ),
                default=_DEFAULT_ENABLED,
            ),
            severity=parse_enum(
                block.get("severity"),
                Severity,
                key_path=(
                    "calculation.execute.validation.energy_conservation."
                    "severity"
                ),
                default=Severity.ERROR,
            ),
            tolerance=parse_float(
                block.get("tolerance"),
                key_path=(
                    "calculation.execute.validation.energy_conservation."
                    "tolerance"
                ),
                default=_DEFAULT_ENERGY_TOLERANCE,
                positive=True,
            ),
        )


class _CurrentVoltageRangeFactory:
    """``current_voltage_range`` サブブロック factory。"""

    @staticmethod
    def create(raw: Any) -> CurrentVoltageRangeValidationConfig:
        block = parse_dict(
            raw,
            key_path="calculation.execute.validation.current_voltage_range",
        )
        return CurrentVoltageRangeValidationConfig(
            enabled=parse_bool(
                block.get("enabled"),
                key_path=(
                    "calculation.execute.validation.current_voltage_range."
                    "enabled"
                ),
                default=_DEFAULT_ENABLED,
            ),
            severity=parse_enum(
                block.get("severity"),
                Severity,
                key_path=(
                    "calculation.execute.validation.current_voltage_range."
                    "severity"
                ),
                default=Severity.WARNING,
            ),
            voltage_tolerance=parse_float(
                block.get("voltage_tolerance"),
                key_path=(
                    "calculation.execute.validation.current_voltage_range."
                    "voltage_tolerance"
                ),
                default=_DEFAULT_VOLTAGE_TOLERANCE,
                positive=True,
            ),
            current_tolerance=parse_float(
                block.get("current_tolerance"),
                key_path=(
                    "calculation.execute.validation.current_voltage_range."
                    "current_tolerance"
                ),
                default=_DEFAULT_CURRENT_TOLERANCE,
                positive=True,
            ),
        )


class ValidationConfigFactory:
    """``calculation.execute.validation`` を dataclass に変換する。"""

    @staticmethod
    def create(raw: Any) -> ValidationConfig:
        """YAML 由来の dict から :class:`ValidationConfig` を組み立てる。

        Args:
            raw: ``calculation.execute.validation`` の生 dict（``None`` 可）。

        Returns:
            ValidationConfig: 補完・検証済みの dataclass。

        Raises:
            ValueError: dict 以外、または各サブブロックの制約違反。
        """
        block = parse_dict(
            raw,
            key_path="calculation.execute.validation",
        )
        return ValidationConfig(
            energy_conservation=_EnergyConservationFactory.create(
                block.get("energy_conservation"),
            ),
            current_voltage_range=_CurrentVoltageRangeFactory.create(
                block.get("current_voltage_range"),
            ),
        )
