"""IM 総合イミタンス synthesizer / factory の単体テスト。"""

from __future__ import annotations

import numpy as np
import pytest

from im_cable_system.engine.algorithm.execute_algorithm.build_model.build_im_model.im_total_immittance.double_cage_im_total_immittance_synthesizer import (  # noqa: E501
    DoubleCageImTotalImmittanceSynthesizerFactory,
    LTypeDoubleCageImTotalImmittanceSynthesizer,
    TTypeDoubleCageImTotalImmittanceSynthesizer,
)
from im_cable_system.engine.algorithm.execute_algorithm.build_model.build_im_model.im_total_immittance.single_cage_im_total_immittance_synthesizer import (  # noqa: E501
    LTypeSingleCageImTotalImmittanceSynthesizer,
    SingleCageImTotalImmittanceSynthesizerFactory,
    TTypeSingleCageImTotalImmittanceSynthesizer,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ImCageMultiplicityType,
    ImCircuitType,
    ImExcitationModelDto,
    ImExcitationModelType,
    ImPrimaryModelDto,
    ImPrimaryModelType,
    ImSecondaryCageBranchType,
    ImSecondaryModelDto,
    ImSecondaryModelType,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexAdmittanceDto,
    ArrayComplexImpedanceDto,
    FloatInductanceDto,
    FloatResistanceDto,
)
from im_cable_system.engine.shared.dto.itm import (
    ItmImExcitationDto,
    ItmImPrimaryDto,
    ItmImSecondaryDto,
)


def _z(value: complex) -> ArrayComplexImpedanceDto:
    """1要素のインピーダンスDTOを作る。"""
    return ArrayComplexImpedanceDto(
        value=np.array([[value]], dtype=np.complex128),
        unit="Ω",
    )


def _y_from_z(value: complex) -> ArrayComplexAdmittanceDto:
    """1要素のアドミタンスDTOを作る。"""
    return ArrayComplexAdmittanceDto(
        value=np.array([[1.0 / value]], dtype=np.complex128),
        unit="S",
    )


def _r() -> FloatResistanceDto:
    """ダミーの抵抗DTOを作る（合成器テストでは値を参照しない）。"""
    return FloatResistanceDto(value=1.0, unit="Ω")


def _l() -> FloatInductanceDto:
    """ダミーのインダクタンスDTOを作る（合成器テストでは値を参照しない）。"""
    return FloatInductanceDto(value=1.0, unit="H")


def _primary(value: complex) -> ItmImPrimaryDto:
    """一次モデルDTOを作る。"""
    return ItmImPrimaryDto(
        model=ImPrimaryModelDto(name=ImPrimaryModelType.BASIC),
        resistance=_r(),
        inductance=_l(),
        impedance=_z(value),
        admittance=_y_from_z(value),
    )


def _excitation(value: complex) -> ItmImExcitationDto:
    """励磁モデルDTOを作る。"""
    return ItmImExcitationDto(
        model=ImExcitationModelDto(name=ImExcitationModelType.BASIC),
        resistance=_r(),
        inductance=_l(),
        impedance=_z(value),
        admittance=_y_from_z(value),
    )


def _single_secondary(value: complex) -> ItmImSecondaryDto:
    """単一かご二次モデルDTOを作る。"""
    branch = ImSecondaryCageBranchType.SINGLE
    model = ImSecondaryModelDto(name=ImSecondaryModelType.BASIC)
    impedance = _z(value)
    admittance = _y_from_z(value)
    return ItmImSecondaryDto(
        cage_multiplicity=ImCageMultiplicityType.SINGLE_CAGE,
        resistances={branch: _r()},
        inductances={branch: _l()},
        models={branch: model},
        impedances={branch: impedance},
        admittances={branch: admittance},
        base_impedances={branch: impedance},
        base_admittances={branch: admittance},
        load_impedances={branch: impedance},
        load_admittances={branch: admittance},
    )


def _double_secondary(
    inner_value: complex, outer_value: complex
) -> ItmImSecondaryDto:
    """二重かご二次モデルDTOを作る。"""
    inner = ImSecondaryCageBranchType.INNER
    outer = ImSecondaryCageBranchType.OUTER
    model = ImSecondaryModelDto(name=ImSecondaryModelType.BASIC)
    impedances = {inner: _z(inner_value), outer: _z(outer_value)}
    admittances = {
        inner: _y_from_z(inner_value),
        outer: _y_from_z(outer_value),
    }
    models = {inner: model, outer: model}
    resistances = {inner: _r(), outer: _r()}
    inductances = {inner: _l(), outer: _l()}
    return ItmImSecondaryDto(
        cage_multiplicity=ImCageMultiplicityType.DOUBLE_CAGE,
        resistances=resistances,
        inductances=inductances,
        models=models,
        impedances=impedances,
        admittances=admittances,
        base_impedances=impedances,
        base_admittances=admittances,
        load_impedances=impedances,
        load_admittances=admittances,
    )


