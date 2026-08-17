"""摩擦・風損計算器（NONE / CONSTANT_V1）とファクトリーの単体テスト。

内部実装の単体テスト。窓口（``calculate_im_shaft_output_deduction`` の
``__all__``）に載せていないリーフモジュールへ直 import している。
"""

from __future__ import annotations

import numpy as np
import pytest

from im_cable_system.engine.algorithm.execute_algorithm.simulate.power.calculate_im_shaft_output_deduction.friction_windage.constant_friction_windage_loss_calculator import (  # noqa: E501
    ConstantFrictionWindageLossCalculator,
)
from im_cable_system.engine.algorithm.execute_algorithm.simulate.power.calculate_im_shaft_output_deduction.friction_windage.factory_friction_windage_loss_calculator import (  # noqa: E501
    FrictionWindageLossCalculatorFactory,
)
from im_cable_system.engine.algorithm.execute_algorithm.simulate.power.calculate_im_shaft_output_deduction.friction_windage.none_friction_windage_loss_calculator import (  # noqa: E501
    NoneFrictionWindageLossCalculator,
)
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    FloatParamDto,
    FloatParamDtos,
    ImFrictionWindageModelDto,
    ImFrictionWindageModelType,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    FloatActivePowerDto,
)


class _DummyLogger:
    def info(self, _msg: str, *_args: object) -> None:
        pass

    def warning(self, _msg: str, *_args: object) -> None:
        pass

    def error(self, _msg: str, *_args: object) -> None:
        pass


class _DummyConfig:
    config_file_path = "dummy"


class _StubImModel:
    """``friction_windage_model`` / ``nameplate_power`` だけを持つ最小スタブ。"""

    def __init__(
        self, friction_windage_model: ImFrictionWindageModelDto
    ) -> None:
        self.friction_windage_model = friction_windage_model
        self.nameplate_power = FloatActivePowerDto(value=1000.0, unit="W")


class TestFrictionWindageLossCalculatorFactory:
    """モデル種別ごとの分岐網羅。"""

    def test_none_returns_none_calculator(self) -> None:
        calculator = FrictionWindageLossCalculatorFactory.create(
            model_type=ImFrictionWindageModelType.NONE,
            config=_DummyConfig(),  # type: ignore[arg-type]
            logger=_DummyLogger(),  # type: ignore[arg-type]
        )
        assert isinstance(calculator, NoneFrictionWindageLossCalculator)

    def test_constant_v1_returns_constant_calculator(self) -> None:
        calculator = FrictionWindageLossCalculatorFactory.create(
            model_type=ImFrictionWindageModelType.CONSTANT_V1,
            config=_DummyConfig(),  # type: ignore[arg-type]
            logger=_DummyLogger(),  # type: ignore[arg-type]
        )
        assert isinstance(calculator, ConstantFrictionWindageLossCalculator)


class TestNoneFrictionWindageLossCalculator:
    def test_returns_zero_array_of_reference_shape(self) -> None:
        calculator = NoneFrictionWindageLossCalculator.create(
            config=_DummyConfig(),  # type: ignore[arg-type]
            logger=_DummyLogger(),  # type: ignore[arg-type]
        )
        im_model = _StubImModel(
            ImFrictionWindageModelDto(name=ImFrictionWindageModelType.NONE)
        )
        loss = calculator.calculate(
            im_model=im_model,  # type: ignore[arg-type]
            reference_shape=(2, 3),
        )
        assert loss.get_shape() == (2, 3)
        np.testing.assert_allclose(loss.get_value(), np.zeros((2, 3)))
        assert loss.get_unit() == "VA"


class TestConstantFrictionWindageLossCalculator:
    def test_returns_expected_constant_loss(self) -> None:
        calculator = ConstantFrictionWindageLossCalculator.create(
            config=_DummyConfig(),  # type: ignore[arg-type]
            logger=_DummyLogger(),  # type: ignore[arg-type]
        )
        im_model = _StubImModel(
            ImFrictionWindageModelDto(
                name=ImFrictionWindageModelType.CONSTANT_V1,
                params=FloatParamDtos(
                    objects=[
                        FloatParamDto(name="k_friction_windage", value=0.02)
                    ]
                ),
            )
        )
        loss = calculator.calculate(
            im_model=im_model,  # type: ignore[arg-type]
            reference_shape=(2,),
        )
        # P_FW = 0.02 * 1000 = 20
        np.testing.assert_allclose(loss.get_value(), [20.0 + 0.0j, 20.0 + 0.0j])
        assert np.all(np.imag(loss.get_value()) == 0.0)

    def test_raises_when_params_missing(self) -> None:
        calculator = ConstantFrictionWindageLossCalculator.create(
            config=_DummyConfig(),  # type: ignore[arg-type]
            logger=_DummyLogger(),  # type: ignore[arg-type]
        )
        # NONE モデル（params=None）を CONSTANT_V1 計算器へ直接渡す
        # （factory を経由しない分岐外の異常系。params 欠落ガードを確認する）。
        im_model = _StubImModel(
            ImFrictionWindageModelDto(name=ImFrictionWindageModelType.NONE)
        )
        with pytest.raises(ValueError, match="paramsが必要"):
            calculator.calculate(
                im_model=im_model,  # type: ignore[arg-type]
                reference_shape=(1,),
            )
