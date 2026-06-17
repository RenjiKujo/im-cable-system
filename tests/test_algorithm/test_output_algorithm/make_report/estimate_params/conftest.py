"""estimate_params make_report テスト用フィクスチャ。"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
import pytest

from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ArrayKey,
    ArrayLayoutDto,
    ImCableSystemName,
    ImPerformanceCurveCatalogDtos,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexVoltageDto,
    ArrayFrequencyDto,
    ArraySlipDto,
)
from im_cable_system.engine.shared.dto.output import OutputDto
from tests.test_algorithm.test_output_algorithm.make_report.estimate_params._estimate_params_report_helpers import (  # noqa: E501
    im_dto_stub,
    minimal_fit_summary,
    result_stub,
)


@pytest.fixture
def build_estimate_params_output_dto() -> Callable[..., OutputDto]:
    """estimate_params 向け最小 ``OutputDto`` を組み立てるファクトリ。"""

    def _build(
        *,
        with_summary: bool = True,
        reference_axes: list[ArrayKey] | None = None,
    ) -> OutputDto:
        axes = reference_axes or [
            ArrayKey.SLIP,
            ArrayKey.FREQUENCY,
            ArrayKey.INPUT_LINE_VOLTAGE,
        ]
        arrays = {
            ArrayKey.SLIP: ArraySlipDto(
                value=np.array([0.1, 0.2], dtype=np.float64),
                unit="-",
            ),
            ArrayKey.FREQUENCY: ArrayFrequencyDto(
                value=np.array([60.0], dtype=np.float64),
                unit="Hz",
            ),
            ArrayKey.INPUT_LINE_VOLTAGE: ArrayComplexVoltageDto(
                value=np.array([460.0 + 0.0j], dtype=np.complex128),
                unit="V",
            ),
        }
        layout = ArrayLayoutDto(
            arrays={key: arrays[key] for key in axes},
            reference_axes=axes,
        )
        return OutputDto(
            name=ImCableSystemName(value="SYS01"),
            array_layout=layout,
            im=im_dto_stub(),
            cable=None,
            result=result_stub(),  # type: ignore[arg-type]
            im_pc_catalogs=ImPerformanceCurveCatalogDtos(objects=[]),
            estimate_params_fit_summary=(
                minimal_fit_summary() if with_summary else None
            ),
        )

    return _build
