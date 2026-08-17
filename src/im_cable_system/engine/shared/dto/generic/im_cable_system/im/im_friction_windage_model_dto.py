"""Friction and windage loss model DTO.

DTO holding the friction/windage loss model type and parameters.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from im_cable_system.engine.shared.dto.generic.im_cable_system.parameter.param_dto import (  # noqa: E501
    FloatParamDtos,
    validate_param_names_match,
)


class ImFrictionWindageModelType(Enum):
    """Friction/windage loss model type enumeration."""

    NONE = "NONE"
    CONSTANT_V1 = "CONSTANT_V1"


@dataclass(frozen=True)
class ImFrictionWindageModelDto:
    """Friction/windage loss model DTO.

    Holds the friction/windage loss model type and parameters.

    Attributes:
        name: Model type (``ImFrictionWindageModelType``).
        params: Model-specific parameters.
    """

    name: ImFrictionWindageModelType
    params: FloatParamDtos | None = None

    def __post_init__(self) -> None:
        """Validate fields after initialization.

        ``params`` の name 集合がモデルの要求と完全一致することを共通検証で
        確認する（不足・余分・None 誤指定をいずれも :class:`ValueError`）。
        値が finite であることは :class:`FloatParamDto` 側で担保。
        """
        validate_param_names_match(
            self.params,
            required_names=self.get_required_parameter_names(),
            context=f"ImFrictionWindageModelDto[{self.name.value}]",
        )

    def get_required_parameter_names(self) -> list[str]:
        """Return the list of required parameter names.

        Returns:
            list[str]: Required parameter names (empty if none required).

        Raises:
            ValueError: モデル種別が未対応の場合（Enum 追加時の対応漏れ検知）。
        """
        if self.name == ImFrictionWindageModelType.NONE:
            return []
        if self.name == ImFrictionWindageModelType.CONSTANT_V1:
            return ["k_friction_windage"]
        raise ValueError(f"未対応の摩擦・風損モデル型です: {self.name!r}")

    def get_name(self) -> str:
        """Return the model name as a catalog token string.

        Returns:
            str: Model type value (``UPPER_SNAKE``).
        """
        return self.name.value
