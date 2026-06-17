"""IM performance curve catalog DTO (1-D slip curves per supply condition)."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import cast

import numpy as np

from im_cable_system.engine.shared.dto.generic.interfaces import (
    IArrayWithUnitDto,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayActivePowerDto,
    ArrayCurrentMagnitudeDto,
    ArrayEfficiencyDto,
    ArrayPowerFactorDto,
    ArrayRotationalSpeedDto,
    ArraySlipDto,
    ArrayTorqueDto,
    FloatFrequencyDto,
    FloatVoltageDto,
)

_TORQUE_POWER_RTOL: float = 1.0e-4
_TORQUE_POWER_ATOL: float = 1.0


@dataclass(frozen=True)
class ImPerformanceCurveCatalogDto:
    """ある1供給条件における slip 軸に対する性能曲線 DTO。

    1供給条件 = ``(supply_frequency, supply_voltage)`` の組。
    供給条件の欠落はレコード自体を省略することで表現する
    （配列に NaN を入れて表現しない）。

    観測セルのマスキング戦略 (NaN-to-mask):
        各従属系列 (``power`` / ``torque`` / ``current`` /
        ``power_factor`` / ``efficiency``) は、観測点と未観測点の区別を
        伝えるための companion bool 配列 ``*_series_mask``
        （``slip_series`` と同じ長さ）を **必ず併せて持つ**。

        - ``True``: 有効（観測あり）点。
        - ``False``: 未観測点。``*_series`` 側にはプレースホルダ
          （通常 ``0``）が入っており、下流の残差計算やフィッティングから
          除外される想定。

        ``rotational_speed_series`` は独立軸として扱い、mask を持たない
        （すべての点が観測済みであることを要求する）。

        厳格化ポリシー (Option A):
            ``*_series is not None`` のときは ``*_series_mask`` を必ず
            一緒に渡す必要がある（``None`` は不可）。全点有効でも
            ``np.ones(n, dtype=bool)`` を明示する。これは「mask の有無で
            分岐するロジック」を下流に増やさないための契約である。

    Attributes:
        name: カタログ行識別子（系列名・条件ラベル等の非空文字列）。
        supply_frequency: 供給周波数（スカラ）。
        supply_voltage: 供給電圧（スカラ、実数）。
        slip_series: 独立軸となる slip 配列（1-D; NaN/inf 禁止）。
        rotational_speed_series: 回転速度（1-D; optional, NaN/inf 禁止）。
            独立軸として扱われ、mask は持たない。
        power_series: 有効電力（1-D; optional, NaN/inf 禁止）。
        power_series_mask: ``power_series`` 用の bool 有効点 mask
            （1-D; ``power_series`` と同じ長さ）。
            ``power_series is None`` のときは ``None``、それ以外では
            非 ``None`` の bool 配列が必須。
        torque_series: 軸トルク（1-D; optional, NaN/inf 禁止）。
        torque_series_mask: ``torque_series`` 用 mask
            （``power_series_mask`` と同様の制約）。
        current_series: 電流の大きさ |I|（1-D; optional, NaN/inf 禁止）。
        current_series_mask: ``current_series`` 用 mask
            （``power_series_mask`` と同様の制約）。
        power_factor_series: 力率（1-D; optional, NaN/inf 禁止）。
        power_factor_series_mask: ``power_factor_series`` 用 mask
            （``power_series_mask`` と同様の制約）。
        efficiency_series: 効率（1-D; optional, NaN/inf 禁止）。
        efficiency_series_mask: ``efficiency_series`` 用 mask
            （``power_series_mask`` と同様の制約）。

    Note:
        - すべての optional 従属系列は 1-D で、``slip_series`` と同じ
          長さでなければならない。
        - ``power_series`` / ``torque_series`` / ``current_series`` /
          ``power_factor_series`` / ``efficiency_series`` /
          ``rotational_speed_series`` の少なくとも 1 つを必ず指定する
          必要がある（さもなくば従属データを持たない空エントリとなる）。
        - ``power_series`` / ``torque_series`` /
          ``rotational_speed_series`` が **すべて** 揃っている場合、
          要素ごとに ``P = T·ω`` を検証する。対象となるシリーズ番号は
          **3 系列すべての mask が True かつ値が finite なインデックスに
          限定** する（``rtol = 1e-4`` / ``atol = 1.0 [W]``）。違反は
          :class:`ValueError`。
    """

    name: str

    supply_frequency: FloatFrequencyDto
    supply_voltage: FloatVoltageDto

    slip_series: ArraySlipDto
    rotational_speed_series: ArrayRotationalSpeedDto | None = None

    power_series: ArrayActivePowerDto | None = None
    power_series_mask: np.ndarray | None = None
    torque_series: ArrayTorqueDto | None = None
    torque_series_mask: np.ndarray | None = None
    current_series: ArrayCurrentMagnitudeDto | None = None
    current_series_mask: np.ndarray | None = None
    power_factor_series: ArrayPowerFactorDto | None = None
    power_factor_series_mask: np.ndarray | None = None
    efficiency_series: ArrayEfficiencyDto | None = None
    efficiency_series_mask: np.ndarray | None = None

    def __post_init__(self) -> None:
        """Validate 1-D shape, length consistency, and finite values.

        Raises:
            ValueError: If any contract check fails. See class docstring
                for individual rules (length / finite / at-least-one /
                torque-power consistency / mask shape).
        """
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("name must be a non-empty str")

        slip_arr = self.slip_series.get_value()
        if self.slip_series.get_ndim() != 1:
            raise ValueError("slip_series must be a 1-D array")
        n = int(slip_arr.size)
        if n < 1:
            raise ValueError("slip_series length must be at least 1")
        if not np.all(np.isfinite(slip_arr)):
            raise ValueError("slip_series must not contain NaN or inf")

        dependent_series: list[tuple[str, IArrayWithUnitDto | None]] = [
            ("power_series", self.power_series),
            ("torque_series", self.torque_series),
            ("current_series", self.current_series),
            ("power_factor_series", self.power_factor_series),
            ("efficiency_series", self.efficiency_series),
            ("rotational_speed_series", self.rotational_speed_series),
        ]
        if all(dto is None for _, dto in dependent_series):
            raise ValueError(
                "ImPerformanceCurveCatalogDto must carry at least one "
                "dependent series (power / torque / current / power_factor"
                " / efficiency / rotational_speed)"
            )
        for label, dto in dependent_series:
            self._assert_optional_1d_same_len_strict(label, dto, n)

        # Mask 検証（rotational_speed には mask を持たない）
        masked_pairs: list[
            tuple[str, IArrayWithUnitDto | None, np.ndarray | None]
        ] = [
            ("power_series", self.power_series, self.power_series_mask),
            ("torque_series", self.torque_series, self.torque_series_mask),
            ("current_series", self.current_series, self.current_series_mask),
            (
                "power_factor_series",
                self.power_factor_series,
                self.power_factor_series_mask,
            ),
            (
                "efficiency_series",
                self.efficiency_series,
                self.efficiency_series_mask,
            ),
        ]
        for label, series, mask in masked_pairs:
            self._assert_mask_consistent(
                label=label,
                series=series,
                mask=mask,
                expected_len=n,
            )

        self._assert_torque_power_consistency()

    @staticmethod
    def _assert_optional_1d_same_len_strict(
        label: str,
        dto: IArrayWithUnitDto | None,
        expected_len: int,
    ) -> None:
        """NaN/inf を許容しない optional 系列の形状・有限性検証。"""
        if dto is None:
            return
        arr = dto.get_value()
        if dto.get_ndim() != 1 or int(arr.size) != expected_len:
            raise ValueError(
                f"{label} must be 1-D with length {expected_len} "
                f"(shape={arr.shape})"
            )
        if not np.all(np.isfinite(arr)):
            raise ValueError(f"{label} must not contain NaN or inf")

    @staticmethod
    def _assert_mask_consistent(
        *,
        label: str,
        series: IArrayWithUnitDto | None,
        mask: np.ndarray | None,
        expected_len: int,
    ) -> None:
        """``*_series`` と対応 ``*_series_mask`` の整合性検証。

        Option A 厳格モード:

        - ``series is None`` のときは ``mask`` も ``None`` でなければ
          ``ValueError``。
        - ``series is not None`` のときは ``mask`` も非 ``None`` の
          ``np.ndarray`` （bool 型・1-D・長さ ``expected_len``）でなければ
          ``ValueError``。全点有効を表す場合も ``np.ones(expected_len,
          dtype=bool)`` を明示的に渡す必要がある。
        """
        if series is None:
            if mask is not None:
                raise ValueError(
                    f"{label}_mask must be None when {label} is None"
                )
            return
        if mask is None:
            raise ValueError(
                f"{label}_mask must be provided when {label} is not None "
                "(pass np.ones(n, dtype=bool) if all points are valid)"
            )
        if not isinstance(mask, np.ndarray):
            raise ValueError(
                f"{label}_mask must be a numpy ndarray (got {type(mask)!r})"
            )
        if mask.dtype != np.bool_:
            raise ValueError(
                f"{label}_mask must be a boolean array (dtype={mask.dtype!r})"
            )
        if mask.ndim != 1 or int(mask.size) != expected_len:
            raise ValueError(
                f"{label}_mask must be 1-D with length {expected_len} "
                f"(shape={mask.shape})"
            )

    def _assert_torque_power_consistency(self) -> None:
        """``P = T·ω`` の整合性を要素ごとに検証する。

        ``power_series`` / ``torque_series`` / ``rotational_speed_series``
        の3本が揃ったときのみ実行する。検証対象とするシリーズ番号は
        **power/torque の mask が True かつ値が finite なインデックスに
        限定** する（mask=False の点はプレースホルダなので除外）。
        ``rotational_speed_series`` は mask を持たないので全 True 扱い。
        単位は内部で SI（``W`` / ``Nm`` / ``rad/s``）に揃えて比較する。

        厳格化（Option A）後は ``power_series`` / ``torque_series`` に
        対応する mask が必ず非 ``None`` であることが
        :meth:`_assert_mask_consistent` により保証される。本メソッドでは
        その不変条件を ``assert`` で局所的に明示し、以降はそのまま使う。
        """
        if (
            self.power_series is None
            or self.torque_series is None
            or self.rotational_speed_series is None
        ):
            return
        power_w = self.power_series.to_base_unit().get_value()
        torque_nm = self.torque_series.to_base_unit().get_value()
        omega_rad_s = self.rotational_speed_series.to_base_unit().get_value()
        # __post_init__ 上流の _assert_mask_consistent により
        # power/torque の mask は非 None が保証されている。
        power_mask = cast(np.ndarray, self.power_series_mask)
        torque_mask = cast(np.ndarray, self.torque_series_mask)
        mask = (
            power_mask
            & torque_mask
            & np.isfinite(power_w)
            & np.isfinite(torque_nm)
            & np.isfinite(omega_rad_s)
        )
        if not np.any(mask):
            return
        power_w = power_w[mask]
        torque_nm = torque_nm[mask]
        omega_rad_s = omega_rad_s[mask]

        power_from_torque = torque_nm * omega_rad_s
        if not np.allclose(
            power_from_torque,
            power_w,
            rtol=_TORQUE_POWER_RTOL,
            atol=_TORQUE_POWER_ATOL,
        ):
            abs_err = float(np.max(np.abs(power_from_torque - power_w)))
            rel_err = float(
                np.max(
                    np.abs(power_from_torque - power_w)
                    / np.maximum(np.abs(power_w), 1e-300)
                )
            )
            raise ValueError(
                "torque_series と power_series / rotational_speed_series "
                "の関係が P = T·ω と整合しません "
                f"(max_abs={abs_err}, max_rel={rel_err}, "
                f"rtol={_TORQUE_POWER_RTOL}, atol={_TORQUE_POWER_ATOL})。"
            )


class ImPerformanceCurveCatalogDtos:
    """Collection of IM performance curve catalog entries.

    Duplicate ``name`` values are allowed (e.g. multiple supply conditions
    for the same series name).
    """

    def __init__(
        self,
        objects: list[ImPerformanceCurveCatalogDto],
    ) -> None:
        """Initialize the collection.

        Args:
            objects: List of catalog DTOs.
        """
        self._objects: list[ImPerformanceCurveCatalogDto] = list(objects)

    def get_all(self) -> list[ImPerformanceCurveCatalogDto]:
        """Return a copy of all elements."""
        return self._objects.copy()

    def __len__(self) -> int:
        return len(self._objects)

    def __iter__(self) -> Iterator[ImPerformanceCurveCatalogDto]:
        return iter(self._objects)
