"""モデル係数（``FloatParam``）の DTO と検証ヘルパー。

``ImPrimaryModelDto`` / ``ImExcitationModelDto`` / ``ImSecondaryModelDto`` /
``CableConductorModelDto`` の各モデル DTO が共通で使う「モデル係数」を
保持する DTO と、それを「期待される name 集合と完全一致しているか」
検証する共通関数 :func:`validate_param_names_match` を提供する。
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from im_cable_system.engine.shared.dto.generic.entity import (
    BaseEntityDto,
)


@dataclass(frozen=True)
class FloatParamDto:
    """DTO for a named float parameter.

    Attributes:
        name: Parameter name.
        value: Parameter value.
    """

    name: str
    value: float

    def __post_init__(self) -> None:
        """Validate the parameter name and value.

        Raises:
            ValueError: name が空文字 / value が非数値 / value が NaN・inf。
        """
        if not isinstance(self.name, str) or self.name.strip() == "":
            raise ValueError("parameter name must be a non-empty str")
        if not isinstance(self.value, (int, float)) or isinstance(
            self.value, bool
        ):
            raise ValueError("parameter value must be numeric")
        if not math.isfinite(float(self.value)):
            raise ValueError(
                f"parameter value must be finite (got {self.value!r}) "
                f"for parameter {self.name!r}"
            )

    def get_value(self) -> float:
        """Return the parameter value."""
        return float(self.value)


class FloatParamDtos(BaseEntityDto[FloatParamDto]):
    """Collection DTO for FloatParamDto instances."""

    def __init__(self, objects: list[FloatParamDto]) -> None:
        """Initialize the collection.

        Args:
            objects: Initial list of FloatParamDto instances.

        Raises:
            ValueError: ``objects`` 内で ``name`` が重複している場合。
        """
        names: list[str] = [obj.name for obj in objects]
        seen: set[str] = set()
        duplicates: list[str] = []
        for name in names:
            if name in seen and name not in duplicates:
                duplicates.append(name)
            seen.add(name)
        if duplicates:
            raise ValueError(
                f"FloatParamDtos に同じ name が重複しています: "
                f"{sorted(duplicates)}"
            )
        super().__init__(objects=objects, attribute_name="name")


def validate_param_names_match(
    params: FloatParamDtos | None,
    *,
    required_names: list[str],
    context: str,
) -> None:
    """``params`` の name 集合が ``required_names`` と完全一致するか検証する。

    モデル係数 DTO の ``__post_init__`` で共通的に使われる契約。
    「必要なものが揃っているか」だけでなく、「余分なものが混ざっていないか」
    も同時に検証する（カタログ YAML の typo や、別モデルの係数を取り違える
    バグを早期に弾く目的）。

    Args:
        params: 検証対象のパラメータコレクション。``None`` 許容。
        required_names: 期待する name のリスト（順序は不問）。
        context: エラーメッセージに含めるコンテキスト
            （例: ``"ImPrimaryModelDto[SLIP_DEPENDENT_LEAKAGE_SATURATION_V1]"``）。

    Raises:
        ValueError:
            - ``required_names`` が空でないのに ``params is None``。
            - ``required_names`` が空なのに ``params`` に要素がある。
            - ``params`` の name 集合が ``required_names`` に対して
              不足・余分のいずれかを含む。
    """
    expected = set(required_names)
    if not expected:
        if params is None:
            return
        actual_list = sorted(params.get_names())
        if actual_list:
            raise ValueError(
                f"{context}: パラメータを取らないモデルですが "
                f"params が指定されています: {actual_list}"
            )
        return
    if params is None:
        raise ValueError(
            f"{context}: パラメータが必須ですが params が None です。"
            f" 必須: {sorted(expected)}"
        )
    actual = set(params.get_names())
    missing = expected - actual
    unexpected = actual - expected
    if missing or unexpected:
        details: list[str] = []
        if missing:
            details.append(f"不足: {sorted(missing)}")
        if unexpected:
            details.append(f"余分: {sorted(unexpected)}")
        raise ValueError(
            f"{context}: params の name 集合が不一致 "
            f"({', '.join(details)})。必須: {sorted(expected)}"
        )
