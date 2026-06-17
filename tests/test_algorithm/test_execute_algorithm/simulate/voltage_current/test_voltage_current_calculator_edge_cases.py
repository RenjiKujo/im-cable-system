"""電圧電流計算器のエッジケース・契約のテスト。

以下を直接（計算器／モデル DTO レベルで）検証する:
    - 二重かご計算器に単一かごモデルを渡すと ``ValueError`` となること
      （``_validate_secondary_branch_keys`` の契約）。
    - 地絡 (``is_ground_shorted``) を有限大アドミタンス近似として
      一般式で処理し、結果が有限（NaN/Inf を含まない）であること。
"""

from __future__ import annotations

from dataclasses import replace
from typing import cast

import numpy as np
import pytest

from im_cable_system.engine.algorithm.execute_algorithm.simulate.voltage_current.calculate_cable_voltage_current import (  # noqa: E501
    PieCableVoltageCurrentCalculator,
)
from im_cable_system.engine.algorithm.execute_algorithm.simulate.voltage_current.calculate_im_voltage_current import (  # noqa: E501
    DoubleCageImVoltageCurrentCalculator,
    SingleCageImVoltageCurrentCalculator,
)
from im_cable_system.engine.algorithm.execute_algorithm.simulate.voltage_current.orchestrate import (  # noqa: E501
    VoltageCurrentCalculationOrchestrator,
)
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ImCircuitType,
    ImSecondaryCageBranchType,
    PieCableGroundKey,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexAdmittanceDto,
    ArrayComplexCurrentDto,
    ArrayComplexImpedanceDto,
    ArrayComplexVoltageDto,
)
from tests.test_algorithm.test_execute_algorithm.fixtures.input_double_im_cable_system_data import (  # noqa: E501
    make_input_im_cable_system_dtos as make_double_cage_input_dtos,
)
from tests.test_algorithm.test_execute_algorithm.fixtures.input_single_im_cable_system_data import (  # noqa: E501
    make_input_im_cable_system_dtos,
)


@pytest.fixture
def single_cage_model_dto(build_model_orchestrator):
    """単一かごの最初の入力DTOから構築したモデルDTO。"""
    input_dto = make_input_im_cable_system_dtos().get_all()[0]
    return build_model_orchestrator.build(input_dto)


@pytest.fixture
def double_cage_model_dto(build_model_orchestrator):
    """二重かごのT型入力DTOから構築したモデルDTO。"""
    input_dtos = make_double_cage_input_dtos().get_all()
    input_dto = next(
        dto
        for dto in input_dtos
        if dto.im.im_series.circuit_type == ImCircuitType.T
    )
    return build_model_orchestrator.build(input_dto)


def _constant_admittance_like(
    base: ArrayComplexAdmittanceDto,
    magnitude: float,
) -> ArrayComplexAdmittanceDto:
    """既存アドミタンスDTOと同じ形状・単位で定数値DTOを作る。"""
    return ArrayComplexAdmittanceDto(
        value=np.full_like(base.value, magnitude, dtype=np.complex128),
        unit=base.get_unit(),
    )


def _assert_magnitude_allclose(
    value: np.ndarray,
    expected: float,
) -> None:
    """複素配列の絶対値が期待値と一致することを検証する。"""
    np.testing.assert_allclose(
        np.abs(value),
        expected,
        rtol=1e-12,
        atol=expected * 1e-12,
    )


class TestDoubleCageValidationContract:
    """二重かご計算器のキー検証契約のテスト。"""

    def test_raises_when_single_cage_model_given(
        self, config, logger, single_cage_model_dto
    ) -> None:
        """単一かごモデルを渡すと ValueError となること。"""
        calculator = DoubleCageImVoltageCurrentCalculator.create(
            config=config, logger=logger
        )
        shape = single_cage_model_dto.array_layout.shape
        dummy_voltage = ArrayComplexVoltageDto(
            value=np.ones(shape, dtype=np.complex128), unit="V"
        )
        dummy_current = ArrayComplexCurrentDto(
            value=np.ones(shape, dtype=np.complex128), unit="A"
        )

        with pytest.raises(ValueError):
            calculator.calculate(
                input_phase_voltage=dummy_voltage,
                input_phase_current=dummy_current,
                im_model=single_cage_model_dto.im,
            )


