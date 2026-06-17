"""``validation.im_rated_value`` の単体テスト。

``validate_voltage_range`` / ``validate_current_range`` は ``ValidationResultDto``
を返す検証関数。境界値と異常系を網羅する。
"""

from __future__ import annotations

import numpy as np
import pytest

from im_cable_system.engine.domain.validation import (
    validate_current_range,
    validate_voltage_range,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexCurrentDto,
    ArrayComplexVoltageDto,
)


class TestValidateVoltageRangeWithinTolerance:
    """電圧 ±10% 以内（``tolerance=0.1``）でパスすること。"""

    @pytest.mark.parametrize(
        "magnitude",
        [90.0, 100.0, 110.0],
    )
    def test_passes_at_boundary_and_center(self, magnitude: float) -> None:
        voltage = ArrayComplexVoltageDto(
            value=np.array([magnitude + 0j]), unit="V"
        )
        result = validate_voltage_range(
            voltage=voltage, rated_voltage=100.0, tolerance=0.1
        )
        assert result.is_valid is True

    def test_passes_with_complex_voltage_in_range(self) -> None:
        """複素電圧でも絶対値で比較されること。"""
        # 80 + 60j -> magnitude = 100
        voltage = ArrayComplexVoltageDto(
            value=np.array([80.0 + 60.0j]), unit="V"
        )
        result = validate_voltage_range(
            voltage=voltage, rated_voltage=100.0, tolerance=0.1
        )
        assert result.is_valid is True


class TestValidateVoltageRangeOutOfTolerance:
    """電圧が許容範囲外のときの ``is_valid=False`` と詳細レポート。"""

    def test_fails_below_minimum(self) -> None:
        voltage = ArrayComplexVoltageDto(value=np.array([85.0 + 0j]), unit="V")
        result = validate_voltage_range(
            voltage=voltage, rated_voltage=100.0, tolerance=0.1
        )
        assert result.is_valid is False
        assert "許容範囲外" in result.message

    def test_fails_above_maximum(self) -> None:
        voltage = ArrayComplexVoltageDto(value=np.array([115.0 + 0j]), unit="V")
        result = validate_voltage_range(
            voltage=voltage, rated_voltage=100.0, tolerance=0.1
        )
        assert result.is_valid is False
        assert "許容範囲外" in result.message

    def test_reports_multiple_violations_in_message(self) -> None:
        """複数要素が許容外のとき、違反件数がメッセージに反映される。"""
        voltage = ArrayComplexVoltageDto(
            value=np.array([100.0, 80.0, 70.0, 95.0]) + 0j, unit="V"
        )
        result = validate_voltage_range(
            voltage=voltage, rated_voltage=100.0, tolerance=0.1
        )
        assert result.is_valid is False
        assert "違反箇所数: 2/4" in result.message


class TestValidateVoltageRangeInvalidRated:
    """定格電圧 <= 0 を許可しないこと。"""

    @pytest.mark.parametrize("rated_voltage", [0.0, -10.0])
    def test_fails_when_rated_is_non_positive(
        self, rated_voltage: float
    ) -> None:
        voltage = ArrayComplexVoltageDto(value=np.array([100.0 + 0j]), unit="V")
        result = validate_voltage_range(
            voltage=voltage, rated_voltage=rated_voltage
        )
        assert result.is_valid is False
        assert "正の値" in result.message


class TestValidateCurrentRangeWithinTolerance:
    """電流が ``tolerance=6.0``（7 倍）以内でパスすること。"""

    @pytest.mark.parametrize(
        "magnitude",
        [0.0, 10.0, 70.0],
    )
    def test_passes_at_or_below_max(self, magnitude: float) -> None:
        """下限はチェックされず、上限ぴったりまでパス。"""
        current = ArrayComplexCurrentDto(
            value=np.array([magnitude + 0j]), unit="A"
        )
        result = validate_current_range(
            current=current, rated_current=10.0, tolerance=6.0
        )
        assert result.is_valid is True

    def test_passes_with_complex_current(self) -> None:
        # |30 + 40j| = 50 ≤ 70
        current = ArrayComplexCurrentDto(
            value=np.array([30.0 + 40.0j]), unit="A"
        )
        result = validate_current_range(
            current=current, rated_current=10.0, tolerance=6.0
        )
        assert result.is_valid is True


class TestValidateCurrentRangeOutOfTolerance:
    """電流が許容範囲外のときの ``is_valid=False`` と詳細レポート。"""

    def test_fails_above_max(self) -> None:
        current = ArrayComplexCurrentDto(value=np.array([80.0 + 0j]), unit="A")
        result = validate_current_range(
            current=current, rated_current=10.0, tolerance=6.0
        )
        assert result.is_valid is False
        assert "許容範囲外" in result.message

    def test_reports_multiple_violations_in_message(self) -> None:
        current = ArrayComplexCurrentDto(
            value=np.array([10.0, 100.0, 200.0, 30.0]) + 0j, unit="A"
        )
        result = validate_current_range(
            current=current, rated_current=10.0, tolerance=6.0
        )
        assert result.is_valid is False
        assert "違反箇所数: 2/4" in result.message


class TestValidateCurrentRangeInvalidRated:
    """定格電流 <= 0 を許可しないこと。"""

    @pytest.mark.parametrize("rated_current", [0.0, -1.0])
    def test_fails_when_rated_is_non_positive(
        self, rated_current: float
    ) -> None:
        current = ArrayComplexCurrentDto(value=np.array([1.0 + 0j]), unit="A")
        result = validate_current_range(
            current=current, rated_current=rated_current
        )
        assert result.is_valid is False
        assert "正の値" in result.message
