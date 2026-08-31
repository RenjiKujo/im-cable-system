"""IM catalog / bounds YAML の軸出力控除 2 軸の契約検証。

公開窓口 ``apps.web.engine_contract`` から import する。
"""

from __future__ import annotations

from pathlib import Path

from apps.web.engine_contract import (
    find_bounds_contract_errors,
    find_catalog_contract_errors,
)

_REPO_ROOT = Path(__file__).resolve().parents[4]
_CATALOG = _REPO_ROOT / "src/im_cable_system/catalog/im_series_catalog.yaml"
_BOUNDS = (
    _REPO_ROOT
    / "src/im_cable_system/bounds_and_init/im_descriptor_bounds_and_init.yaml"
)


_MINIMAL_SERIES = """
version: 1
im_series:
  - name: "Dummy01"
    friction_windage:
      model: { name: "NONE", params: [] }
    stray_load:
      model: { name: "NONE", params: [] }
"""


class TestFindCatalogContractErrors:
    """同梱 catalog は通り、ブロック欠落・未知種別はエラー。"""

    def test_bundled_catalog_has_no_errors(self) -> None:
        errors = find_catalog_contract_errors(
            _CATALOG.read_text(encoding="utf-8")
        )
        assert errors == []

    def test_missing_branch_includes_series_name(self) -> None:
        text = """
version: 1
im_series:
  - name: "Broken01"
    primary:
      model: { name: "BASIC", params: [] }
"""
        errors = find_catalog_contract_errors(text)

        assert errors
        assert any("Broken01" in msg for msg in errors)
        assert any("friction_windage" in msg for msg in errors)
        assert any("stray_load" in msg for msg in errors)

    def test_unknown_kind_includes_series_name(self) -> None:
        text = """
version: 1
im_series:
  - name: "Broken02"
    friction_windage:
      model: { name: "NOT_A_KIND", params: [] }
    stray_load:
      model: { name: "NONE", params: [] }
"""
        errors = find_catalog_contract_errors(text)

        assert any("Broken02" in msg and "NOT_A_KIND" in msg for msg in errors)

    def test_minimal_valid_catalog_passes(self) -> None:
        assert find_catalog_contract_errors(_MINIMAL_SERIES) == []


class TestFindBoundsContractErrors:
    """同梱 bounds は通り、トップレベル欠落はエラー。"""

    def test_bundled_bounds_has_no_errors(self) -> None:
        errors = find_bounds_contract_errors(
            _BOUNDS.read_text(encoding="utf-8")
        )
        assert errors == []

    def test_missing_top_level_blocks(self) -> None:
        errors = find_bounds_contract_errors("version: 1\nprimary: {}\n")

        assert any("friction_windage" in msg for msg in errors)
        assert any("stray_load" in msg for msg in errors)

    def test_missing_model_parameters(self) -> None:
        text = """
friction_windage: {}
stray_load:
  model_parameters: {}
"""
        errors = find_bounds_contract_errors(text)

        assert any(
            "friction_windage" in msg and "model_parameters" in msg
            for msg in errors
        )
