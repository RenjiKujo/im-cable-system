"""Unit-aware DTOs for torque."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from im_cable_system.engine.shared.dto.generic.interfaces.i_value_with_unit_dto import (
    IArrayWithUnitDto,
)

TORQUE_FACTORS: dict[str, float] = {
    "Nm": 1.0,
    "N·m": 1.0,
    "kgf·m": 9.80665,
}


@dataclass(frozen=True)
class ArrayTorqueDto(IArrayWithUnitDto):
    """Torque array DTO.

    Attributes:
        value: トルク配列。``inf`` は禁止。``NaN`` は Generic DTO レベル
            では許容する（例: ドメイン層の計算で omega ≈ 0 のときトルクが
            未定義となるケースを、配列を作り直さずに「未定義サンプル」
            マーカとしてそのまま運べるようにするため）。
            観測曲線を束ねるコンテナ DTO（特に
            :class:`ImPerformanceCurveCatalogDto`）はこの上に
            **より厳格な契約** を課し、``torque_series`` の value 配列に
            NaN が含まれることを拒否する。未観測点は
            ``torque_series_mask`` で表現することを必須とする。
        unit: ``Nm``、``N·m``、``kgf·m`` のいずれか。

    NOTE:
        将来的に ``ArrayTorqueDto`` 自体を NaN 禁止の厳格 DTO へ移行する
        ことを想定している。その際は次の方針を取る予定。

        - InputDto に **始動トルク（slip = 1 / omega = 0 における
          トルク）** を持たせる。
        - ドメイン層の ``calculate_torque`` を改修し、omega ≈ 0 の点では
          ``P / omega`` ではなく InputDto から取得した始動トルクを返す。
        - InputDto に始動トルクが未設定の場合は、警告ログを出した上で
          便宜的に ``0`` を代入する（プレースホルダ）。

        本対応は YAGNI の観点で必要になってから着手する位置付けであり、
        現時点では本 NOTE のみで意図を残す。
    """

    value: np.ndarray
    unit: str

    def __post_init__(self) -> None:
        """Validate the instance."""
        arr = np.asarray(self.value, dtype=np.float64)
        if arr.size == 0:
            raise ValueError("torque array must not be empty")
        if np.any(np.isinf(arr)):
            raise ValueError("torque array must not contain inf")
        object.__setattr__(self, "value", arr)

        valid_units = list(TORQUE_FACTORS.keys())
        if self.unit not in valid_units:
            raise ValueError(f"invalid torque unit: {self.unit}")

    def get_value(self) -> np.ndarray:
        """Return the torque array."""
        return self.value

    def get_unit(self) -> str:
        """Return the torque unit."""
        return self.unit

    def get_shape(self) -> tuple[int, ...]:
        """Return the array shape."""
        return self.value.shape

    def get_ndim(self) -> int:
        """Return the number of dimensions."""
        return self.value.ndim

    def to_base_unit(self) -> ArrayTorqueDto:
        """Convert to the base unit (``Nm``)."""
        if self.unit == "Nm":
            return self
        base_value = self.value * TORQUE_FACTORS[self.unit]
        return ArrayTorqueDto(value=base_value, unit="Nm")

    def convert_to_unit(self, target_unit: str) -> ArrayTorqueDto:
        """Return a new DTO in the requested unit."""
        if target_unit not in TORQUE_FACTORS:
            raise ValueError(f"invalid torque unit: {target_unit}")
        if target_unit == self.unit:
            return self

        base = self.to_base_unit().value
        reverse = {
            unit: (1.0 / factor) for unit, factor in TORQUE_FACTORS.items()
        }
        converted = base * reverse[target_unit]
        return ArrayTorqueDto(value=converted, unit=target_unit)
