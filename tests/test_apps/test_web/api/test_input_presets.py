"""GET /api/input-presets と、入力ファイルをすべてプリセットで回す投入経路。"""

from __future__ import annotations

import io
import json
from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

_REPO_ROOT = Path(__file__).resolve().parents[4]
_MANIFEST_PATH = _REPO_ROOT / "apps/web/presets/input.yaml"

_ALLOWED_PATH_PREFIXES = (
    "examples/",
    "src/im_cable_system/bounds_and_init/",
    "src/im_cable_system/catalog/",
)

_SUBMIT_DATA_BY_MODE: dict[str, dict[str, str]] = {
    "estimate_params": {
        "base_config": "estimate_params_default",
        "input_preset": "quick_start_slipandcurrentdependent03",
        "im_bounds_preset": "bundled_default",
        "cable_bounds_preset": "bundled_default",
    },
    "forward_by_cartesian_grid": {
        "base_config": "forward_by_cartesian_grid_default",
        "series_selection_preset": "basic03_no_cable",
        "axes_preset": "cartesian_grid_50hz_200v",
        "performance_curve_preset": "slipandcurrentdependent03",
        "im_catalog_preset": "bundled_default",
        "cable_catalog_preset": "bundled_default",
    },
    "forward_by_operating_points": {
        "base_config": "forward_by_operating_points_default",
        "series_selection_preset": (
            "slipandcurrentdependent03_feeder30m_lead10m"
        ),
        "axes_preset": "operating_points_40to60hz",
        "performance_curve_preset": "slipandcurrentdependent03",
        "im_catalog_preset": "bundled_default",
        "cable_catalog_preset": "bundled_default",
    },
}


class TestGetInputPresets:
    """GET /api/input-presets?mode=... の一覧取得。"""

    @pytest.mark.parametrize("mode", list(_SUBMIT_DATA_BY_MODE))
    def test_returns_fields_and_presets(
        self, client: TestClient, mode: str
    ) -> None:
        response = client.get("/api/input-presets", params={"mode": mode})

        assert response.status_code == 200
        presets_by_field = response.json()["presets_by_field"]
        assert presets_by_field
        for presets in presets_by_field.values():
            assert presets
            for preset in presets:
                assert preset["name"]
                assert preset["text"].strip()

    def test_unknown_mode_returns_400(self, client: TestClient) -> None:
        response = client.get(
            "/api/input-presets", params={"mode": "not_a_real_mode"}
        )

        assert response.status_code == 400


class TestManifestPathsExist:
    """manifest.yaml のすべての参照先が実在すること（プリセットの腐り検出）。"""

    def test_all_paths_exist(self) -> None:
        manifest = yaml.safe_load(_MANIFEST_PATH.read_text(encoding="utf-8"))
        for mode, fields in manifest.items():
            if mode == "version":
                continue
            for field, presets in fields.items():
                for preset in presets:
                    path = _REPO_ROOT / preset["path"]
                    assert path.is_file(), (
                        f"{mode}.{field}.{preset['name']} -> {preset['path']}"
                    )

    def test_paths_use_allowed_prefixes(self) -> None:
        manifest = yaml.safe_load(_MANIFEST_PATH.read_text(encoding="utf-8"))
        for mode, fields in manifest.items():
            if mode == "version":
                continue
            for field, presets in fields.items():
                for preset in presets:
                    rel_path = preset["path"]
                    location = f"{mode}.{field}.{preset['name']} -> {rel_path}"
                    assert not rel_path.startswith("tests/"), location
                    assert rel_path.startswith(_ALLOWED_PATH_PREFIXES), location


class TestSubmitWithPresetsOnly:
    """アップロード 0 件・プリセットだけで投入でき、inputs/ と cmd.json に反映される。"""

    @pytest.mark.parametrize("mode", list(_SUBMIT_DATA_BY_MODE))
    def test_submits_with_presets_only(
        self, client: TestClient, mode: str
    ) -> None:
        data = _SUBMIT_DATA_BY_MODE[mode]

        response = client.post(f"/api/jobs/{mode}", data=data)

        assert response.status_code == 202, response.text
        job_id = response.json()["job_id"]

        jobs_root = client.app.state.settings.jobs_root
        job_dir = jobs_root / job_id
        inputs_dir = job_dir / "inputs"
        saved = list(inputs_dir.iterdir())
        assert saved

        argv = json.loads((job_dir / "cmd.json").read_text(encoding="utf-8"))[
            "argv"
        ]
        for path in saved:
            assert str(path) in argv


class TestPresetAndUploadConflict:
    """アップロードとプリセットの同時指定は 400。未知のプリセット名も 400。"""

    def test_upload_and_preset_together_returns_400(
        self, client: TestClient
    ) -> None:
        response = client.post(
            "/api/jobs/estimate_params",
            data={
                "base_config": "estimate_params_default",
                "input_preset": "quick_start_slipandcurrentdependent03",
            },
            files={
                "input": (
                    "input.csv",
                    io.BytesIO(b"slip,current\n0.1,1.0\n"),
                    "text/csv",
                )
            },
        )

        assert response.status_code == 400

    def test_unknown_preset_name_returns_400(self, client: TestClient) -> None:
        response = client.post(
            "/api/jobs/estimate_params",
            data={
                "base_config": "estimate_params_default",
                "input_preset": "not_a_real_preset",
            },
        )

        assert response.status_code == 400
