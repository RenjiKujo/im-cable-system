"""Secondary circuit model DTO.

DTO holding the secondary circuit model type and parameters.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from im_cable_system.engine.shared.dto.generic.im_cable_system.parameter.param_dto import (  # noqa: E501
    FloatParamDtos,
    validate_param_names_match,
)


class ImSecondaryModelType(Enum):
    """Secondary circuit model type enumeration."""

    BASIC = "BASIC"
    SLIP_DEPENDENT_SKIN_EFFECT_V1 = "SLIP_DEPENDENT_SKIN_EFFECT_V1"
    CURRENT_DEPENDENT_SKIN_EFFECT_V1 = "CURRENT_DEPENDENT_SKIN_EFFECT_V1"
    CURRENT_DEPENDENT_LEAKAGE_SATURATION_V1 = (
        "CURRENT_DEPENDENT_LEAKAGE_SATURATION_V1"
    )
    CURRENT_DEPENDENT_SKIN_EFFECT_AND_LEAKAGE_SATURATION_V1 = (
        "CURRENT_DEPENDENT_SKIN_EFFECT_AND_LEAKAGE_SATURATION_V1"
    )


class ImSecondaryCageBranchType(Enum):
    """Branch keys when representing the secondary (cage) circuit as a dict.

    For a single cage, only ``SINGLE`` is used.
    For a double cage, ``INNER`` (inner bar) and ``OUTER`` (outer bar) are used.

    Note:
        Whether the machine has one or two cages is expressed by
        :class:`ImCageMultiplicityType`. ``SINGLE`` here is a branch key name,
        not synonymous with single-cage multiplicity.
    """

    SINGLE = "SINGLE"
    INNER = "INNER"
    OUTER = "OUTER"


class ImCageMultiplicityType(Enum):
    """Cage multiplicity (single cage vs double cage).

    Must stay consistent with the key set of
    :class:`ImSecondaryCageBranchType` dictionaries.

    - ``SINGLE_CAGE``: keys are :attr:`ImSecondaryCageBranchType.SINGLE` only.
    - ``DOUBLE_CAGE``: keys are :attr:`ImSecondaryCageBranchType.INNER` and
      :attr:`ImSecondaryCageBranchType.OUTER`.
    """

    SINGLE_CAGE = "SINGLE_CAGE"
    DOUBLE_CAGE = "DOUBLE_CAGE"


def expected_branch_keys_for_cage_multiplicity(
    multiplicity: ImCageMultiplicityType,
) -> frozenset[ImSecondaryCageBranchType]:
    """Return allowed secondary-dict branch keys for the given cage multiplicity.

    Args:
        multiplicity: Cage multiplicity (single cage or double cage).

    Returns:
        frozenset[ImSecondaryCageBranchType]: Allowed branch keys for that
        multiplicity.
    """
    if multiplicity == ImCageMultiplicityType.SINGLE_CAGE:
        return frozenset({ImSecondaryCageBranchType.SINGLE})
    return frozenset(
        {
            ImSecondaryCageBranchType.INNER,
            ImSecondaryCageBranchType.OUTER,
        }
    )


@dataclass(frozen=True)
class ImSecondaryModelDto:
    """Secondary circuit model DTO.

    Holds the secondary circuit model type and parameters.

    Attributes:
        name: Model type (``ImSecondaryModelType``).
        params (FloatParamDtos | None): Model-specific parameters.
    """

    name: ImSecondaryModelType
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
            context=f"ImSecondaryModelDto[{self.name.value}]",
        )

    def get_required_parameter_names(self) -> list[str]:
        """Return the list of required parameter names.

        Returns:
            list[str]: Required parameter names (empty if none required).

        Raises:
            ValueError: モデル種別が未対応の場合（Enum 追加時の対応漏れ検知）。
        """
        if self.name == ImSecondaryModelType.BASIC:
            return []
        if self.name == ImSecondaryModelType.SLIP_DEPENDENT_SKIN_EFFECT_V1:
            return [
                "alpha_secondary_r",
                "beta_secondary_r",
                "alpha_secondary_x",
                "beta_secondary_x",
            ]
        if self.name == ImSecondaryModelType.CURRENT_DEPENDENT_SKIN_EFFECT_V1:
            return [
                "alpha_secondary_r",
                "beta_secondary_r",
                "alpha_secondary_x",
                "beta_secondary_x",
            ]
        if (
            self.name
            == ImSecondaryModelType.CURRENT_DEPENDENT_LEAKAGE_SATURATION_V1
        ):
            return [
                "alpha_secondary_leakage_x",
                "beta_secondary_leakage_x",
            ]
        if (
            self.name
            == ImSecondaryModelType.CURRENT_DEPENDENT_SKIN_EFFECT_AND_LEAKAGE_SATURATION_V1
        ):
            return [
                "alpha_secondary_r",
                "beta_secondary_r",
                "alpha_secondary_x",
                "beta_secondary_x",
                "alpha_secondary_leakage_x",
                "beta_secondary_leakage_x",
            ]
        raise ValueError(f"未対応の二次モデル型です: {self.name!r}")

    def get_name(self) -> str:
        """Return the model name as a catalog token string.

        Returns:
            str: Model type value (``UPPER_SNAKE``).
        """
        return self.name.value
