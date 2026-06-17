"""Cable circuit model contract (conductor types, pi dictionary keys, DTO).

Bundles conductor calculation model types (Input / build_model) and pi-type
equivalent-circuit dictionary branch keys (ITM, simulate, ArrayKey integration)
in one module. Mirrors the "model type + branch key Enum" pattern in
:class:`im_cable_system.engine.shared.dto.generic.im_cable_system.im.im_secondary_model_dto`.

Note:
    Enum values follow two conventions by use case
    (see ``docs/shared/dto_principle.md``).

    - ``ConductorModelType``: ``UPPER_SNAKE`` for catalog and factory branching
    - ``PieCableConductorKey`` / ``PieCableGroundKey``: Lowercase for ITM
      dictionaries and ``ArrayKey`` segments (e.g. ``pie_single``)

    The absence of a pi-dictionary-only ``ImKey`` on the IM side is intentional.
    - IM is represented by fixed attributes on
      :class:`~im_cable_system.engine.shared.dto.itm.model.itm_im_model_dto.ItmImModelDto`
      (primary and excitation) and a dictionary only for secondary branches via
      :class:`~im_cable_system.engine.shared.dto.generic.im_cable_system.im.im_secondary_model_dto.ImSecondaryCageBranchType`.
    - Current names placed on array layouts are covered by the shared wire-key
      vocabulary in
      :class:`~im_cable_system.engine.shared.dto.generic.im_cable_system.array.array_key.ArrayKey`.
    - ``PieCable*Key`` is for pi-type cable ``conductor_*`` / ``ground_*``
      dictionaries only. Values are flattened into ``ArrayLayoutDto`` as
      ``conductor_current.{value}`` (see ``ArrayKey`` ``CONDUCTOR_CURRENT_*`` /
      ``GROUND_CURRENT_*``).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from im_cable_system.engine.shared.dto.generic.im_cable_system.parameter.param_dto import (  # noqa: E501
    FloatParamDtos,
    validate_param_names_match,
)


class ConductorModelType(Enum):
    """Conductor circuit model type enumeration.

    Defines model types for conductor circuits.
    """

    BASIC = "BASIC"
    FREQUENCY_DEPENDENT_SKIN_EFFECT_V1 = "FREQUENCY_DEPENDENT_SKIN_EFFECT_V1"
    CURRENT_DEPENDENT_SKIN_EFFECT_V1 = "CURRENT_DEPENDENT_SKIN_EFFECT_V1"


class PieCableConductorKey(str, Enum):
    """Pi-type cable conductor (series branch) key."""

    SINGLE = "pie_single"


class PieCableGroundKey(str, Enum):
    """Pi-type cable ground (shunt branch) key."""

    UPSTREAM = "pie_upstream"
    DOWNSTREAM = "pie_downstream"


@dataclass(frozen=True)
class CableConductorModelDto:
    """DTO for a conductor circuit model.

    Holds the conductor model type and its parameters.

    Attributes:
        name: Model type (``ConductorModelType``).
        params: Model-specific parameters (``FloatParamDtos`` or None).
    """

    name: ConductorModelType
    params: FloatParamDtos | None = None

    def __post_init__(self) -> None:
        """Validate required parameters.

        ``params`` の name 集合がモデルの要求と完全一致することを共通検証で
        確認する（不足・余分・None 誤指定をいずれも :class:`ValueError`）。
        値が finite であることは :class:`FloatParamDto` 側で担保。
        """
        validate_param_names_match(
            self.params,
            required_names=self.get_required_parameter_names(),
            context=f"CableConductorModelDto[{self.name.value}]",
        )

    def get_required_parameter_names(self) -> list[str]:
        """Return names of parameters required for this model.

        Returns:
            list[str]: Required parameter names (empty when none are required).

        Raises:
            ValueError: モデル種別が未対応の場合（Enum 追加時の対応漏れ検知）。
        """
        if self.name == ConductorModelType.BASIC:
            return []
        if self.name == ConductorModelType.FREQUENCY_DEPENDENT_SKIN_EFFECT_V1:
            return [
                "alpha_conductor_r",
                "beta_conductor_r",
                "alpha_conductor_x",
                "beta_conductor_x",
            ]
        if self.name == ConductorModelType.CURRENT_DEPENDENT_SKIN_EFFECT_V1:
            return [
                "alpha_conductor_r",
                "beta_conductor_r",
                "alpha_conductor_x",
                "beta_conductor_x",
            ]
        raise ValueError(f"未対応の導体モデル型です: {self.name!r}")

    def get_name(self) -> str:
        """Return the model name as a catalog token string.

        Returns:
            str: Model type value (``UPPER_SNAKE``).
        """
        return self.name.value
