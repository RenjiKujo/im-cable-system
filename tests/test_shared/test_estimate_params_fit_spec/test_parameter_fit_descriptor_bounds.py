"""Tests for IM / Cable parameter-fit descriptor bounds.

``from_estimation_document`` の解釈（フラット / レガシー
``im_cable_system`` ルート・必須キー欠損エラー）を担保する。
"""

from __future__ import annotations

from typing import Any

import pytest

from im_cable_system.engine.shared.estimate_params_fit_spec import (  # noqa: E501
    CableParameterFitDescriptorBounds,
    ImParameterFitDescriptorBounds,
)

_MIDPOINT_INIT: dict[str, str] = {"method": "midpoint"}


def _flat_im_document() -> dict[str, Any]:
    return {
        "version": 3,
        "primary": {
            "fit_parameters": {
                "primary_resistance": {
                    "bounds": {"lb": 0.35, "ub": 0.85},
                    "init": _MIDPOINT_INIT,
                },
                "primary_inductance": {
                    "bounds": {"lb": 0.045, "ub": 0.082},
                    "init": _MIDPOINT_INIT,
                },
            },
            "model_parameters": {
                "SLIP_DEPENDENT_LEAKAGE_SATURATION_V1": {
                    "params": {
                        "alpha_primary_r": {
                            "bounds": {"lb": 0.05, "ub": 2.5},
                            "init": _MIDPOINT_INIT,
                        },
                    }
                }
            },
        },
        "excitation": {
            "fit_parameters": {
                "excitation_resistance": {
                    "bounds": {"lb": 260.0, "ub": 480.0},
                    "init": _MIDPOINT_INIT,
                },
                "excitation_inductance": {
                    "bounds": {"lb": 0.015, "ub": 0.050},
                    "init": _MIDPOINT_INIT,
                },
            },
        },
        "secondary": {
            "fit_parameters": {
                "secondary_resistance": {
                    "bounds": {"lb": 0.05, "ub": 0.40},
                    "init": _MIDPOINT_INIT,
                },
                "secondary_inductance": {
                    "bounds": {"lb": 0.003, "ub": 0.008},
                    "init": _MIDPOINT_INIT,
                },
            },
        },
    }


def _flat_cable_document() -> dict[str, Any]:
    return {
        "version": 1,
        "conductor": {
            "fit_parameters": {
                "conductor_resistance_per_length": {
                    "bounds": {"lb": 1e-5, "ub": 0.5},
                    "init": _MIDPOINT_INIT,
                },
                "conductor_inductance_per_length": {
                    "bounds": {"lb": 1e-7, "ub": 1e-6},
                    "init": _MIDPOINT_INIT,
                },
            },
            "model_parameters": {
                "CURRENT_DEPENDENT_V1": {
                    "params": {
                        "alpha_cond_r": {
                            "bounds": {"lb": 0.1, "ub": 1.5},
                            "init": _MIDPOINT_INIT,
                        },
                    }
                }
            },
        },
        "ground": {
            "fit_parameters": {
                "ground_resistance_length": {
                    "bounds": {"lb": 1e9, "ub": 1e10},
                    "init": _MIDPOINT_INIT,
                },
                "ground_capacitance_per_length": {
                    "bounds": {"lb": 1e-10, "ub": 0.5},
                    "init": _MIDPOINT_INIT,
                },
            }
        },
    }


class TestImBoundsErrors:
    """IM bounds YAML の欠損・未知キーエラー。"""

    def test_unknown_model_param_raises(self) -> None:
        bounds = ImParameterFitDescriptorBounds.from_estimation_document(
            _flat_im_document()
        )
        with pytest.raises(KeyError, match="unknown IM primary model"):
            bounds.im_model_param(
                subsystem="primary",
                model_type_name="UNKNOWN_MODEL",
                param_name="unknown",
            )

    def test_missing_fixed_key_raises(self) -> None:
        document = _flat_im_document()
        del document["secondary"]["fit_parameters"]["secondary_inductance"]
        with pytest.raises(
            ValueError,
            match="IM bounds YAML missing required fixed parameters",
        ):
            ImParameterFitDescriptorBounds.from_estimation_document(document)


