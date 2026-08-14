"""model_equations/ の 3 者（コード・docs・bounds_and_init YAML）整合性テスト。

docs/model_equations/index.md が「モデル種別（Enum）と各種別が要求する係数名は
shared の DTO / Enum を正とする」と宣言している契約を、実行時に検証する。

対象は「モデル種別 → 必須係数名の集合」で、次の 3 箇所が完全一致することを保証する。

- **コード**: 各 ``*ModelDto.get_required_parameter_names()`` の分岐（正）。
- **docs**: ``docs/model_equations/*.md`` の記号 ↔ YAML キー対応表。
- **YAML**: ``bounds_and_init/*.yaml`` の ``model_parameters.<種別>.params`` キー。

3 者のいずれかだけを更新（モデル追加・係数名変更）すると、このテストが落ちる。

さらに :class:`TestModelEquationsCoverage` が「本テスト自身の網羅」を守る。
モデル種別の追加は既存のパラメータ化で自動的に検証対象へ入るが、**サブシステムを
新設した場合**（新しい ``*ModelDto`` や ``model_equations/*.md`` の追加）は
``_SUBSYSTEMS`` を更新しない限り検証されない。その取りこぼしを検出する。
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import pytest
import yaml

from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    CableConductorModelDto,
    ConductorModelType,
    ImExcitationModelDto,
    ImExcitationModelType,
    ImPrimaryModelDto,
    ImPrimaryModelType,
    ImSecondaryModelDto,
    ImSecondaryModelType,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_MODEL_EQUATIONS_DIR = _REPO_ROOT / "docs" / "model_equations"
_IM_BOUNDS_PATH = (
    _REPO_ROOT
    / "src"
    / "im_cable_system"
    / "bounds_and_init"
    / "im_descriptor_bounds_and_init.yaml"
)
_CABLE_BOUNDS_PATH = (
    _REPO_ROOT
    / "src"
    / "im_cable_system"
    / "bounds_and_init"
    / "cable_descriptor_bounds_and_init.yaml"
)

_SRC_DIR = _REPO_ROOT / "src"
_INDEX_DOC_PATH = _MODEL_EQUATIONS_DIR / "index.md"

# docs の対応表 1 行から YAML キーを抜き出す（記号列 → `yaml_key` 列の表）。
_DOC_TABLE_ROW_PATTERN = re.compile(
    r"\|\s*\$[^$]+\$\s*\|\s*`([a-z_0-9]+)`\s*\|"
)
# index.md の三者対応表 1 行からモデル種別（第 2 列）を抜き出す。
_INDEX_TABLE_ROW_PATTERN = re.compile(
    r"^\|[^|]*\|\s*`([A-Z][A-Z_0-9]*)`\s*\|", re.M
)
# 必須係数名を宣言する DTO を見分けるメソッド名。
_REQUIRED_PARAMS_METHOD = "get_required_parameter_names"


@dataclass(frozen=True)
class _Subsystem:
    """1 サブシステム分の「コード・docs・YAML」参照情報。"""

    label: str
    enum_cls: type[Enum]
    dto_cls: type[Any]
    doc_path: Path
    yaml_path: Path
    yaml_top_key: str


_SUBSYSTEMS = (
    _Subsystem(
        label="im_primary",
        enum_cls=ImPrimaryModelType,
        dto_cls=ImPrimaryModelDto,
        doc_path=_MODEL_EQUATIONS_DIR / "im_primary.md",
        yaml_path=_IM_BOUNDS_PATH,
        yaml_top_key="primary",
    ),
    _Subsystem(
        label="im_excitation",
        enum_cls=ImExcitationModelType,
        dto_cls=ImExcitationModelDto,
        doc_path=_MODEL_EQUATIONS_DIR / "im_excitation.md",
        yaml_path=_IM_BOUNDS_PATH,
        yaml_top_key="excitation",
    ),
    _Subsystem(
        label="im_secondary",
        enum_cls=ImSecondaryModelType,
        dto_cls=ImSecondaryModelDto,
        doc_path=_MODEL_EQUATIONS_DIR / "im_secondary.md",
        yaml_path=_IM_BOUNDS_PATH,
        yaml_top_key="secondary",
    ),
    _Subsystem(
        label="cable_conductor",
        enum_cls=ConductorModelType,
        dto_cls=CableConductorModelDto,
        doc_path=_MODEL_EQUATIONS_DIR / "cable_conductor.md",
        yaml_path=_CABLE_BOUNDS_PATH,
        yaml_top_key="conductor",
    ),
)


def _code_required_params(
    enum_cls: type[Enum], dto_cls: type[Any]
) -> dict[str, set[str]]:
    """各 Enum メンバーについて、DTO の必須係数名（正）を集める。

    ``get_required_parameter_names`` は ``self.name`` だけを参照する契約
    （``__post_init__`` の値検証はここでは不要）なので、``params`` を経由せず
    ``__new__`` + ``object.__setattr__`` で ``name`` だけを持つインスタンスを作る。
    通常の `dto_cls(name=member)` は frozen dataclass の ``__post_init__`` が
    ``params`` の整合を検証してしまい、係数名を得る前に ``ValueError`` になる。
    """
    result: dict[str, set[str]] = {}
    for member in enum_cls:
        instance = object.__new__(dto_cls)
        object.__setattr__(instance, "name", member)
        result[member.name] = set(instance.get_required_parameter_names())
    return result


def _doc_yaml_keys(doc_path: Path) -> dict[str, set[str]]:
    """docs の対応表から `モデル種別 → YAML キー集合` を抽出する。"""
    text = doc_path.read_text(encoding="utf-8")
    result: dict[str, set[str]] = {}
    # "## MODEL_NAME" 見出しで節を分割し、節内の対応表行から YAML キーを拾う。
    for section in re.split(r"\n## ", text)[1:]:
        model_name = section.split("\n", 1)[0].strip()
        result[model_name] = set(_DOC_TABLE_ROW_PATTERN.findall(section))
    return result


def _yaml_required_params(yaml_path: Path, top_key: str) -> dict[str, set[str]]:
    """bounds_and_init YAML から `モデル種別 → params キー集合` を抽出する。"""
    data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    model_parameters = data.get(top_key, {}).get("model_parameters", {}) or {}
    result: dict[str, set[str]] = {}
    for model_name, node in model_parameters.items():
        result[model_name] = set((node or {}).get("params", {}).keys())
    return result


class TestModelEquationsConsistency:
    """コード・docs・YAML の 3 者が全サブシステムで一致することを検証する。"""

    @pytest.mark.parametrize(
        "subsystem", _SUBSYSTEMS, ids=[s.label for s in _SUBSYSTEMS]
    )
    def test_docs_matches_code(self, subsystem: _Subsystem) -> None:
        """docs の対応表の係数名集合が、コードの必須係数名集合と一致する。"""
        code = _code_required_params(subsystem.enum_cls, subsystem.dto_cls)
        docs = _doc_yaml_keys(subsystem.doc_path)

        missing_in_docs = set(code) - set(docs)
        assert not missing_in_docs, (
            f"{subsystem.label}: コードにあるモデル種別が "
            f"{subsystem.doc_path.name} に無い: {sorted(missing_in_docs)}"
        )
        for model_name, code_params in code.items():
            doc_params = docs[model_name]
            assert doc_params == code_params, (
                f"{subsystem.label}.{model_name}: 係数名が不一致\n"
                f"  コードのみ: {sorted(code_params - doc_params)}\n"
                f"  docsのみ  : {sorted(doc_params - code_params)}"
            )

    @pytest.mark.parametrize(
        "subsystem", _SUBSYSTEMS, ids=[s.label for s in _SUBSYSTEMS]
    )
    def test_yaml_bounds_matches_code(self, subsystem: _Subsystem) -> None:
        """bounds_and_init YAML の params キー集合が、コードの必須係数名集合と一致する。"""
        code = _code_required_params(subsystem.enum_cls, subsystem.dto_cls)
        yaml_params = _yaml_required_params(
            subsystem.yaml_path, subsystem.yaml_top_key
        )

        missing_in_yaml = {
            name for name, params in code.items() if params
        } - set(yaml_params)
        assert not missing_in_yaml, (
            f"{subsystem.label}: コードにあるモデル種別が "
            f"{subsystem.yaml_path.name} に無い: {sorted(missing_in_yaml)}"
        )
        for model_name, code_params in code.items():
            if not code_params and model_name not in yaml_params:
                continue  # BASIC 等、係数不要なモデルは bounds 未記載でもよい。
            yaml_keys = yaml_params.get(model_name, set())
            assert yaml_keys == code_params, (
                f"{subsystem.label}.{model_name}: 係数名が不一致\n"
                f"  コードのみ: {sorted(code_params - yaml_keys)}\n"
                f"  YAMLのみ  : {sorted(yaml_keys - code_params)}"
            )


def _discover_param_dto_class_names() -> set[str]:
    """``src/`` から必須係数名を宣言する DTO クラス名を発見する。

    ``get_required_parameter_names`` を定義するクラスは「モデル種別ごとに必須係数を
    持つサブシステム」であり、本テストの検証対象になるべきものである。import せず
    AST で走査するため、公開窓口へ載っていない新設 DTO も取りこぼさない。
    """
    found: set[str] = set()
    for py in _SRC_DIR.rglob("*.py"):
        if "__pycache__" in py.parts:
            continue
        tree = ast.parse(py.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            if any(
                isinstance(body, ast.FunctionDef)
                and body.name == _REQUIRED_PARAMS_METHOD
                for body in node.body
            ):
                found.add(node.name)
    return found


class TestModelEquationsCoverage:
    """本テスト自身が全サブシステムを網羅していることを保証する。

    モデル**種別**の追加は ``_SUBSYSTEMS`` のパラメータ化で自動的に検証されるが、
    サブシステム自体の新設（新 DTO・新 md）は ``_SUBSYSTEMS`` を更新しない限り
    検証対象に入らない。ここが「実装を変えたらテストも更新する」の機械的な担保。
    """

    def test_all_param_dtos_are_covered(self) -> None:
        """必須係数を持つ DTO がすべて ``_SUBSYSTEMS`` に登録されている。"""
        discovered = _discover_param_dto_class_names()
        covered = {subsystem.dto_cls.__name__ for subsystem in _SUBSYSTEMS}
        missing = discovered - covered
        assert not missing, (
            f"{_REQUIRED_PARAMS_METHOD} を持つ DTO が本テストで検証されていない: "
            f"{sorted(missing)}\n"
            "  → tests/test_docs/test_model_equations_consistency.py の "
            "_SUBSYSTEMS に追加すること。"
        )
        stale = covered - discovered
        assert not stale, (
            f"_SUBSYSTEMS に実装が存在しない DTO がある: {sorted(stale)}\n"
            "  → 削除・改名したなら _SUBSYSTEMS からも外すこと。"
        )

    def test_all_model_equation_docs_are_covered(self) -> None:
        """``model_equations/`` の各 md がすべて ``_SUBSYSTEMS`` に登録されている。"""
        # index.md は索引であり、個別モデルの係数表を持たないため対象外。
        doc_files = {
            path.name for path in _MODEL_EQUATIONS_DIR.glob("*.md")
        } - {_INDEX_DOC_PATH.name}
        covered = {subsystem.doc_path.name for subsystem in _SUBSYSTEMS}
        assert doc_files == covered, (
            "model_equations/ の md と _SUBSYSTEMS が一致しない\n"
            f"  テスト未登録の md: {sorted(doc_files - covered)}\n"
            f"  md が無い登録    : {sorted(covered - doc_files)}"
        )

    def test_index_table_lists_every_model_type(self) -> None:
        """``index.md`` の三者対応表が全モデル種別を列挙している。"""
        listed = set(
            _INDEX_TABLE_ROW_PATTERN.findall(
                _INDEX_DOC_PATH.read_text(encoding="utf-8")
            )
        )
        defined = {
            member.name
            for subsystem in _SUBSYSTEMS
            for member in subsystem.enum_cls
        }
        missing = defined - listed
        assert not missing, (
            f"index.md の対応表に載っていないモデル種別: {sorted(missing)}"
        )
