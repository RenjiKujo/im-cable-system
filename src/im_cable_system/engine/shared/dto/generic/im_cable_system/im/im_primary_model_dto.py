"""Primary circuit model DTO.

DTO holding the primary circuit model type and parameters.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from im_cable_system.engine.shared.dto.generic.im_cable_system.parameter.param_dto import (  # noqa: E501
    FloatParamDtos,
    validate_param_names_match,
)


class ImPrimaryModelType(Enum):
    """Primary circuit model type enumeration."""

    BASIC = "BASIC"
    SLIP_DEPENDENT_LEAKAGE_SATURATION_V1 = (
        "SLIP_DEPENDENT_LEAKAGE_SATURATION_V1"
    )
    CURRENT_DEPENDENT_LEAKAGE_SATURATION_V1 = (
        "CURRENT_DEPENDENT_LEAKAGE_SATURATION_V1"
    )


@dataclass(frozen=True)
class ImPrimaryModelDto:
    """Primary circuit model DTO.

    Holds the primary circuit model type and parameters.

    Attributes:
        name: Model type (``ImPrimaryModelType``).
        params: Model-specific parameters.
    """

    name: ImPrimaryModelType
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
            context=f"ImPrimaryModelDto[{self.name.value}]",
        )

    def get_required_parameter_names(self) -> list[str]:
        """Return the list of required parameter names.

        Returns:
            list[str]: Required parameter names (empty if none required).

        Raises:
            ValueError: モデル種別が未対応の場合（Enum 追加時の対応漏れ検知）。
        """
        if self.name == ImPrimaryModelType.BASIC:
            return []
        if self.name == ImPrimaryModelType.SLIP_DEPENDENT_LEAKAGE_SATURATION_V1:
            return [
                "alpha_primary_r",
                "alpha_primary_x",
                "beta_primary_x",
            ]
        if (
            self.name
            == ImPrimaryModelType.CURRENT_DEPENDENT_LEAKAGE_SATURATION_V1
        ):
            return [
                "alpha_primary_leakage_x",
                "beta_primary_leakage_x",
            ]
        raise ValueError(f"未対応の一次モデル型です: {self.name!r}")

    def get_name(self) -> str:
        """Return the model name as a catalog token string.

        Returns:
            str: Model type value (``UPPER_SNAKE``).
        """
        return self.name.value