class TestImFromEstimationDocument:
    """フラット / レガシー / 欠損ケース。"""

    def test_flat_document_resolves_fixed_params(self) -> None:
        bounds = ImParameterFitDescriptorBounds.from_estimation_document(
            _flat_im_document()
        )
        assert bounds.im_fixed("primary_resistance") == (0.35, 0.85)
        assert bounds.im_fixed("excitation_resistance") == (260.0, 480.0)
        assert bounds.im_fixed("secondary_resistance") == (0.05, 0.40)
        assert bounds.im_fixed("secondary_inductance") == (0.003, 0.008)

    def test_flat_document_resolves_model_params(self) -> None:
        bounds = ImParameterFitDescriptorBounds.from_estimation_document(
            _flat_im_document()
        )
        assert bounds.im_model_param(
            subsystem="primary",
            model_type_name="SLIP_DEPENDENT_LEAKAGE_SATURATION_V1",
            param_name="alpha_primary_r",
        ) == (0.05, 2.5)

    def test_flat_document_missing_model_param_raises(self) -> None:
        bounds = ImParameterFitDescriptorBounds.from_estimation_document(
            _flat_im_document()
        )
        with pytest.raises(
            KeyError,
            match="missing bounds/init for IM primary model parameter",
        ):
            bounds.im_model_param(
                subsystem="primary",
                model_type_name="SLIP_DEPENDENT_LEAKAGE_SATURATION_V1",
                param_name="beta_primary_x",
            )

    def test_legacy_im_cable_system_subtree_takes_precedence(self) -> None:
        legacy_doc = {
            "version": 1,
            "im_cable_system": {
                "im": {
                    "primary": {
                        "fit_parameters": {
                            "primary_resistance": {
                                "bounds": {"lb": 0.50, "ub": 0.55},
                                "init": _MIDPOINT_INIT,
                            },
                            "primary_inductance": {
                                "bounds": {"lb": 0.01, "ub": 0.02},
                                "init": _MIDPOINT_INIT,
                            },
                        }
                    },
                    "excitation": {
                        "fit_parameters": {
                            "excitation_resistance": {
                                "bounds": {"lb": 100.0, "ub": 200.0},
                                "init": _MIDPOINT_INIT,
                            },
                            "excitation_inductance": {
                                "bounds": {"lb": 0.03, "ub": 0.04},
                                "init": _MIDPOINT_INIT,
                            },
                        }
                    },
                    "secondary": {
                        "fit_parameters": {
                            "secondary_resistance": {
                                "bounds": {"lb": 0.10, "ub": 0.20},
                                "init": _MIDPOINT_INIT,
                            },
                            "secondary_inductance": {
                                "bounds": {"lb": 0.005, "ub": 0.006},
                                "init": _MIDPOINT_INIT,
                            },
                        }
                    },
                }
            },
            # 同居するフラットルートはレガシーがあるため無視される。
            "primary": {
                "fit_parameters": {
                    "primary_resistance": {
                        "bounds": {"lb": 9.0, "ub": 10.0},
                        "init": _MIDPOINT_INIT,
                    },
                }
            },
        }
        bounds = ImParameterFitDescriptorBounds.from_estimation_document(
            legacy_doc
        )
        assert bounds.im_fixed("primary_resistance") == (0.50, 0.55)

    def test_empty_document_raises(self) -> None:
        with pytest.raises(
            ValueError,
            match="IM bounds YAML missing required fixed parameters",
        ):
            ImParameterFitDescriptorBounds.from_estimation_document({})


