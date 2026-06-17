"""IM 成分イミタンス converter factory の単体テスト。"""

from __future__ import annotations

import pytest

from im_cable_system.engine.algorithm.execute_algorithm.build_model.build_im_model.im_component_immittance.excitation.basic.excitation_immittance_converter import (  # noqa: E501
    BasicExcitationImmittanceConverter,
)
from im_cable_system.engine.algorithm.execute_algorithm.build_model.build_im_model.im_component_immittance.excitation.current_dependent.v1_excitation_saturation_immittance_converter import (  # noqa: E501
    CurrentDependentExcitationSaturationImmittanceConverterV1,
)
from im_cable_system.engine.algorithm.execute_algorithm.build_model.build_im_model.im_component_immittance.excitation.slip_dependent.v1_excitation_saturation_immittance_converter import (  # noqa: E501
    SlipDependentExcitationSaturationImmittanceConverterV1,
)
from im_cable_system.engine.algorithm.execute_algorithm.build_model.build_im_model.im_component_immittance.factory_im_component_immittance_converter import (  # noqa: E501
    ImComponentImmittanceConverterFactory,
)
from im_cable_system.engine.algorithm.execute_algorithm.build_model.build_im_model.im_component_immittance.primary.basic.primary_immittance_converter import (  # noqa: E501
    BasicPrimaryImmittanceConverter,
)
from im_cable_system.engine.algorithm.execute_algorithm.build_model.build_im_model.im_component_immittance.primary.current_dependent.v1_primary_leakage_saturation_immittance_converter import (  # noqa: E501
    CurrentDependentPrimaryLeakageSaturationImmittanceConverterV1,
)
from im_cable_system.engine.algorithm.execute_algorithm.build_model.build_im_model.im_component_immittance.primary.slip_dependent.v1_primary_leakage_saturation_immittance_converter import (  # noqa: E501
    SlipDependentPrimaryLeakageSaturationImmittanceConverterV1,
)
from im_cable_system.engine.algorithm.execute_algorithm.build_model.build_im_model.im_component_immittance.secondary.basic.secondary_immittance_converter import (  # noqa: E501
    BasicSecondaryImmittanceConverter,
)
from im_cable_system.engine.algorithm.execute_algorithm.build_model.build_im_model.im_component_immittance.secondary.current_dependent.v1_secondary_leakage_saturation_immittance_converter import (  # noqa: E501
    CurrentDependentSecondaryLeakageSaturationImmittanceConverterV1,
)
from im_cable_system.engine.algorithm.execute_algorithm.build_model.build_im_model.im_component_immittance.secondary.current_dependent.v1_secondary_skin_effect_and_leakage_saturation_immittance_converter import (  # noqa: E501
    CurrentDependentSecondarySkinEffectAndLeakageSaturationImmittanceConverterV1,
)
from im_cable_system.engine.algorithm.execute_algorithm.build_model.build_im_model.im_component_immittance.secondary.current_dependent.v1_secondary_skin_effect_immittance_converter import (  # noqa: E501
    CurrentDependentSecondarySkinEffectImmittanceConverterV1,
)
from im_cable_system.engine.algorithm.execute_algorithm.build_model.build_im_model.im_component_immittance.secondary.slip_dependent.v1_secondary_skin_effect_immittance_converter import (  # noqa: E501
    SlipDependentSecondarySkinEffectImmittanceConverterV1,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    FloatParamDto,
    FloatParamDtos,
    ImExcitationModelDto,
    ImExcitationModelType,
    ImPrimaryModelDto,
    ImPrimaryModelType,
    ImSecondaryModelDto,
    ImSecondaryModelType,
)


def _params(required_names: list[str]) -> FloatParamDtos | None:
    """required_names に対応するテスト用 params を作る。"""
    if not required_names:
        return None
    return FloatParamDtos(
        objects=[
            FloatParamDto(name=name, value=0.2) for name in required_names
        ],
    )


_PRIMARY_REQUIRED_NAMES: dict[ImPrimaryModelType, list[str]] = {
    ImPrimaryModelType.BASIC: [],
    ImPrimaryModelType.SLIP_DEPENDENT_LEAKAGE_SATURATION_V1: [
        "alpha_primary_r",
        "alpha_primary_x",
        "beta_primary_x",
    ],
    ImPrimaryModelType.CURRENT_DEPENDENT_LEAKAGE_SATURATION_V1: [
        "alpha_primary_leakage_x",
        "beta_primary_leakage_x",
    ],
}

_EXCITATION_REQUIRED_NAMES: dict[ImExcitationModelType, list[str]] = {
    ImExcitationModelType.BASIC: [],
    ImExcitationModelType.SLIP_DEPENDENT_SATURATION_V1: [
        "alpha_excitation_r",
        "alpha_excitation_x",
        "beta_excitation_x",
    ],
    ImExcitationModelType.CURRENT_DEPENDENT_SATURATION_V1: [
        "alpha_excitation_r",
        "alpha_excitation_x",
        "beta_excitation_x",
    ],
}

