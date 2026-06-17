"""ImPerformanceCurveCatalogDto の torque_series 関連検証テスト。

カバー対象:
    - ``torque_series`` 単独で dependent 系列の条件を満たす
    - Catalog DTO **コンテナレベル** で ``torque_series`` の NaN/inf を
      **禁止** する（``ArrayTorqueDto`` 単独では NaN を許容するが、
      Catalog DTO の ``__post_init__`` が追加で NaN を弾く。
      点単位の除外は ``torque_series_mask`` 経由で行う）
    - ``power_series`` / ``torque_series`` / ``rotational_speed_series``
      が全部揃ったとき ``P = T·ω`` の整合性を要素ごとに検証
    - ``torque_series_mask`` が False の要素は整合性検証からスキップ
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ImPerformanceCurveCatalogDto,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayActivePowerDto,
    ArrayCurrentMagnitudeDto,
    ArrayRotationalSpeedDto,
    ArraySlipDto,
    ArrayTorqueDto,
    FloatFrequencyDto,
    FloatVoltageDto,
)

_RPM = np.array([1800.0, 1750.0, 1700.0], dtype=np.float64)
_OMEGA = 2.0 * math.pi * _RPM / 60.0
_TORQUE = np.array([10.0, 12.0, 14.0], dtype=np.float64)
_POWER = _TORQUE * _OMEGA
_SLIP = np.array([0.00, 0.03, 0.06], dtype=np.float64)
_N = int(_SLIP.size)


def _all_true_mask() -> np.ndarray:
    """全点有効を表す bool mask（長さ ``_N``）。"""
    return np.ones(_N, dtype=np.bool_)


def _supply_freq() -> FloatFrequencyDto:
    return FloatFrequencyDto(value=60.0, unit="Hz")


def _supply_volt() -> FloatVoltageDto:
    return FloatVoltageDto(value=230.0, unit="V")


def _slip_dto() -> ArraySlipDto:
    return ArraySlipDto(value=_SLIP, unit="-")


def _power_dto(values: np.ndarray | None = None) -> ArrayActivePowerDto:
    return ArrayActivePowerDto(
        value=values if values is not None else _POWER,
        unit="W",
    )


def _torque_dto(values: np.ndarray | None = None) -> ArrayTorqueDto:
    return ArrayTorqueDto(
        value=values if values is not None else _TORQUE,
        unit="Nm",
    )


def _rpm_dto() -> ArrayRotationalSpeedDto:
    return ArrayRotationalSpeedDto(value=_RPM, unit="rpm")


class TestTorqueSeriesAsDependent:
    """torque_series が dependent 系列として有効に扱われるかのテスト。"""

    def test_torque_only_satisfies_at_least_one_dependent(self) -> None:
        ImPerformanceCurveCatalogDto(
            name="catalog",
            supply_frequency=_supply_freq(),
            supply_voltage=_supply_volt(),
            slip_series=_slip_dto(),
            torque_series=_torque_dto(),
            torque_series_mask=_all_true_mask(),
        )

    def test_all_none_raises(self) -> None:
        with pytest.raises(ValueError, match="at least one"):
            ImPerformanceCurveCatalogDto(
                name="catalog",
                supply_frequency=_supply_freq(),
                supply_voltage=_supply_volt(),
                slip_series=_slip_dto(),
            )


class TestTorqueSeriesNanInfRules:
    """torque_series の NaN/inf 取り扱い（Catalog DTO 内では両方禁止）。"""

    def test_torque_nan_allowed_at_array_dto_level(self) -> None:
        """``ArrayTorqueDto`` 単独では NaN を許容する（Generic 契約）。

        Catalog DTO の追加検証で初めて NaN が弾かれる
        （:meth:`test_torque_nan_rejected_at_catalog_level` 参照）。
        """
        torque_with_nan = np.array([10.0, np.nan, 14.0], dtype=np.float64)
        dto = _torque_dto(torque_with_nan)
        assert np.isnan(dto.get_value()[1])

    def test_torque_nan_rejected_at_catalog_level(self) -> None:
        """Catalog DTO に NaN 入り torque を渡すと拒否される。"""
        torque_with_nan = np.array([10.0, np.nan, 14.0], dtype=np.float64)
        with pytest.raises(ValueError, match="NaN"):
            ImPerformanceCurveCatalogDto(
                name="catalog",
                supply_frequency=_supply_freq(),
                supply_voltage=_supply_volt(),
                slip_series=_slip_dto(),
                torque_series=_torque_dto(torque_with_nan),
                torque_series_mask=_all_true_mask(),
            )

    def test_torque_inf_rejected(self) -> None:
        torque_with_inf = np.array([10.0, np.inf, 14.0], dtype=np.float64)
        with pytest.raises(ValueError):
            _torque_dto(torque_with_inf)

    def test_torque_wrong_length_rejected(self) -> None:
        bad = np.array([10.0, 12.0], dtype=np.float64)
        bad_mask = np.array([True, True], dtype=np.bool_)
        with pytest.raises(ValueError, match="torque_series"):
            ImPerformanceCurveCatalogDto(
                name="catalog",
                supply_frequency=_supply_freq(),
                supply_voltage=_supply_volt(),
                slip_series=_slip_dto(),
                torque_series=_torque_dto(bad),
                torque_series_mask=bad_mask,
            )


class TestTorquePowerConsistency:
    """P = T·ω の要素ごと整合性検証。"""

    def test_consistent_triple_ok(self) -> None:
        ImPerformanceCurveCatalogDto(
            name="catalog",
            supply_frequency=_supply_freq(),
            supply_voltage=_supply_volt(),
            slip_series=_slip_dto(),
            power_series=_power_dto(),
            power_series_mask=_all_true_mask(),
            torque_series=_torque_dto(),
            torque_series_mask=_all_true_mask(),
            rotational_speed_series=_rpm_dto(),
        )

    def test_inconsistent_triple_raises(self) -> None:
        bad_power = _POWER.copy()
        bad_power[1] *= 1.5
        with pytest.raises(
            ValueError,
            match="P = T",
        ):
            ImPerformanceCurveCatalogDto(
                name="catalog",
                supply_frequency=_supply_freq(),
                supply_voltage=_supply_volt(),
                slip_series=_slip_dto(),
                power_series=_power_dto(bad_power),
                power_series_mask=_all_true_mask(),
                torque_series=_torque_dto(),
                torque_series_mask=_all_true_mask(),
                rotational_speed_series=_rpm_dto(),
            )

    def test_inconsistent_element_skipped_when_torque_mask_false(self) -> None:
        """``torque_series_mask`` が False の要素は整合性検証から除外される。

        power 側に「もし torque があれば不整合」になる値を入れていても、
        その要素位置の torque_series_mask が False なら、その点は
        プレースホルダとして除外され、__post_init__ は通る。
        """
        bad_power = _POWER.copy()
        bad_power[1] *= 1.5
        torque_with_zero = _TORQUE.copy()
        torque_with_zero[1] = 0.0  # placeholder
        torque_mask = np.array([True, False, True], dtype=np.bool_)
        ImPerformanceCurveCatalogDto(
            name="catalog",
            supply_frequency=_supply_freq(),
            supply_voltage=_supply_volt(),
            slip_series=_slip_dto(),
            power_series=_power_dto(bad_power),
            power_series_mask=_all_true_mask(),
            torque_series=_torque_dto(torque_with_zero),
            torque_series_mask=torque_mask,
            rotational_speed_series=_rpm_dto(),
        )

    def test_inconsistent_element_skipped_when_power_mask_false(self) -> None:
        """``power_series_mask`` が False の要素も整合性検証から除外される。"""
        bad_power = _POWER.copy()
        bad_power[1] = 0.0  # placeholder
        power_mask = np.array([True, False, True], dtype=np.bool_)
        ImPerformanceCurveCatalogDto(
            name="catalog",
            supply_frequency=_supply_freq(),
            supply_voltage=_supply_volt(),
            slip_series=_slip_dto(),
            power_series=_power_dto(bad_power),
            power_series_mask=power_mask,
            torque_series=_torque_dto(),
            torque_series_mask=_all_true_mask(),
            rotational_speed_series=_rpm_dto(),
        )

    def test_consistency_skipped_when_rotational_speed_missing(self) -> None:
        """omega が無いと整合性検証はスキップされる。

        本来は不整合だが rpm が無いため検証されず通る。
        """
        bad_power = _POWER.copy()
        bad_power[1] *= 1.5
        ImPerformanceCurveCatalogDto(
            name="catalog",
            supply_frequency=_supply_freq(),
            supply_voltage=_supply_volt(),
            slip_series=_slip_dto(),
            power_series=_power_dto(bad_power),
            power_series_mask=_all_true_mask(),
            torque_series=_torque_dto(),
            torque_series_mask=_all_true_mask(),
            rotational_speed_series=None,
        )


class TestSeriesMaskConsistency:
    """``*_series_mask`` の形状・dtype・整合性検証（Option A 厳格モード）。"""

    def test_mask_required_when_series_not_none(self) -> None:
        """``series is not None`` のとき ``mask=None`` は raise。"""
        with pytest.raises(
            ValueError,
            match=r"power_series_mask must be provided",
        ):
            ImPerformanceCurveCatalogDto(
                name="catalog",
                supply_frequency=_supply_freq(),
                supply_voltage=_supply_volt(),
                slip_series=_slip_dto(),
                power_series=_power_dto(),
                power_series_mask=None,
            )

    def test_mask_required_none_when_series_none(self) -> None:
        """``series=None`` のとき ``mask`` も None でなければ raise。"""
        bogus_mask = np.array([True, True, True], dtype=np.bool_)
        with pytest.raises(
            ValueError,
            match=r"power_series_mask must be None",
        ):
            ImPerformanceCurveCatalogDto(
                name="catalog",
                supply_frequency=_supply_freq(),
                supply_voltage=_supply_volt(),
                slip_series=_slip_dto(),
                power_series=None,
                power_series_mask=bogus_mask,
                torque_series=_torque_dto(),
                torque_series_mask=_all_true_mask(),
            )

    def test_mask_must_be_bool(self) -> None:
        """整数配列を mask に渡すと dtype エラー。"""
        bad_mask = np.array([1, 1, 1], dtype=np.int64)
        with pytest.raises(ValueError, match=r"boolean"):
            ImPerformanceCurveCatalogDto(
                name="catalog",
                supply_frequency=_supply_freq(),
                supply_voltage=_supply_volt(),
                slip_series=_slip_dto(),
                power_series=_power_dto(),
                power_series_mask=bad_mask,
            )

    def test_mask_must_match_length(self) -> None:
        """長さ不一致の mask は raise。"""
        bad_mask = np.array([True, True], dtype=np.bool_)
        with pytest.raises(ValueError, match=r"length 3"):
            ImPerformanceCurveCatalogDto(
                name="catalog",
                supply_frequency=_supply_freq(),
                supply_voltage=_supply_volt(),
                slip_series=_slip_dto(),
                power_series=_power_dto(),
                power_series_mask=bad_mask,
            )

    def test_mask_accepts_partial_false(self) -> None:
        """``False`` を含む mask は通る（値は ``Array*Dto`` の finite 制約に従う）。"""
        mask = np.array([True, False, True], dtype=np.bool_)
        power_with_placeholder = _POWER.copy()
        power_with_placeholder[1] = 0.0
        ImPerformanceCurveCatalogDto(
            name="catalog",
            supply_frequency=_supply_freq(),
            supply_voltage=_supply_volt(),
            slip_series=_slip_dto(),
            power_series=_power_dto(power_with_placeholder),
            power_series_mask=mask,
        )

    def test_current_mask_independent_of_power_mask(self) -> None:
        """各 ``*_series_mask`` は独立に設定できる。"""
        current_arr = np.array([10.0, 0.0, 14.0], dtype=np.float64)
        current_mask = np.array([True, False, True], dtype=np.bool_)
        ImPerformanceCurveCatalogDto(
            name="catalog",
            supply_frequency=_supply_freq(),
            supply_voltage=_supply_volt(),
            slip_series=_slip_dto(),
            current_series=ArrayCurrentMagnitudeDto(
                value=current_arr,
                unit="A",
            ),
            current_series_mask=current_mask,
        )