def _flat_im_document_with_shaft_output_deduction() -> dict[str, Any]:
    document = _flat_im_document()
    document["friction_windage"] = {
        "model_parameters": {
            "NONE": {"params": {}},
            "CONSTANT_V1": {
                "params": {
                    "k_friction_windage": {
                        "bounds": {"lb": 0.0, "ub": 0.05},
                        "init": {"method": "value", "value": 0.01},
                    },
                }
            },
        },
    }
    document["stray_load"] = {
        "model_parameters": {
            "NONE": {"params": {}},
            "CURRENT_DEPENDENT_QUADRATIC_V1": {
                "params": {
                    "k_stray_load": {
                        "bounds": {"lb": 0.0, "ub": 0.05},
                        "init": {"method": "value", "value": 0.005},
                    },
                }
            },
        },
    }
    return document


class TestImShaftOutputDeductionBounds:
    """friction_windage / stray_load（イミタンスを持たない2ノード）の解釈。"""

    def test_resolves_friction_windage_model_param(self) -> None:
        bounds = ImParameterFitDescriptorBounds.from_estimation_document(
            _flat_im_document_with_shaft_output_deduction()
        )
        assert bounds.im_model_param(
            subsystem="friction_windage",
            model_type_name="CONSTANT_V1",
            param_name="k_friction_windage",
        ) == (0.0, 0.05)

    def test_resolves_stray_load_model_param(self) -> None:
        bounds = ImParameterFitDescriptorBounds.from_estimation_document(
            _flat_im_document_with_shaft_output_deduction()
        )
        assert bounds.im_model_param(
            subsystem="stray_load",
            model_type_name="CURRENT_DEPENDENT_QUADRATIC_V1",
            param_name="k_stray_load",
        ) == (0.0, 0.05)

    def test_unknown_friction_windage_key_raises(self) -> None:
        """friction_windage / stray_load ブロックを書いていない文書では
        未定義キー扱いで KeyError になる。"""
        bounds = ImParameterFitDescriptorBounds.from_estimation_document(
            _flat_im_document()
        )
        with pytest.raises(KeyError, match="unknown IM friction_windage"):
            bounds.im_model_param(
                subsystem="friction_windage",
                model_type_name="CONSTANT_V1",
                param_name="k_friction_windage",
            )

    def test_unknown_stray_load_key_raises(self) -> None:
        bounds = ImParameterFitDescriptorBounds.from_estimation_document(
            _flat_im_document()
        )
        with pytest.raises(KeyError, match="unknown IM stray_load"):
            bounds.im_model_param(
                subsystem="stray_load",
                model_type_name="CURRENT_DEPENDENT_QUADRATIC_V1",
                param_name="k_stray_load",
            )


class TestCableBoundsErrors:
    """ケーブル bounds YAML の欠損・未知キーエラー。"""

    def test_unknown_conductor_model_param_raises(self) -> None:
        bounds = CableParameterFitDescriptorBounds.from_estimation_document(
            _flat_cable_document()
        )
        with pytest.raises(KeyError, match="unknown conductor model"):
            bounds.conductor_model_param(
                model_type_name="UNKNOWN",
                param_name="unknown",
            )

    def test_missing_fixed_key_raises(self) -> None:
        document = _flat_cable_document()
        del document["ground"]["fit_parameters"]["ground_resistance_length"]
        with pytest.raises(
            ValueError,
            match="cable bounds YAML missing required fixed parameters",
        ):
            CableParameterFitDescriptorBounds.from_estimation_document(document)


