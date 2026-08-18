"""IM パラメータフィットストラテジファクトリーと記述子収集の単体テスト。"""

from __future__ import annotations

from dataclasses import fields, replace

import pytest

from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.collect_descriptors.cable import (  # noqa: E501
    collect_cable_fittable_descriptors,
)
from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.collect_descriptors.im import (  # noqa: E501
    DoubleCageImParameterFitStrategy,
    ImParameterFitStrategyFactory,
    SingleCageImParameterFitStrategy,
)
from im_cable_system.engine.shared.config import IConfig, load_yaml_root_dict
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    CableConductorModelDto,
    CableSectionDtos,
    ConductorModelType,
    FloatParamDto,
    FloatParamDtos,
    ImCageMultiplicityType,
    ImFrictionWindageModelDto,
    ImFrictionWindageModelType,
    ImSeriesDto,
    ImStrayLoadModelDto,
    ImStrayLoadModelType,
)
from im_cable_system.engine.shared.dto.input import (
    InputDto,
    InputDtos,
)
from im_cable_system.engine.shared.estimate_params_fit_spec import (  # noqa: E501
    CableParameterFitDescriptorBounds,
    ImParameterFitDescriptorBounds,
)


def _input_with_cage(
    input_dtos: InputDtos,
    cage_multiplicity: ImCageMultiplicityType,
) -> InputDto:
    """指定したかご種別を持つ InputDto を返す。"""
    for input_dto in input_dtos.get_all():
        im_series = input_dto.im.im_series
        if im_series is not None and (
            im_series.cage_multiplicity == cage_multiplicity
        ):
            return input_dto
    raise AssertionError(f"InputDto が見つかりません: {cage_multiplicity}")


def _input_with_cable(input_dtos: InputDtos) -> InputDto:
    """BASIC ケーブルの先頭 1 セクションだけを持つ InputDto を返す。"""
    for input_dto in input_dtos.get_all():
        cable = input_dto.cable
        if cable is not None and (
            cable.conductor_model.name == ConductorModelType.BASIC
        ):
            first_section = cable.sections.get_all()[0]
            one_section_cable = replace(
                cable,
                sections=CableSectionDtos(objects=[first_section]),
            )
            return replace(input_dto, cable=one_section_cable)
    raise AssertionError("BASIC ケーブル付き InputDto が見つかりません")


def _load_im_bounds(config: IConfig) -> ImParameterFitDescriptorBounds:
    """テスト設定の IM bounds YAML から境界 DTO を作る。"""
    document = load_yaml_root_dict(config.get_im_bounds_and_init_file_path())
    return ImParameterFitDescriptorBounds.from_estimation_document(document)


def _load_cable_bounds(config: IConfig) -> CableParameterFitDescriptorBounds:
    """テスト設定のケーブル bounds YAML から境界 DTO を作る。"""
    document = load_yaml_root_dict(config.get_cable_bounds_and_init_file_path())
    return CableParameterFitDescriptorBounds.from_estimation_document(document)