@pytest.mark.parametrize(
    ("topology", "expected_type"),
    [
        (ImCircuitType.L, LTypeSingleCageImTotalImmittanceSynthesizer),
        (ImCircuitType.T, TTypeSingleCageImTotalImmittanceSynthesizer),
    ],
)
def test_single_cage_factory_selects_synthesizer(
    topology: ImCircuitType,
    expected_type: type,
    config: IConfig,
    logger: ILogger,
) -> None:
    """単一かご factory が回路タイプごとの synthesizer を返す。"""
    synthesizer = (
        SingleCageImTotalImmittanceSynthesizerFactory.create_synthesizer(
            topology=topology,
            config=config,
            logger=logger,
        )
    )
    assert isinstance(synthesizer, expected_type)


@pytest.mark.parametrize(
    ("topology", "expected_type"),
    [
        (ImCircuitType.L, LTypeDoubleCageImTotalImmittanceSynthesizer),
        (ImCircuitType.T, TTypeDoubleCageImTotalImmittanceSynthesizer),
    ],
)
def test_double_cage_factory_selects_synthesizer(
    topology: ImCircuitType,
    expected_type: type,
    config: IConfig,
    logger: ILogger,
) -> None:
    """二重かご factory が回路タイプごとの synthesizer を返す。"""
    synthesizer = (
        DoubleCageImTotalImmittanceSynthesizerFactory.create_synthesizer(
            topology=topology,
            config=config,
            logger=logger,
        )
    )
    assert isinstance(synthesizer, expected_type)


def test_l_type_single_cage_synthesizes_parallel_excitation_and_series_branch(
    config: IConfig,
    logger: ILogger,
) -> None:
    """単一かごL型は Zm と (Z1+Z2) の並列合成を返す。"""
    synthesizer = LTypeSingleCageImTotalImmittanceSynthesizer.create(
        config=config,
        logger=logger,
    )

    result = synthesizer.synthesize(
        primary_model=_primary(1.0 + 0.0j),
        excitation_model=_excitation(6.0 + 0.0j),
        secondary_model=_single_secondary(2.0 + 0.0j),
    )

    np.testing.assert_allclose(result.impedance.value, [[2.0 + 0.0j]])
    np.testing.assert_allclose(result.admittance.value, [[0.5 + 0.0j]])


def test_t_type_single_cage_synthesizes_series_primary_and_parallel_branch(
    config: IConfig,
    logger: ILogger,
) -> None:
    """単一かごT型は Z1 + parallel(Zm, Z2) を返す。"""
    synthesizer = TTypeSingleCageImTotalImmittanceSynthesizer.create(
        config=config,
        logger=logger,
    )

    result = synthesizer.synthesize(
        primary_model=_primary(1.0 + 0.0j),
        excitation_model=_excitation(6.0 + 0.0j),
        secondary_model=_single_secondary(2.0 + 0.0j),
    )

    np.testing.assert_allclose(result.impedance.value, [[2.5 + 0.0j]])
    np.testing.assert_allclose(result.admittance.value, [[0.4 + 0.0j]])


def test_l_type_double_cage_synthesizes_with_equivalent_secondary(
    config: IConfig,
    logger: ILogger,
) -> None:
    """二重かごL型は INNER/OUTER の並列等価二次を使う。"""
    synthesizer = LTypeDoubleCageImTotalImmittanceSynthesizer.create(
        config=config,
        logger=logger,
    )

    result = synthesizer.synthesize(
        primary_model=_primary(1.0 + 0.0j),
        excitation_model=_excitation(6.0 + 0.0j),
        secondary_model=_double_secondary(2.0 + 0.0j, 3.0 + 0.0j),
    )

    expected_impedance = 1.0 / (1.0 / 6.0 + 1.0 / (1.0 + 1.2))
    expected_admittance = 1.0 / expected_impedance
    np.testing.assert_allclose(result.impedance.value, [[expected_impedance]])
    np.testing.assert_allclose(result.admittance.value, [[expected_admittance]])


def test_t_type_double_cage_synthesizes_with_equivalent_secondary(
    config: IConfig,
    logger: ILogger,
) -> None:
    """二重かごT型は Z1 + parallel(Zm, Z2_eq) を返す。"""
    synthesizer = TTypeDoubleCageImTotalImmittanceSynthesizer.create(
        config=config,
        logger=logger,
    )

    result = synthesizer.synthesize(
        primary_model=_primary(1.0 + 0.0j),
        excitation_model=_excitation(6.0 + 0.0j),
        secondary_model=_double_secondary(2.0 + 0.0j, 3.0 + 0.0j),
    )

    np.testing.assert_allclose(result.impedance.value, [[2.0 + 0.0j]])
    np.testing.assert_allclose(result.admittance.value, [[0.5 + 0.0j]])