class TestCableFromEstimationDocument:
    """フラット / レガシー / 欠損ケース。"""

    def test_flat_document_resolves_fixed_params(self) -> None:
        bounds = CableParameterFitDescriptorBounds.from_estimation_document(
            _flat_cable_document()
        )
        assert bounds.cable_fixed("conductor_resistance_per_length") == (
            1e-5,
            0.5,
        )
        assert bounds.cable_fixed("ground_capacitance_per_length") == (
            1e-10,
            0.5,
        )

    def test_flat_document_resolves_conductor_model_params(self) -> None:
        bounds = CableParameterFitDescriptorBounds.from_estimation_document(
            _flat_cable_document()
        )
        assert bounds.conductor_model_param(
            model_type_name="CURRENT_DEPENDENT_V1",
            param_name="alpha_cond_r",
        ) == (0.1, 1.5)

    def test_flat_document_missing_conductor_model_param_raises(self) -> None:
        bounds = CableParameterFitDescriptorBounds.from_estimation_document(
            _flat_cable_document()
        )
        with pytest.raises(
            KeyError,
            match="missing bounds/init for conductor model parameter",
        ):
            bounds.conductor_model_param(
                model_type_name="CURRENT_DEPENDENT_V1",
                param_name="beta_cond_r",
            )

    def test_legacy_im_cable_system_subtree_takes_precedence(self) -> None:
        legacy_doc = {
            "version": 1,
            "im_cable_system": {
                "cable": {
                    "conductor": {
                        "fit_parameters": {
                            "conductor_resistance_per_length": {
                                "bounds": {"lb": 0.2, "ub": 0.3},
                                "init": _MIDPOINT_INIT,
                            },
                            "conductor_inductance_per_length": {
                                "bounds": {"lb": 1e-7, "ub": 2e-7},
                                "init": _MIDPOINT_INIT,
                            },
                        }
                    },
                    "ground": {
                        "fit_parameters": {
                            "ground_resistance_length": {
                                "bounds": {"lb": 1e8, "ub": 2e8},
                                "init": _MIDPOINT_INIT,
                            },
                            "ground_capacitance_per_length": {
                                "bounds": {"lb": 1e-10, "ub": 2e-10},
                                "init": _MIDPOINT_INIT,
                            },
                        }
                    },
                }
            },
            "conductor": {
                "fit_parameters": {
                    "conductor_resistance_per_length": {
                        "bounds": {"lb": 5.0, "ub": 6.0},
                        "init": _MIDPOINT_INIT,
                    },
                }
            },
        }
        bounds = CableParameterFitDescriptorBounds.from_estimation_document(
            legacy_doc
        )
        assert bounds.cable_fixed("conductor_resistance_per_length") == (
            0.2,
            0.3,
        )

    def test_empty_document_raises(self) -> None:
        with pytest.raises(
            ValueError,
            match="cable bounds YAML missing required fixed parameters",
        ):
            CableParameterFitDescriptorBounds.from_estimation_document({})


def _im_document_with_full_primary_models() -> dict[str, Any]:
    """BASIC と 3 係数の SLIP_DEPENDENT を持つ primary 文書。"""
    document = _flat_im_document()
    document["primary"]["model_parameters"] = {
        "BASIC": {"params": {}},
        "SLIP_DEPENDENT_LEAKAGE_SATURATION_V1": {
            "params": {
                "alpha_primary_r": {
                    "bounds": {"lb": 0.05, "ub": 2.5},
                    "init": _MIDPOINT_INIT,
                },
                "alpha_primary_x": {
                    "bounds": {"lb": 0.1, "ub": 0.9},
                    "init": _MIDPOINT_INIT,
                },
                "beta_primary_x": {
                    "bounds": {"lb": 0.2, "ub": 0.8},
                    "init": _MIDPOINT_INIT,
                },
            }
        },
    }
    return document


def _cable_document_with_full_conductor_models() -> dict[str, Any]:
    """BASIC と 4 係数の FREQUENCY_DEPENDENT を持つ conductor 文書。"""
    document = _flat_cable_document()
    document["conductor"]["model_parameters"] = {
        "BASIC": {"params": {}},
        "FREQUENCY_DEPENDENT_SKIN_EFFECT_V1": {
            "params": {
                "alpha_conductor_r": {
                    "bounds": {"lb": 0.01, "ub": 0.10},
                    "init": _MIDPOINT_INIT,
                },
                "beta_conductor_r": {
                    "bounds": {"lb": 0.05, "ub": 0.15},
                    "init": _MIDPOINT_INIT,
                },
                "alpha_conductor_x": {
                    "bounds": {"lb": 0.01, "ub": 0.10},
                    "init": _MIDPOINT_INIT,
                },
                "beta_conductor_x": {
                    "bounds": {"lb": 0.05, "ub": 0.15},
                    "init": _MIDPOINT_INIT,
                },
            }
        },
    }
    return document