class TestImParameterFitStrategyFactory:
    """ImParameterFitStrategyFactory のテスト。"""

    def test_create_returns_single_cage_strategy_for_estimate_params_series(
        self,
        input_im_cable_system_dtos: InputDtos,
    ) -> None:
        """単一かご IM は Single ストラテジになる。"""
        im_series = _input_with_cage(
            input_im_cable_system_dtos,
            ImCageMultiplicityType.SINGLE_CAGE,
        ).im.im_series
        assert im_series is not None
        assert im_series.cage_multiplicity == ImCageMultiplicityType.SINGLE_CAGE
        strategy = ImParameterFitStrategyFactory.create(im_series)
        assert isinstance(strategy, SingleCageImParameterFitStrategy)

    def test_create_returns_double_cage_strategy_for_double_cage_series(
        self,
        input_im_cable_system_dtos: InputDtos,
    ) -> None:
        """二重かご IM は Double ストラテジになる。"""
        im_series = _input_with_cage(
            input_im_cable_system_dtos,
            ImCageMultiplicityType.DOUBLE_CAGE,
        ).im.im_series
        assert im_series is not None
        assert im_series.cage_multiplicity == ImCageMultiplicityType.DOUBLE_CAGE
        strategy = ImParameterFitStrategyFactory.create(im_series)
        assert isinstance(strategy, DoubleCageImParameterFitStrategy)

    def test_create_raises_when_secondary_keys_mismatch_multiplicity(
        self,
        input_im_cable_system_dtos: InputDtos,
    ) -> None:
        """cage_multiplicity と secondary_models のキーが一致しない場合は ValueError。"""
        im_series = input_im_cable_system_dtos.get_all()[0].im.im_series
        assert im_series is not None
        invalid = object.__new__(ImSeriesDto)
        for field in fields(ImSeriesDto):
            object.__setattr__(
                invalid,
                field.name,
                getattr(im_series, field.name),
            )
        object.__setattr__(
            invalid,
            "cage_multiplicity",
            ImCageMultiplicityType.DOUBLE_CAGE,
        )
        with pytest.raises(ValueError, match="cage_multiplicity"):
            ImParameterFitStrategyFactory.create(invalid)

    def test_double_cage_strategy_type(self) -> None:
        """二重かごストラテジの create がインターフェイス実装を返す。"""
        strategy = DoubleCageImParameterFitStrategy.create()
        assert isinstance(strategy, DoubleCageImParameterFitStrategy)


class TestFittableDescriptorsOrchestratorOrdering:
    """execute と同じ規則で IM 記述子＋任意のケーブル記述子を並べたときの件数。

    （オーケストレーター内の直書きロジックと整合することを単体で保証する。）
    """

    def test_im_count_equals_strategy_length_without_cable(
        self,
        input_im_cable_system_dtos: InputDtos,
        config: IConfig,
    ) -> None:
        """ケーブル無しでは全記述子が IM 部と一致する。"""
        im_series = _input_with_cage(
            input_im_cable_system_dtos,
            ImCageMultiplicityType.SINGLE_CAGE,
        ).im.im_series
        assert im_series is not None
        strategy = ImParameterFitStrategyFactory.create(im_series)
        im_bounds = _load_im_bounds(config)
        im_descriptors = strategy.collect_im_descriptors(
            im_series,
            im_bounds,
        )
        descriptors = list(im_descriptors)
        assert len(descriptors) == len(im_descriptors)

    def test_with_cable_appends_four_descriptors(
        self,
        input_im_cable_system_dtos: InputDtos,
        config: IConfig,
    ) -> None:
        """ケーブルありでは末尾に π 型 4 記述子が付く。"""
        input_dto = _input_with_cable(input_im_cable_system_dtos)
        im_series = input_dto.im.im_series
        assert im_series is not None
        assert input_dto.cable is not None
        strategy = ImParameterFitStrategyFactory.create(im_series)
        im_bounds = _load_im_bounds(config)
        cable_bounds = _load_cable_bounds(config)
        im_descriptors = strategy.collect_im_descriptors(
            im_series,
            im_bounds,
        )
        im_descriptor_count = len(im_descriptors)
        descriptors = list(im_descriptors)
        descriptors.extend(
            collect_cable_fittable_descriptors(
                input_dto.cable,
                cable_bounds,
            )
        )
        assert len(descriptors) == im_descriptor_count + 4

    def test_with_skin_effect_conductor_appends_eight_descriptors(
        self,
        input_im_cable_system_dtos: InputDtos,
        config: IConfig,
    ) -> None:
        """皮膚効果導体モデルでは π 4 + 係数 4 記述子が付く。"""
        input_dto = _input_with_cable(input_im_cable_system_dtos)
        im_series = input_dto.im.im_series
        assert im_series is not None
        assert input_dto.cable is not None
        skin_model = CableConductorModelDto(
            name=ConductorModelType.FREQUENCY_DEPENDENT_SKIN_EFFECT_V1,
            params=FloatParamDtos(
                objects=[
                    FloatParamDto(name="alpha_conductor_r", value=1.0),
                    FloatParamDto(name="beta_conductor_r", value=1.0),
                    FloatParamDto(name="alpha_conductor_x", value=1.0),
                    FloatParamDto(name="beta_conductor_x", value=1.0),
                ],
            ),
        )
        cable_with_skin = replace(
            input_dto.cable,
            conductor_model=skin_model,
        )
        strategy = ImParameterFitStrategyFactory.create(im_series)
        im_bounds = _load_im_bounds(config)
        cable_bounds = _load_cable_bounds(config)
        im_descriptors = strategy.collect_im_descriptors(
            im_series,
            im_bounds,
        )
        im_descriptor_count = len(im_descriptors)
        descriptors = list(im_descriptors)
        descriptors.extend(
            collect_cable_fittable_descriptors(
                cable_with_skin,
                cable_bounds,
            )
        )
        assert len(descriptors) == im_descriptor_count + 8

    def test_config_exposes_yaml_backed_fit_bounds(
        self,
        config: IConfig,
    ) -> None:
        """im_descriptor_bounds_and_init.yaml 由来の IM 境界を読み込める。"""
        im_bounds = _load_im_bounds(config)
        lb, ub = im_bounds.im_fixed("primary_resistance")
        # im_descriptor_bounds_and_init.yaml（primary.rl_parameters）
        assert lb == pytest.approx(1.0e-2)
        assert ub == pytest.approx(1.0)


