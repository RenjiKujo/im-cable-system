"""routes_presets: config プリセット一覧。"""

from __future__ import annotations

from pathlib import Path

import yaml
from fastapi.testclient import TestClient

_REPO_ROOT = Path(__file__).resolve().parents[4]
_CONFIG_MANIFEST_PATH = _REPO_ROOT / "apps/web/presets/config.yaml"
_MODES = (
    "forward_by_cartesian_grid",
    "estimate_params",
    "forward_by_operating_points",
)


class TestGetConfigPresets:
    """同梱プリセットの一覧取得。"""

    def test_returns_mode_default_first(self, client: TestClient) -> None:
        for mode in _MODES:
            response = client.get("/api/config-presets", params={"mode": mode})

            assert response.status_code == 200
            presets = response.json()["presets"]
            assert presets
            assert presets[0]["name"] == f"{mode}_default"
            assert presets[0]["description"].strip()
            assert presets[0]["yaml_text"].strip()

    def test_unknown_mode_returns_400(self, client: TestClient) -> None:
        response = client.get(
            "/api/config-presets", params={"mode": "not_a_real_mode"}
        )

        assert response.status_code == 400

    def test_missing_mode_returns_422(self, client: TestClient) -> None:
        response = client.get("/api/config-presets")

        assert response.status_code == 422


class TestConfigManifestPaths:
    """config マニフェストの参照先が examples/config/ 配下に実在すること。"""

    def test_all_paths_exist_under_examples(self) -> None:
        manifest = yaml.safe_load(
            _CONFIG_MANIFEST_PATH.read_text(encoding="utf-8")
        )
        for mode, presets in manifest.items():
            if mode == "version":
                continue
            for preset in presets:
                rel_path = preset["path"]
                path = _REPO_ROOT / rel_path
                assert rel_path.startswith("examples/"), (
                    f"{mode}.{preset['name']} -> {rel_path}"
                )
                assert path.is_file(), f"{mode}.{preset['name']} -> {rel_path}"


class TestLegacyPresetDirsRemoved:
    """実体コピー置き場は廃止済みであること。"""

    def test_old_preset_directories_do_not_exist(self) -> None:
        assert not (_REPO_ROOT / "apps/web/config_presets").exists()
        assert not (_REPO_ROOT / "apps/web/input_presets").exists()
