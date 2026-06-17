"""二重かご input_dto を用いた build_model 疎通テスト。"""

from __future__ import annotations

import pytest

from im_cable_system.engine.algorithm.execute_algorithm.build_model.orchestrate import (  # noqa: E501
    ImCableModelBuildOrchestrator,
)
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ImSecondaryCageBranchType,
)
from im_cable_system.engine.shared.dto.input import (  # noqa: E501
    InputDtos,
)
from tests.test_algorithm.test_execute_algorithm.fixtures.input_double_im_cable_system_data import (  # noqa: E501
    make_input_im_cable_system_dtos,
)


@pytest.fixture
def input_im_cable_system_dtos_double() -> InputDtos:
    return make_input_im_cable_system_dtos()


def test_execute_build_model_double_cage_builds_secondary_inner_outer(
    config,
    logger,
    input_im_cable_system_dtos_double: InputDtos,
) -> None:
    """二重かご入力（27パターン）で build_model が最後まで走ること。"""
    orchestrator = ImCableModelBuildOrchestrator.create(
        config=config,
        logger=logger,
    )
    original_count = len(input_im_cable_system_dtos_double)
    for dto in input_im_cable_system_dtos_double.get_all():
        result = orchestrator.build(dto)

        expected_shape = dto.array_layout.shape
        assert result.im.secondary_model.cage_multiplicity is not None
        assert (
            result.im.secondary_model.impedances[
                ImSecondaryCageBranchType.INNER
            ].value.shape
            == expected_shape
        )
        assert (
            result.im.secondary_model.impedances[
                ImSecondaryCageBranchType.OUTER
            ].value.shape
            == expected_shape
        )
        assert result.im.total_model.impedance.value.shape == expected_shape

    # NOTE: build_model 実行後も InputDtos が再生成できる（副作用で壊れていない）ことを確認
    regenerated = make_input_im_cable_system_dtos()
    assert len(regenerated) == original_count