class TestPieCableGroundShortApproximation:
    """地絡（有限大アドミタンス近似）の処理のテスト。"""

    def _make_ground_shorted_model_dto(self, model_dto, eps: float):
        """既存モデルの地絡枝を ``Y=1/eps`` の有限大近似に置換する。"""
        immittance = model_dto.cable.cable_immittance
        large_admittance = 1.0 / eps
        small_impedance = eps

        ground_admittance = {
            key: ArrayComplexAdmittanceDto(
                value=np.full_like(
                    adm.value, large_admittance, dtype=np.complex128
                ),
                unit=adm.get_unit(),
            )
            for key, adm in immittance.ground_admittance.items()
        }
        ground_impedance = {
            key: ArrayComplexImpedanceDto(
                value=np.full_like(
                    imp.value, small_impedance, dtype=np.complex128
                ),
                unit=imp.get_unit(),
            )
            for key, imp in immittance.ground_impedance.items()
        }
        shorted_immittance = replace(
            immittance,
            ground_admittance=ground_admittance,
            ground_impedance=ground_impedance,
            is_ground_insulated=False,
            is_ground_shorted=True,
            is_conductor_ideal=False,
        )
        shorted_cable = replace(
            model_dto.cable, cable_immittance=shorted_immittance
        )
        return replace(model_dto, cable=shorted_cable)

    def test_ground_short_produces_finite_results(
        self, config, logger, single_cage_model_dto
    ) -> None:
        """地絡近似でも結果が有限（NaN/Inf を含まない）であること。"""
        eps = config.numerical_guard_config.eps
        shorted_model = self._make_ground_shorted_model_dto(
            single_cage_model_dto, eps=eps
        )

        orchestrator = VoltageCurrentCalculationOrchestrator.create(
            config=config, logger=logger
        )
        result = orchestrator.calculate(model_dto=shorted_model)
        cable_vc = result.cable_voltage_current

        for value in (
            cable_vc.input_phase_voltage.value,
            cable_vc.input_phase_current.value,
            cable_vc.end_point_phase_voltage.value,
            cable_vc.end_point_phase_current.value,
            cable_vc.ground_current[PieCableGroundKey.UPSTREAM].value,
            cable_vc.ground_current[PieCableGroundKey.DOWNSTREAM].value,
        ):
            assert not np.any(np.isnan(value))
            assert not np.any(np.isinf(value))

    def test_ground_short_uses_general_path(
        self, config, logger, single_cage_model_dto
    ) -> None:
        """地絡は専用分岐ではなく一般式で扱われること（直接計算器を検証）。"""
        eps = config.numerical_guard_config.eps
        shorted_model = self._make_ground_shorted_model_dto(
            single_cage_model_dto, eps=eps
        )
        immittance = shorted_model.cable.cable_immittance
        # 一般式が選ばれる前提として、完全絶縁でも理想導体でもないことを確認する
        assert immittance.is_ground_shorted is True
        assert immittance.is_ground_insulated is False
        assert immittance.is_conductor_ideal is False

        calculator = PieCableVoltageCurrentCalculator.create(
            config=config, logger=logger
        )
        shape = shorted_model.array_layout.shape
        input_line_voltage = ArrayComplexVoltageDto(
            value=np.full(shape, 200.0, dtype=np.complex128), unit="V"
        )
        result = calculator.calculate(
            input_line_voltage=input_line_voltage,
            cable_model=shorted_model.cable,
            system_model=shorted_model.system,
        )

        # 地絡では上流地絡電流が大きく（有限）流れる
        ground_up = result.ground_current[PieCableGroundKey.UPSTREAM].value
        assert not np.any(np.isnan(ground_up))
        assert not np.any(np.isinf(ground_up))
        assert np.all(np.abs(ground_up) > 0.0)


