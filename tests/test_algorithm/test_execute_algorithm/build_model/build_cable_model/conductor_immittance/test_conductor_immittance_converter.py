"""導線イミタンス converter / factory の単体テスト。"""

from __future__ import annotations

import numpy as np
import pytest

from im_cable_system.engine.algorithm.execute_algorithm.build_model.build_cable_model.conductor_immittance.basic.basic_conductor_immittance_converter import (  # noqa: E501
    BasicConductorImmittanceConverter,
)
from im_cable_system.engine.algorithm.execute_algorithm.build_model.build_cable_model.conductor_immittance.current_dependent.v1_current_dependent_skin_effect_immittance_converter import (  # noqa: E501
    CurrentDependentSkinEffectConductorImmittanceConverterV1,
)
from im_cable_system.engine.algorithm.execute_algorithm.build_model.build_cable_model.conductor_immittance.factory_conductor_immittance_converter import (  # noqa: E501
    ConductorImmittanceConverterFactory,
)
from im_cable_system.engine.algorithm.execute_algorithm.build_model.build_cable_model.conductor_immittance.frequency_dependent.v1_frequency_dependent_skin_effect_immittance_converter import (  # noqa: E501
    FrequencyDependentSkinEffectConductorImmittanceConverterV1,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    CableConductorModelDto,
    ConductorModelType,
    FloatParamDto,
    FloatParamDtos,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexCurrentDto,
    ArrayFrequencyDto,
    FloatInductanceDto,
    FloatResistanceDto,
)

_BASE_RESISTANCE = FloatResistanceDto(value=2.0, unit="Ω")
_BASE_INDUCTANCE = FloatInductanceDto(value=0.1, unit="H")


def _params(names: list[str]) -> FloatParamDtos:
    """指定名に同じ正値を入れた FloatParamDtos を作る。"""
    return FloatParamDtos(
        objects=[FloatParamDto(name=name, value=0.5) for name in names],
    )


def _conductor_model(
    model_type: ConductorModelType,
) -> CableConductorModelDto:
    """導線モデル DTO を作る。"""
    return CableConductorModelDto(
        name=model_type,
        params=(
            None
            if model_type == ConductorModelType.BASIC
            else _params(
                [
                    "alpha_conductor_r",
                    "beta_conductor_r",
                    "alpha_conductor_x",
                    "beta_conductor_x",
                ]
            )
        ),
    )


@pytest.mark.parametrize(
    ("model_type", "expected_type"),
    [
        (ConductorModelType.BASIC, BasicConductorImmittanceConverter),
        (
            ConductorModelType.FREQUENCY_DEPENDENT_SKIN_EFFECT_V1,
            FrequencyDependentSkinEffectConductorImmittanceConverterV1,
        ),
        (
            ConductorModelType.CURRENT_DEPENDENT_SKIN_EFFECT_V1,
            CurrentDependentSkinEffectConductorImmittanceConverterV1,
        ),
    ],
)
def test_factory_selects_converter_by_conductor_model_type(
    model_type: ConductorModelType,
    expected_type: type,
    config: IConfig,
    logger: ILogger,
) -> None:
    """ConductorModelType ごとに対応 converter が返る。"""
    converter = ConductorImmittanceConverterFactory.create_pie_converter(
        conductor_model=_conductor_model(model_type),
        config=config,
        logger=logger,
    )
    assert isinstance(converter, expected_type)


def test_basic_converter_returns_rl_series_impedance(
    config: IConfig,
    logger: ILogger,
) -> None:
    """BASIC converter は R + jωL を返す。"""
    converter = BasicConductorImmittanceConverter.create(
        config=config,
        logger=logger,
    )
    frequency = ArrayFrequencyDto(
        value=np.array([[50.0, 60.0]], dtype=np.float64),
        unit="Hz",
    )

    result = converter.convert(
        conductor_model=_conductor_model(ConductorModelType.BASIC),
        base_resistance_total=_BASE_RESISTANCE,
        base_inductance_total=_BASE_INDUCTANCE,
        frequency=frequency,
    )

    expected = 2.0 + 1j * 2.0 * np.pi * frequency.value * 0.1
    np.testing.assert_allclose(result.value, expected)
    assert result.unit == "Ω"


def test_frequency_dependent_converter_changes_with_frequency(
    config: IConfig,
    logger: ILogger,
) -> None:
    """周波数依存 converter は高周波側で抵抗を増やしリアクタンスを下げる。"""
    converter = (
        FrequencyDependentSkinEffectConductorImmittanceConverterV1.create(
            config=config,
            logger=logger,
        )
    )
    frequency = ArrayFrequencyDto(
        value=np.array([[50.0, 100.0]], dtype=np.float64),
        unit="Hz",
    )

    result = converter.convert(
        conductor_model=_conductor_model(
            ConductorModelType.FREQUENCY_DEPENDENT_SKIN_EFFECT_V1
        ),
        base_resistance_total=_BASE_RESISTANCE,
        base_inductance_total=_BASE_INDUCTANCE,
        frequency=frequency,
    )

    assert result.value.real[0, 1] > result.value.real[0, 0]
    assert result.value.imag[0, 1] < 2.0 * result.value.imag[0, 0]
    assert np.all(np.isfinite(result.value))


def test_current_dependent_converter_changes_with_current(
    config: IConfig,
    logger: ILogger,
) -> None:
    """電流依存 converter は大電流側で抵抗を増やしリアクタンスを下げる。"""
    converter = CurrentDependentSkinEffectConductorImmittanceConverterV1.create(
        config=config,
        logger=logger,
    )
    frequency = ArrayFrequencyDto(
        value=np.array([[50.0, 50.0]], dtype=np.float64),
        unit="Hz",
    )
    conductor_current = ArrayComplexCurrentDto(
        value=np.array([[0.0 + 0.0j, 100.0 + 0.0j]], dtype=np.complex128),
        unit="A",
    )

    result = converter.convert(
        conductor_model=_conductor_model(
            ConductorModelType.CURRENT_DEPENDENT_SKIN_EFFECT_V1
        ),
        base_resistance_total=_BASE_RESISTANCE,
        base_inductance_total=_BASE_INDUCTANCE,
        frequency=frequency,
        conductor_current=conductor_current,
    )

    assert result.value.real[0, 1] > result.value.real[0, 0]
    assert result.value.imag[0, 1] < result.value.imag[0, 0]
    assert np.all(np.isfinite(result.value))
