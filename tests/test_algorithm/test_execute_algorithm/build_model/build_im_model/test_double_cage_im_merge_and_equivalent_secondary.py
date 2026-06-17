"""二重かご: 二次 DTO マージと等価二次イミタンスの単体テスト。"""

from __future__ import annotations

import numpy as np
import pytest

from im_cable_system.engine.algorithm.execute_algorithm.build_model.build_im_model import (  # noqa: E402,E501
    merge_double_cage_itm_im_secondary_dto,
)
from im_cable_system.engine.algorithm.execute_algorithm.build_model.build_im_model.im_total_immittance import (  # noqa: E402,E501
    DoubleCageImTotalImmittanceSynthesizerFactory,
)
from im_cable_system.engine.algorithm.execute_algorithm.build_model.build_im_model.im_total_immittance.double_cage_im_total_immittance_synthesizer import (  # noqa: E402,E501
    _equivalent_secondary_immittance_for_double_cage_total_synthesis,
)
from im_cable_system.engine.domain.physics.electrical import (  # noqa: E402
    admittance_from_impedance,
    combine_admittance_parallel,
    impedance_from_admittance,
)
from im_cable_system.engine.shared.dto.generic.im_cable_system import (  # noqa: E402
    ImCageMultiplicityType,
    ImCircuitType,
    ImSecondaryCageBranchType,
    ImSecondaryModelDto,
    ImSecondaryModelType,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (  # noqa: E402
    ArrayComplexImpedanceDto,
    FloatInductanceDto,
    FloatResistanceDto,
)
from im_cable_system.engine.shared.dto.itm import (  # noqa: E402
    ItmImSecondaryDto,
)

# テスト用の数値ガードしきい値（domain 既定値撤廃に伴いテストから明示注入）。
_EPS: float = 1e-12
_MAX_MAG: float = 1.0 / _EPS


def _scalar_z(value_complex: complex) -> ArrayComplexImpedanceDto:
    return ArrayComplexImpedanceDto(
        value=np.array([[value_complex]], dtype=np.complex128),
        unit="Ω",
    )


def _branch_secondary_dto(
    branch: ImSecondaryCageBranchType,
    z_total: ArrayComplexImpedanceDto,
) -> ItmImSecondaryDto:
    sm = ImSecondaryModelDto(
        name=ImSecondaryModelType.BASIC,
        params=None,
    )
    y_total = admittance_from_impedance(z_total, eps=_EPS, max_mag=_MAX_MAG)
    return ItmImSecondaryDto(
        cage_multiplicity=ImCageMultiplicityType.DOUBLE_CAGE,
        resistances={branch: FloatResistanceDto(value=1.0, unit="Ω")},
        inductances={branch: FloatInductanceDto(value=1.0, unit="H")},
        models={branch: sm},
        impedances={branch: z_total},
        admittances={branch: y_total},
        base_impedances={branch: z_total},
        base_admittances={branch: y_total},
        load_impedances={branch: z_total},
        load_admittances={branch: y_total},
    )


def test_merge_double_cage_itm_im_secondary_dto_merges_keys() -> None:
    """INNER/OUTER の部分 DTO をマージすると両枝を持つ完全形になる。"""
    z_in = _scalar_z(2.0 + 0.0j)
    z_out = _scalar_z(1.0 + 0.0j)
    inner = _branch_secondary_dto(ImSecondaryCageBranchType.INNER, z_in)
    outer = _branch_secondary_dto(ImSecondaryCageBranchType.OUTER, z_out)
    merged = merge_double_cage_itm_im_secondary_dto(
        inner_partial=inner,
        outer_partial=outer,
    )
    assert merged.cage_multiplicity == ImCageMultiplicityType.DOUBLE_CAGE
    assert set(merged.models.keys()) == {
        ImSecondaryCageBranchType.INNER,
        ImSecondaryCageBranchType.OUTER,
    }


def test_merge_rejects_swapped_partials() -> None:
    """INNER 専用でない inner_partial は ValueError。"""
    z = _scalar_z(1.0 + 0.0j)
    wrong = _branch_secondary_dto(ImSecondaryCageBranchType.OUTER, z)
    inner_ok = _branch_secondary_dto(ImSecondaryCageBranchType.INNER, z)
    with pytest.raises(ValueError, match="inner_partial"):
        merge_double_cage_itm_im_secondary_dto(
            inner_partial=wrong,
            outer_partial=inner_ok,
        )


def test_equivalent_secondary_double_cage_parallel_admittance(
    config,
) -> None:
    """等価二次は INNER/OUTER アドミタンスの並列和に一致する。"""
    eps = config.numerical_guard_config.eps
    max_mag = 1.0 / eps
    z_in = _scalar_z(2.0 + 0.0j)
    z_out = _scalar_z(1.0 + 0.0j)
    inner = _branch_secondary_dto(ImSecondaryCageBranchType.INNER, z_in)
    outer = _branch_secondary_dto(ImSecondaryCageBranchType.OUTER, z_out)
    merged = merge_double_cage_itm_im_secondary_dto(
        inner_partial=inner,
        outer_partial=outer,
    )
    z_eq, y_eq = (
        _equivalent_secondary_immittance_for_double_cage_total_synthesis(
            merged,
            eps=eps,
            max_mag=max_mag,
        )
    )
    y_expect = combine_admittance_parallel(
        inner.admittances[ImSecondaryCageBranchType.INNER],
        outer.admittances[ImSecondaryCageBranchType.OUTER],
        eps=eps,
        max_mag=max_mag,
    )
    z_expect = impedance_from_admittance(
        y_expect,
        eps=eps,
        max_mag=max_mag,
    )
    np.testing.assert_allclose(
        z_eq.get_value(),
        z_expect.get_value(),
        rtol=0.0,
        atol=1e-12,
    )
    np.testing.assert_allclose(
        y_eq.get_value(),
        y_expect.get_value(),
        rtol=0.0,
        atol=1e-12,
    )


def test_double_cage_factory_returns_synthesizer(config, logger) -> None:
    """二重かごファクトリが L/T 合成器を返す。"""
    l_syn = DoubleCageImTotalImmittanceSynthesizerFactory.create_synthesizer(
        topology=ImCircuitType.L,
        config=config,
        logger=logger,
    )
    t_syn = DoubleCageImTotalImmittanceSynthesizerFactory.create_synthesizer(
        topology=ImCircuitType.T,
        config=config,
        logger=logger,
    )
    # 具象クラスの型は固定しすぎず、「合成器が返る」ことのみ確認する
    assert l_syn is not None
    assert t_syn is not None


def test_itm_im_secondary_double_cage_single_branch_allowed() -> None:
    """二重かごでも 1 枝のみの辞書は __post_init__ を通過する。"""
    z = _scalar_z(1.0 + 0.0j)
    dto = _branch_secondary_dto(ImSecondaryCageBranchType.INNER, z)
    assert ImSecondaryCageBranchType.INNER in dto.admittances


def test_itm_im_secondary_rejects_empty_dict() -> None:
    """空辞書は ValueError。"""
    with pytest.raises(ValueError, match="空"):
        ItmImSecondaryDto(
            cage_multiplicity=ImCageMultiplicityType.SINGLE_CAGE,
            resistances={},
            inductances={},
            models={},
            impedances={},
            admittances={},
            base_impedances={},
            base_admittances={},
            load_impedances={},
            load_admittances={},
        )