class TestVoltageCurrentBoundaryClamp:
    """eps / max_mag 境界値そのものを狙ったクランプテスト。"""

    @pytest.mark.parametrize(
        ("boundary_name", "expected_name"),
        [
            ("eps", "eps"),
            ("max_mag", "max_mag"),
        ],
    )
    def test_pie_cable_ground_admittance_boundary_is_clamped(
        self,
        config,
        logger,
        single_cage_model_dto,
        boundary_name: str,
        expected_name: str,
    ) -> None:
        """地絡アドミタンスが境界値ちょうどで電流クランプされること。"""
        eps = config.numerical_guard_config.eps
        max_mag = 1.0 / eps
        boundary = eps if boundary_name == "eps" else max_mag
        expected = eps if expected_name == "eps" else max_mag

        immittance = single_cage_model_dto.cable.cable_immittance
        ground_admittance = {
            key: _constant_admittance_like(admittance, boundary)
            for key, admittance in immittance.ground_admittance.items()
        }
        boundary_immittance = replace(
            immittance,
            ground_admittance=ground_admittance,
            is_ground_insulated=False,
            is_conductor_ideal=False,
        )
        boundary_cable = replace(
            single_cage_model_dto.cable,
            cable_immittance=boundary_immittance,
        )
        boundary_model = replace(single_cage_model_dto, cable=boundary_cable)

        calculator = PieCableVoltageCurrentCalculator.create(
            config=config,
            logger=logger,
        )
        input_line_voltage = ArrayComplexVoltageDto(
            value=np.full(
                boundary_model.array_layout.shape,
                200.0,
                dtype=np.complex128,
            ),
            unit="V",
        )

        result = calculator.calculate(
            input_line_voltage=input_line_voltage,
            cable_model=boundary_model.cable,
            system_model=boundary_model.system,
        )

        ground_up = result.ground_current[PieCableGroundKey.UPSTREAM].value
        _assert_magnitude_allclose(ground_up, expected)

    @pytest.mark.parametrize(
        ("boundary_name", "expected_name"),
        [
            ("eps", "eps"),
            ("max_mag", "max_mag"),
        ],
    )
    def test_single_cage_excitation_admittance_boundary_is_clamped(
        self,
        config,
        logger,
        single_cage_model_dto,
        boundary_name: str,
        expected_name: str,
    ) -> None:
        """励磁アドミタンスが境界値ちょうどで電流クランプされること。"""
        eps = config.numerical_guard_config.eps
        max_mag = 1.0 / eps
        boundary = eps if boundary_name == "eps" else max_mag
        expected = eps if expected_name == "eps" else max_mag

        im_model = single_cage_model_dto.im
        circuit_info = replace(
            im_model.circuit_info, circuit_type=ImCircuitType.T
        )
        excitation_model = replace(
            im_model.excitation_model,
            admittance=_constant_admittance_like(
                im_model.excitation_admittance,
                boundary,
            ),
        )
        boundary_im_model = replace(
            im_model,
            circuit_info=circuit_info,
            excitation_model=excitation_model,
        )
        shape = single_cage_model_dto.array_layout.shape
        input_phase_voltage = ArrayComplexVoltageDto(
            value=np.full(shape, 200.0, dtype=np.complex128),
            unit="V",
        )
        input_phase_current = ArrayComplexCurrentDto(
            value=np.ones(shape, dtype=np.complex128),
            unit="A",
        )

        calculator = SingleCageImVoltageCurrentCalculator.create(
            config=config,
            logger=logger,
        )
        result = calculator.calculate(
            input_phase_voltage=input_phase_voltage,
            input_phase_current=input_phase_current,
            im_model=boundary_im_model,
        )

        _assert_magnitude_allclose(result.im_excitation_current.value, expected)

    @pytest.mark.parametrize(
        ("boundary_name", "expected_name"),
        [
            ("eps", "max_mag"),
            ("max_mag", "eps"),
        ],
    )
    def test_double_cage_parallel_secondary_admittance_boundary_is_clamped(
        self,
        config,
        logger,
        double_cage_model_dto,
        boundary_name: str,
        expected_name: str,
    ) -> None:
        """二次並列合成の境界値で等価インピーダンスが反転クランプされること。"""
        eps = config.numerical_guard_config.eps
        max_mag = 1.0 / eps
        boundary = eps if boundary_name == "eps" else max_mag
        expected = eps if expected_name == "eps" else max_mag

        sec = double_cage_model_dto.im.secondary_model
        inner = ImSecondaryCageBranchType.INNER
        outer = ImSecondaryCageBranchType.OUTER
        inner_admittance = _constant_admittance_like(
            sec.admittances[inner],
            boundary,
        )
        outer_admittance = _constant_admittance_like(
            sec.admittances[outer],
            boundary,
        )
        calculator = cast(
            DoubleCageImVoltageCurrentCalculator,
            DoubleCageImVoltageCurrentCalculator.create(
                config=config,
                logger=logger,
            ),
        )

        impedance = calculator._calculate_parallel_equivalent_impedance(  # noqa: SLF001
            inner_admittance=inner_admittance,
            outer_admittance=outer_admittance,
            eps=eps,
            max_mag=max_mag,
        )

        _assert_magnitude_allclose(impedance.value, expected)