class TestImModelParamSpecs:
    """``im_model_param_specs`` の行単位アクセサ。"""

    def test_returns_all_params_for_known_model(self) -> None:
        bounds = ImParameterFitDescriptorBounds.from_estimation_document(
            _im_document_with_full_primary_models()
        )
        specs = bounds.im_model_param_specs(
            "primary",
            "SLIP_DEPENDENT_LEAKAGE_SATURATION_V1",
        )
        assert set(specs) == {
            "alpha_primary_r",
            "alpha_primary_x",
            "beta_primary_x",
        }

    def test_returns_empty_dict_for_params_empty_model(self) -> None:
        bounds = ImParameterFitDescriptorBounds.from_estimation_document(
            _im_document_with_full_primary_models()
        )
        assert bounds.im_model_param_specs("primary", "BASIC") == {}

    def test_unknown_model_raises(self) -> None:
        bounds = ImParameterFitDescriptorBounds.from_estimation_document(
            _im_document_with_full_primary_models()
        )
        with pytest.raises(KeyError, match="unknown IM primary model"):
            bounds.im_model_param_specs("primary", "UNKNOWN_MODEL")

    def test_returned_dict_is_a_copy(self) -> None:
        bounds = ImParameterFitDescriptorBounds.from_estimation_document(
            _im_document_with_full_primary_models()
        )
        specs = bounds.im_model_param_specs(
            "primary",
            "SLIP_DEPENDENT_LEAKAGE_SATURATION_V1",
        )
        specs["injected"] = next(iter(specs.values()))
        specs2 = bounds.im_model_param_specs(
            "primary",
            "SLIP_DEPENDENT_LEAKAGE_SATURATION_V1",
        )
        assert "injected" not in specs2


class TestConductorModelParamSpecs:
    """``conductor_model_param_specs`` の行単位アクセサ。"""

    def test_returns_all_params_for_known_model(self) -> None:
        bounds = CableParameterFitDescriptorBounds.from_estimation_document(
            _cable_document_with_full_conductor_models()
        )
        specs = bounds.conductor_model_param_specs(
            "FREQUENCY_DEPENDENT_SKIN_EFFECT_V1",
        )
        assert set(specs) == {
            "alpha_conductor_r",
            "beta_conductor_r",
            "alpha_conductor_x",
            "beta_conductor_x",
        }

    def test_returns_empty_dict_for_params_empty_model(self) -> None:
        bounds = CableParameterFitDescriptorBounds.from_estimation_document(
            _cable_document_with_full_conductor_models()
        )
        assert bounds.conductor_model_param_specs("BASIC") == {}

    def test_unknown_model_raises(self) -> None:
        bounds = CableParameterFitDescriptorBounds.from_estimation_document(
            _cable_document_with_full_conductor_models()
        )
        with pytest.raises(KeyError, match="unknown conductor model"):
            bounds.conductor_model_param_specs("UNKNOWN")

    def test_returned_dict_is_a_copy(self) -> None:
        bounds = CableParameterFitDescriptorBounds.from_estimation_document(
            _cable_document_with_full_conductor_models()
        )
        specs = bounds.conductor_model_param_specs(
            "FREQUENCY_DEPENDENT_SKIN_EFFECT_V1",
        )
        specs["injected"] = next(iter(specs.values()))
        specs2 = bounds.conductor_model_param_specs(
            "FREQUENCY_DEPENDENT_SKIN_EFFECT_V1",
        )
        assert "injected" not in specs2