class TestShaftOutputDeductionDescriptorCount:
    """摩擦・風損／漂遊負荷損の有無 4 パターンで記述子が 0/1/1/2 個増える。"""

    @pytest.mark.parametrize(
        ("friction_windage_model", "stray_load_model", "expected_extra"),
        [
            (
                ImFrictionWindageModelDto(name=ImFrictionWindageModelType.NONE),
                ImStrayLoadModelDto(name=ImStrayLoadModelType.NONE),
                0,
            ),
            (
                ImFrictionWindageModelDto(
                    name=ImFrictionWindageModelType.CONSTANT_V1,
                    params=FloatParamDtos(
                        objects=[
                            FloatParamDto(name="k_friction_windage", value=0.01)
                        ]
                    ),
                ),
                ImStrayLoadModelDto(name=ImStrayLoadModelType.NONE),
                1,
            ),
            (
                ImFrictionWindageModelDto(name=ImFrictionWindageModelType.NONE),
                ImStrayLoadModelDto(
                    name=ImStrayLoadModelType.CURRENT_DEPENDENT_QUADRATIC_V1,
                    params=FloatParamDtos(
                        objects=[
                            FloatParamDto(name="k_stray_load", value=0.005)
                        ]
                    ),
                ),
                1,
            ),
            (
                ImFrictionWindageModelDto(
                    name=ImFrictionWindageModelType.CONSTANT_V1,
                    params=FloatParamDtos(
                        objects=[
                            FloatParamDto(name="k_friction_windage", value=0.01)
                        ]
                    ),
                ),
                ImStrayLoadModelDto(
                    name=ImStrayLoadModelType.CURRENT_DEPENDENT_QUADRATIC_V1,
                    params=FloatParamDtos(
                        objects=[
                            FloatParamDto(name="k_stray_load", value=0.005)
                        ]
                    ),
                ),
                2,
            ),
        ],
        ids=[
            "none_none",
            "constant_none",
            "none_quadratic",
            "constant_quadratic",
        ],
    )
    def test_descriptor_count_matches_pattern(
        self,
        input_im_cable_system_dtos: InputDtos,
        config: IConfig,
        friction_windage_model: ImFrictionWindageModelDto,
        stray_load_model: ImStrayLoadModelDto,
        expected_extra: int,
    ) -> None:
        baseline_series = _input_with_cage(
            input_im_cable_system_dtos,
            ImCageMultiplicityType.SINGLE_CAGE,
        ).im.im_series
        assert baseline_series is not None
        im_bounds = _load_im_bounds(config)

        baseline_strategy = ImParameterFitStrategyFactory.create(
            baseline_series
        )
        baseline_count = len(
            baseline_strategy.collect_im_descriptors(baseline_series, im_bounds)
        )

        variant_series = replace(
            baseline_series,
            friction_windage_model=friction_windage_model,
            stray_load_model=stray_load_model,
        )
        variant_strategy = ImParameterFitStrategyFactory.create(variant_series)
        variant_count = len(
            variant_strategy.collect_im_descriptors(variant_series, im_bounds)
        )

        assert variant_count - baseline_count == expected_extra