_SECONDARY_REQUIRED_NAMES: dict[ImSecondaryModelType, list[str]] = {
    ImSecondaryModelType.BASIC: [],
    ImSecondaryModelType.SLIP_DEPENDENT_SKIN_EFFECT_V1: [
        "alpha_secondary_r",
        "beta_secondary_r",
        "alpha_secondary_x",
        "beta_secondary_x",
    ],
    ImSecondaryModelType.CURRENT_DEPENDENT_SKIN_EFFECT_V1: [
        "alpha_secondary_r",
        "beta_secondary_r",
        "alpha_secondary_x",
        "beta_secondary_x",
    ],
    ImSecondaryModelType.CURRENT_DEPENDENT_LEAKAGE_SATURATION_V1: [
        "alpha_secondary_leakage_x",
        "beta_secondary_leakage_x",
    ],
    ImSecondaryModelType.CURRENT_DEPENDENT_SKIN_EFFECT_AND_LEAKAGE_SATURATION_V1: [
        "alpha_secondary_r",
        "beta_secondary_r",
        "alpha_secondary_x",
        "beta_secondary_x",
        "alpha_secondary_leakage_x",
        "beta_secondary_leakage_x",
    ],
}


def _primary_model(model_type: ImPrimaryModelType) -> ImPrimaryModelDto:
    return ImPrimaryModelDto(
        name=model_type,
        params=_params(_PRIMARY_REQUIRED_NAMES[model_type]),
    )


def _excitation_model(
    model_type: ImExcitationModelType,
) -> ImExcitationModelDto:
    return ImExcitationModelDto(
        name=model_type,
        params=_params(_EXCITATION_REQUIRED_NAMES[model_type]),
    )


def _secondary_model(model_type: ImSecondaryModelType) -> ImSecondaryModelDto:
    return ImSecondaryModelDto(
        name=model_type,
        params=_params(_SECONDARY_REQUIRED_NAMES[model_type]),
    )


@pytest.mark.parametrize(
    ("model_type", "expected_type"),
    [
        (ImPrimaryModelType.BASIC, BasicPrimaryImmittanceConverter),
        (
            ImPrimaryModelType.SLIP_DEPENDENT_LEAKAGE_SATURATION_V1,
            SlipDependentPrimaryLeakageSaturationImmittanceConverterV1,
        ),
        (
            ImPrimaryModelType.CURRENT_DEPENDENT_LEAKAGE_SATURATION_V1,
            CurrentDependentPrimaryLeakageSaturationImmittanceConverterV1,
        ),
    ],
)
def test_primary_factory_selects_converter(
    model_type: ImPrimaryModelType,
    expected_type: type,
    config: IConfig,
    logger: ILogger,
) -> None:
    """一次モデルタイプごとに対応 converter が返る。"""
    converter = ImComponentImmittanceConverterFactory.create_primary_converter(
        circuit_model=_primary_model(model_type),
        config=config,
        logger=logger,
    )
    assert isinstance(converter, expected_type)


@pytest.mark.parametrize(
    ("model_type", "expected_type"),
    [
        (ImExcitationModelType.BASIC, BasicExcitationImmittanceConverter),
        (
            ImExcitationModelType.SLIP_DEPENDENT_SATURATION_V1,
            SlipDependentExcitationSaturationImmittanceConverterV1,
        ),
        (
            ImExcitationModelType.CURRENT_DEPENDENT_SATURATION_V1,
            CurrentDependentExcitationSaturationImmittanceConverterV1,
        ),
    ],
)
def test_excitation_factory_selects_converter(
    model_type: ImExcitationModelType,
    expected_type: type,
    config: IConfig,
    logger: ILogger,
) -> None:
    """励磁モデルタイプごとに対応 converter が返る。"""
    converter = (
        ImComponentImmittanceConverterFactory.create_excitation_converter(
            circuit_model=_excitation_model(model_type),
            config=config,
            logger=logger,
        )
    )
    assert isinstance(converter, expected_type)


@pytest.mark.parametrize(
    ("model_type", "expected_type"),
    [
        (ImSecondaryModelType.BASIC, BasicSecondaryImmittanceConverter),
        (
            ImSecondaryModelType.SLIP_DEPENDENT_SKIN_EFFECT_V1,
            SlipDependentSecondarySkinEffectImmittanceConverterV1,
        ),
        (
            ImSecondaryModelType.CURRENT_DEPENDENT_SKIN_EFFECT_V1,
            CurrentDependentSecondarySkinEffectImmittanceConverterV1,
        ),
        (
            ImSecondaryModelType.CURRENT_DEPENDENT_LEAKAGE_SATURATION_V1,
            CurrentDependentSecondaryLeakageSaturationImmittanceConverterV1,
        ),
        (
            ImSecondaryModelType.CURRENT_DEPENDENT_SKIN_EFFECT_AND_LEAKAGE_SATURATION_V1,
            CurrentDependentSecondarySkinEffectAndLeakageSaturationImmittanceConverterV1,
        ),
    ],
)
def test_secondary_factory_selects_converter(
    model_type: ImSecondaryModelType,
    expected_type: type,
    config: IConfig,
    logger: ILogger,
) -> None:
    """二次モデルタイプごとに対応 converter が返る。"""
    converter = (
        ImComponentImmittanceConverterFactory.create_secondary_converter(
            circuit_model=_secondary_model(model_type),
            config=config,
            logger=logger,
        )
    )
    assert isinstance(converter, expected_type)
