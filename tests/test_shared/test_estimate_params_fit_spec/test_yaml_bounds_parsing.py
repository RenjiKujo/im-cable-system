"""Tests for ``estimate_params_fit_spec/yaml_bounds_parsing.py``.

``*_with_init`` 系の厳格バリデーション（init 必須・method 4 種・value の
範囲チェック）と、``document_body_without_version`` の挙動を担保する。

内部テストとして直接 import する理由:
    ``yaml_bounds_parsing`` は ``estimate_params_fit_spec`` パッケージの
    **内部実装**であり、公開窓口 ``__init__.py`` の ``__all__`` には
    載せない。複雑なスキーマ解釈（bounds 必須・init 必須・method 4 種・
    ``value`` の範囲チェック・不完全 bounds の拒否）の分岐網羅は、公開
    クラス ``*_descriptor_bounds`` 経由では到達しにくいため、例外的に
    実装モジュールを直接 import して内部テストする。
"""

from __future__ import annotations

import pytest

from im_cable_system.engine.shared.estimate_params_fit_spec.yaml_bounds_parsing import (  # noqa: E501
    document_body_without_version,
    parse_fixed_parameters_block_with_init,
    parse_model_parameters_block_with_init,
)

_MIDPOINT: dict[str, str] = {"method": "midpoint"}


class TestDocumentBodyWithoutVersion:
    """``version`` キーの除去。"""

    def test_removes_version_key(self) -> None:
        document = {"version": 3, "primary": {"a": 1}, "secondary": {}}
        body = document_body_without_version(document)
        assert body == {"primary": {"a": 1}, "secondary": {}}

    def test_returns_copy(self) -> None:
        document = {"version": 1, "k": 2}
        body = document_body_without_version(document)
        body["new"] = "x"
        assert "new" not in document


class TestParseFixedParametersBlockWithInit:
    """``parse_fixed_parameters_block_with_init`` の厳格スキーマ。"""

    def test_extracts_all_four_methods(self) -> None:
        section = {
            "fit_parameters": {
                "p_mid": {
                    "bounds": {"lb": 0.0, "ub": 4.0},
                    "init": {"method": "midpoint"},
                },
                "p_lb": {
                    "bounds": {"lb": 1.0, "ub": 5.0},
                    "init": {"method": "lb"},
                },
                "p_ub": {
                    "bounds": {"lb": 2.0, "ub": 8.0},
                    "init": {"method": "ub"},
                },
                "p_val": {
                    "bounds": {"lb": 0.0, "ub": 10.0},
                    "init": {"method": "value", "value": 3.5},
                },
            }
        }
        result = parse_fixed_parameters_block_with_init(section)
        assert result["p_mid"].resolve_initial() == 2.0
        assert result["p_lb"].resolve_initial() == 1.0
        assert result["p_ub"].resolve_initial() == 8.0
        assert result["p_val"].resolve_initial() == 3.5

    def test_init_missing_raises(self) -> None:
        section = {
            "fit_parameters": {
                "k": {"bounds": {"lb": 0.0, "ub": 1.0}},
            }
        }
        with pytest.raises(ValueError, match="requires 'init' mapping"):
            parse_fixed_parameters_block_with_init(section)

    def test_unknown_method_raises(self) -> None:
        section = {
            "fit_parameters": {
                "k": {
                    "bounds": {"lb": 0.0, "ub": 1.0},
                    "init": {"method": "geometric_mean"},
                },
            }
        }
        with pytest.raises(ValueError, match="init.method' must be one of"):
            parse_fixed_parameters_block_with_init(section)

    def test_value_method_missing_value_raises(self) -> None:
        section = {
            "fit_parameters": {
                "k": {
                    "bounds": {"lb": 0.0, "ub": 1.0},
                    "init": {"method": "value"},
                },
            }
        }
        with pytest.raises(ValueError, match="requires 'init.value'"):
            parse_fixed_parameters_block_with_init(section)

    def test_value_out_of_bounds_raises(self) -> None:
        section = {
            "fit_parameters": {
                "k": {
                    "bounds": {"lb": 0.0, "ub": 1.0},
                    "init": {"method": "value", "value": 2.5},
                },
            }
        }
        with pytest.raises(ValueError, match="outside bounds"):
            parse_fixed_parameters_block_with_init(section)

    def test_partial_bounds_raises(self) -> None:
        section = {
            "fit_parameters": {
                "missing_ub": {"bounds": {"lb": 0.0}, "init": _MIDPOINT},
            }
        }
        with pytest.raises(
            ValueError, match=r"missing required field\(s\): ub"
        ):
            parse_fixed_parameters_block_with_init(section)

    def test_missing_bounds_raises(self) -> None:
        section = {
            "fit_parameters": {
                "no_bounds": {"unit": "Ω", "init": _MIDPOINT},
            }
        }
        with pytest.raises(ValueError, match="requires 'bounds' mapping"):
            parse_fixed_parameters_block_with_init(section)


class TestParseModelParametersBlockWithInit:
    """``parse_model_parameters_block_with_init`` の厳格スキーマ。"""

    def test_extracts_nested_specs(self) -> None:
        section = {
            "model_parameters": {
                "BASIC": {"params": {}},
                "MODEL_A": {
                    "params": {
                        "alpha": {
                            "bounds": {"lb": 0.0, "ub": 1.0},
                            "init": {"method": "lb"},
                        },
                    }
                },
            }
        }
        result = parse_model_parameters_block_with_init(section)
        assert result["BASIC"] == {}
        assert result["MODEL_A"]["alpha"].resolve_initial() == 0.0

    def test_init_missing_raises_with_param_path(self) -> None:
        section = {
            "model_parameters": {
                "MODEL_A": {
                    "params": {
                        "alpha": {"bounds": {"lb": 0.0, "ub": 1.0}},
                    }
                },
            }
        }
        with pytest.raises(ValueError, match=r"'MODEL_A\.alpha'"):
            parse_model_parameters_block_with_init(section)

    @pytest.mark.parametrize(
        "model_entry",
        [None, {}, {"params": None}, {"params": []}, "BASIC"],
        ids=[
            "null_entry",
            "no_params_key",
            "null_params",
            "params_not_mapping",
            "scalar_entry",
        ],
    )
    def test_model_type_without_params_mapping_raises(
        self, model_entry: object
    ) -> None:
        """``params`` を持たないモデル種別は、黙って読み飛ばさず ValueError。

        読み飛ばすとモデル種別キーごと欠落し、下流が「YAML にキーはあるのに
        未知のモデル種別」という誤導的な KeyError を出すため。
        """
        section = {"model_parameters": {"BASIC": model_entry}}
        with pytest.raises(ValueError, match=r"'BASIC' requires 'params'"):
            parse_model_parameters_block_with_init(section)

    def test_param_entry_not_mapping_raises_with_param_path(self) -> None:
        """係数行が mapping でない場合も、黙って落とさず ValueError。"""
        section = {
            "model_parameters": {
                "MODEL_A": {"params": {"alpha": None}},
            }
        }
        with pytest.raises(
            ValueError, match=r"'MODEL_A\.alpha'.*requires 'bounds' mapping"
        ):
            parse_model_parameters_block_with_init(section)

    def test_partial_bounds_raises_with_param_path(self) -> None:
        section = {
            "model_parameters": {
                "MODEL_A": {
                    "params": {
                        "alpha": {"bounds": {"ub": 1.0}, "init": _MIDPOINT},
                    }
                },
            }
        }
        with pytest.raises(
            ValueError,
            match=r"'MODEL_A\.alpha'.*missing required field\(s\): lb",
        ):
            parse_model_parameters_block_with_init(section)
