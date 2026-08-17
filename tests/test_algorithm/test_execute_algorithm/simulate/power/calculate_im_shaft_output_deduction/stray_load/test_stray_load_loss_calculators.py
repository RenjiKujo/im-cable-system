"""漂遊負荷損計算器（NONE / CURRENT_DEPENDENT_QUADRATIC_V1）とファクトリーの単体テスト。

内部実装の単体テスト。窓口（``calculate_im_shaft_output_deduction`` の
``__all__``）に載せていないリーフモジュールへ直 import している。
"""

from __future__ import annotations

import numpy as np
import pytest

from im_cable_system.engine.algorithm.execute_algorithm.simulate.power.calculate_im_shaft_output_deduction.stray_load.current_dependent_quadratic_stray_load_loss_calculator import (  # noqa: E501
    CurrentDependentQuadraticStrayLoadLossCalculator,
)
from im_cable_system.engine.algorithm.execute_algorithm.simulate.power.calculate_im_shaft_output_deduction.stray_load.factory_stray_load_loss_calculator import (  # noqa: E501
    StrayLoadLossCalculatorFactory,
)
from im_cable_system.engine.algorithm.execute_algorithm.simulate.power.calculate_im_shaft_output_deduction.stray_load.none_stray_load_loss_calculator import (  # noqa: E501
    NoneStrayLoadLossCalculator,
)
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    FloatParamDto,
    FloatParamDtos,
    ImStrayLoadModelDto,
    ImStrayLoadModelType,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexCurrentDto,
    FloatActivePowerDto,
    FloatCurrentDto,
)


class _DummyLogger:
    def info(self, _msg: str, *_args: object) -> None:
        pass

    def warning(self, _msg: str, *_args: object) -> None:
        pass

    def error(self, _msg: str, *_args: object) -> None:
        pass


class _DummyConfig:
    class _NumericalGuardConfig:
        eps: float = 1.0e-9

    numerical_guard_config = _NumericalGuardConfig()


class _StubImModel:
    """``stray_load_model`` / 銘牌値だけを持つ最小スタブ。"""

    def __init__(self, stray_load_model: ImStrayLoadModelDto) -> None:
        self.stray_load_model = stray_load_model
        self.nameplate_power = FloatActivePowerDto(value=1000.0, unit="W")
        self.nameplate_current = FloatCurrentDto(value=10.0, unit="A")


class TestStrayLoadLossCalculatorFactory:
    """モデル種別ごとの分岐網羅。"""

    def test_none_returns_none_calculator(self) -> None:
        calculator = StrayLoadLossCalculatorFactory.create(
            model_type=ImStrayLoadModelType.NONE,
            config=_DummyConfig(),  # type: ignore[arg-type]
            logger=_DummyLogger(),  # type: ignore[arg-type]
        )
        assert isinstance(calculator, NoneStrayLoadLossCalculator)

    def test_current_dependent_quadratic_v1_returns_expected_calculator(
        self,
    ) -> None:
        calculator = StrayLoadLossCalculatorFactory.create(
            model_type=ImStrayLoadModelType.CURRENT_DEPENDENT_QUADRATIC_V1,
            config=_DummyConfig(),  # type: ignore[arg-type]
            logger=_DummyLogger(),  # type: ignore[arg-type]
        )
        assert isinstance(
            calculator, CurrentDependentQuadraticStrayLoadLossCalculator
        )


class TestNoneStrayLoadLossCalculator:
    def test_returns_zero_array_matching_current_shape(self) -> None:
        calculator = NoneStrayLoadLossCalculator.create(
            config=_DummyConfig(),  # type: ignore[arg-type]
            logger=_DummyLogger(),  # type: ignore[arg-type]
        )
        im_model = _StubImModel(
            ImStrayLoadModelDto(name=ImStrayLoadModelType.NONE)
        )
        loss = calculator.calculate(
            im_model=im_model,  # type: ignore[arg-type]
            secondary_current=ArrayComplexCurrentDto(
                value=np.array([1.0 + 1.0j, 2.0]), unit="A"
            ),
        )
        assert loss.get_shape() == (2,)
        np.testing.assert_allclose(loss.get_value(), [0.0, 0.0])


class TestCurrentDependentQuadraticStrayLoadLossCalculator:
    def test_returns_expected_loss(self) -> None:
        calculator = CurrentDependentQuadraticStrayLoadLossCalculator.create(
            config=_DummyConfig(),  # type: ignore[arg-type]
            logger=_DummyLogger(),  # type: ignore[arg-type]
        )
        im_model = _StubImModel(
            ImStrayLoadModelDto(
                name=ImStrayLoadModelType.CURRENT_DEPENDENT_QUADRATIC_V1,
                params=FloatParamDtos(
                    objects=[FloatParamDto(name="k_stray_load", value=0.01)]
                ),
            )
        )
        loss = calculator.calculate(
            im_model=im_model,  # type: ignore[arg-type]
            secondary_current=ArrayComplexCurrentDto(
                value=np.array([5.0 + 0.0j]), unit="A"
            ),
        )
        # r_I2 = 5/10 = 0.5, P_stray = 0.01 * 1000 * 0.25 = 2.5
        np.testing.assert_allclose(loss.get_value(), [2.5 + 0.0j])
        assert np.all(np.imag(loss.get_value()) == 0.0)

    def test_raises_when_params_missing(self) -> None:
        calculator = CurrentDependentQuadraticStrayLoadLossCalculator.create(
            config=_DummyConfig(),  # type: ignore[arg-type]
            logger=_DummyLogger(),  # type: ignore[arg-type]
        )
        im_model = _StubImModel(
            ImStrayLoadModelDto(name=ImStrayLoadModelType.NONE)
        )
        with pytest.raises(ValueError, match="paramsが必要"):
            calculator.calculate(
                im_model=im_model,  # type: ignore[arg-type]
                secondary_current=ArrayComplexCurrentDto(
                    value=np.array([1.0 + 0.0j]), unit="A"
                ),
            )
