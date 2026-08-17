"""Forward 系 カタログ YAML ローダの構造バリデーションテスト。

``im_catalog_parser`` / ``cable_catalog_parser`` の挙動を
``ForwardLoader`` 経由で確認する。

確認観点:
    - 必須キー欠落で ``KeyError`` ではなく ``ValueError`` が上がる
    - シリーズ ``name`` の重複が ``ValueError`` として検出される
    - シリーズ entry の ``name`` 欠落が ``ValueError`` として検出される

YAML を手書きで組み立てるとインデント不整合で壊れやすいため、
``yaml.safe_dump`` で構造的に組み立てる。
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import pytest
import yaml

from im_cable_system.engine.algorithm.input_algorithm.load_data import (
    ForwardLoader,
)
from im_cable_system.engine.shared.config import Config, IConfig, ILogger
from im_cable_system.engine.shared.job_spec.forward import (
    ForwardJobSpec,
)
from tests.test_algorithm.test_input_algorithm._input_algorithm_helpers import (
    input_files_dir,
)


def _series_forward_dir() -> Path:
    return input_files_dir() / "series_forward"


def _axes_forward_by_cartesian_grid_dir() -> Path:
    return input_files_dir() / "axes_forward_by_cartesian_grid"


def _make_spec(
    *,
    series_csv_path: Path | None = None,
) -> ForwardJobSpec:
    return ForwardJobSpec(
        series_selection_path=(
            series_csv_path
            if series_csv_path is not None
            else _series_forward_dir() / "basic01_nocable.tsv"
        ),
        axes_path=(
            _axes_forward_by_cartesian_grid_dir() / "cartesian_grid_v1.tsv"
        ),
    )


def _loader(config: IConfig, logger: ILogger) -> ForwardLoader:
    return ForwardLoader.create(config=config, logger=logger)


def _config_with_catalog_paths(
    config: IConfig,
    *,
    im_series_catalog_path: Path | None = None,
    cable_series_catalog_path: Path | None = None,
) -> IConfig:
    """カタログ YAML だけをテスト用に差し替えた Config を返す。"""
    return Config.create(
        config_file_path=config.config_file_path,
        im_series_catalog_file_path=im_series_catalog_path,
        cable_series_catalog_file_path=cable_series_catalog_path,
    )


def _value_unit(value: float | int, unit: str) -> dict[str, Any]:
    return {"value": value, "unit": unit}


def _basic_im_entry(name: str = "Basic01") -> dict[str, Any]:
    """単一かごの最小限の IM シリーズ entry を作る。"""
    branch = {
        "model": {"name": "BASIC", "params": []},
        "resistance": _value_unit(0.1, "ohm"),
        "inductance": _value_unit(0.01, "H"),
    }
    return {
        "name": name,
        "poles": 4,
        "connection_type": "Y",
        "circuit_type": "SINGLE_CAGE",
        "nameplate": {
            "voltage": _value_unit(200, "V"),
            "current": _value_unit(10, "A"),
            "power": _value_unit(1000, "W"),
            "frequency": _value_unit(50, "Hz"),
        },
        "primary": copy.deepcopy(branch),
        "excitation": copy.deepcopy(branch),
        "secondary": copy.deepcopy(branch),
        "friction_windage": {"model": {"name": "NONE", "params": []}},
        "stray_load": {"model": {"name": "NONE", "params": []}},
    }


def _write_yaml(path: Path, data: Any) -> None:
    path.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


class TestForwardImCatalogValidation:
    """IM カタログ YAML の構造バリデーション。"""

    def test_missing_poles_raises_value_error_not_key_error(
        self,
        config: IConfig,
        logger: ILogger,
        tmp_path: Path,
    ) -> None:
        """必須キー ``poles`` 欠落で KeyError ではなく ValueError を上げる。"""
        entry = _basic_im_entry()
        entry.pop("poles")
        catalog = tmp_path / "im_missing_poles.yaml"
        _write_yaml(catalog, {"im_series": [entry]})
        spec = _make_spec()
        test_config = _config_with_catalog_paths(
            config,
            im_series_catalog_path=catalog,
        )
        with pytest.raises(
            ValueError,
            match=r"必須キー 'poles' がありません",
        ):
            _loader(test_config, logger).load(spec)

    def test_missing_nameplate_voltage_raises_value_error(
        self,
        config: IConfig,
        logger: ILogger,
        tmp_path: Path,
    ) -> None:
        """nameplate.voltage 欠落で ValueError。"""
        entry = _basic_im_entry()
        entry["nameplate"].pop("voltage")
        catalog = tmp_path / "im_missing_voltage.yaml"
        _write_yaml(catalog, {"im_series": [entry]})
        spec = _make_spec()
        test_config = _config_with_catalog_paths(
            config,
            im_series_catalog_path=catalog,
        )
        with pytest.raises(
            ValueError,
            match=r"必須キー 'voltage' がありません",
        ):
            _loader(test_config, logger).load(spec)

    def test_missing_primary_resistance_raises_value_error(
        self,
        config: IConfig,
        logger: ILogger,
        tmp_path: Path,
    ) -> None:
        """primary.resistance 欠落で ValueError。"""
        entry = _basic_im_entry()
        entry["primary"].pop("resistance")
        catalog = tmp_path / "im_missing_primary_resistance.yaml"
        _write_yaml(catalog, {"im_series": [entry]})
        spec = _make_spec()
        test_config = _config_with_catalog_paths(
            config,
            im_series_catalog_path=catalog,
        )
        with pytest.raises(
            ValueError,
            match=r"必須キー 'resistance' がありません",
        ):
            _loader(test_config, logger).load(spec)

    def test_missing_value_in_unit_block_raises_value_error(
        self,
        config: IConfig,
        logger: ILogger,
        tmp_path: Path,
    ) -> None:
        """``{value, unit}`` ブロックの value 欠落で ValueError。"""
        entry = _basic_im_entry()
        entry["nameplate"]["voltage"] = {"unit": "V"}
        catalog = tmp_path / "im_no_value.yaml"
        _write_yaml(catalog, {"im_series": [entry]})
        spec = _make_spec()
        test_config = _config_with_catalog_paths(
            config,
            im_series_catalog_path=catalog,
        )
        with pytest.raises(
            ValueError,
            match=r"'value' がありません",
        ):
            _loader(test_config, logger).load(spec)

    def test_duplicate_series_name_raises(
        self,
        config: IConfig,
        logger: ILogger,
        tmp_path: Path,
    ) -> None:
        """``im_series`` 内で name が重複しているとエラー。

        従来は最初の entry を採用していたが、ユーザの編集ミスが
        silent に解釈されるのを避けるため、LoadData 段で弾く。
        """
        first = _basic_im_entry(name="Basic01")
        second = _basic_im_entry(name="Basic01")
        catalog = tmp_path / "im_dup_name.yaml"
        _write_yaml(catalog, {"im_series": [first, second]})
        spec = _make_spec()
        test_config = _config_with_catalog_paths(
            config,
            im_series_catalog_path=catalog,
        )
        with pytest.raises(
            ValueError,
            match=r"シリーズ名 'Basic01' が重複",
        ):
            _loader(test_config, logger).load(spec)

    def test_entry_without_name_raises(
        self,
        config: IConfig,
        logger: ILogger,
        tmp_path: Path,
    ) -> None:
        """``im_series`` 内に name が無い entry があるとエラー。"""
        first = _basic_im_entry(name="Basic01")
        second_no_name = _basic_im_entry(name="WillBeRemoved")
        second_no_name.pop("name")
        catalog = tmp_path / "im_no_name.yaml"
        _write_yaml(catalog, {"im_series": [first, second_no_name]})
        spec = _make_spec()
        test_config = _config_with_catalog_paths(
            config,
            im_series_catalog_path=catalog,
        )
        with pytest.raises(
            ValueError,
            match=r"im_series\[\d+\] に name キーが",
        ):
            _loader(test_config, logger).load(spec)


class TestForwardImCatalogShaftOutputDeduction:
    """軸出力控除 2 軸（``friction_windage`` / ``stray_load``）は必須。

    一次・励磁・二次と同格の必須ブロックであり、欠落は他の必須キー
    欠落と同じ ``require_mapping_key`` 経由のエラーになる。
    """

    def test_missing_friction_windage_raises_value_error(
        self,
        config: IConfig,
        logger: ILogger,
        tmp_path: Path,
    ) -> None:
        entry = _basic_im_entry()
        entry.pop("friction_windage")
        catalog = tmp_path / "im_missing_friction_windage.yaml"
        _write_yaml(catalog, {"im_series": [entry]})
        spec = _make_spec()
        test_config = _config_with_catalog_paths(
            config,
            im_series_catalog_path=catalog,
        )
        with pytest.raises(
            ValueError,
            match=r"必須キー 'friction_windage' がありません",
        ):
            _loader(test_config, logger).load(spec)

    def test_missing_stray_load_raises_value_error(
        self,
        config: IConfig,
        logger: ILogger,
        tmp_path: Path,
    ) -> None:
        entry = _basic_im_entry()
        entry.pop("stray_load")
        catalog = tmp_path / "im_missing_stray_load.yaml"
        _write_yaml(catalog, {"im_series": [entry]})
        spec = _make_spec()
        test_config = _config_with_catalog_paths(
            config,
            im_series_catalog_path=catalog,
        )
        with pytest.raises(
            ValueError,
            match=r"必須キー 'stray_load' がありません",
        ):
            _loader(test_config, logger).load(spec)

    def test_missing_model_in_friction_windage_names_the_axis(
        self,
        config: IConfig,
        logger: ILogger,
        tmp_path: Path,
    ) -> None:
        """``friction_windage.model`` 欠落時、エラーがどちらの軸か明示する。

        ``_loss_branch_from_entry`` 内の ``model`` 取り出しに
        ``f"{context}.{key}"`` を渡す修正の回帰テスト。
        """
        entry = _basic_im_entry()
        entry["friction_windage"] = {}
        catalog = tmp_path / "im_missing_fw_model.yaml"
        _write_yaml(catalog, {"im_series": [entry]})
        spec = _make_spec()
        test_config = _config_with_catalog_paths(
            config,
            im_series_catalog_path=catalog,
        )
        with pytest.raises(
            ValueError,
            match=r"friction_windage: 必須キー 'model' がありません",
        ):
            _loader(test_config, logger).load(spec)


class TestForwardCableCatalogValidation:
    """ケーブルカタログ YAML の構造バリデーション。

    シリーズ選択 TSV にケーブル区間が含まれる場合のみカタログを引くため、
    ケーブルあり TSV をフィクスチャとして使う。
    """

    _CABLE_SERIES_TSV = (
        "im_cable_system_name\tBasic01_FeederIdeal30m\n\n"
        "im_series_name\tcable_series_name\tcable_length\t"
        "cable_conductor_model\n"
        "[-]\t[-]\t[m]\t[-]\n"
        "Basic01\tFeederIdeal\t30\tBasic01\n"
    )

    def _write_series_csv(self, tmp_path: Path) -> Path:
        path = tmp_path / "series_cable.tsv"
        path.write_text(self._CABLE_SERIES_TSV, encoding="utf-8")
        return path

    def _basic_cable_entry(self, name: str = "FeederIdeal") -> dict[str, Any]:
        return {
            "name": name,
            "shape_type": "ROUND",
            "conductor": {
                "resistance_per_length": _value_unit(0.0, "ohm/m"),
                "inductance_per_length": _value_unit(0.0, "H/m"),
            },
            "ground": {
                "resistance_length": _value_unit(1.0e9, "ohm*m"),
                "capacitance_per_length": _value_unit(0.0, "F/m"),
            },
        }

    def _basic_cable_root(self) -> dict[str, Any]:
        return {
            "cable_series": [self._basic_cable_entry()],
            "cable_conductor_models": {
                "Basic01": {"name": "BASIC", "params": []},
            },
        }

    def test_missing_conductor_resistance_raises_value_error(
        self,
        config: IConfig,
        logger: ILogger,
        tmp_path: Path,
    ) -> None:
        """conductor.resistance_per_length 欠落で ValueError。"""
        root = self._basic_cable_root()
        root["cable_series"][0]["conductor"].pop("resistance_per_length")
        catalog = tmp_path / "cable_missing_key.yaml"
        _write_yaml(catalog, root)
        test_config = _config_with_catalog_paths(
            config,
            cable_series_catalog_path=catalog,
        )
        spec = _make_spec(
            series_csv_path=self._write_series_csv(tmp_path),
        )
        with pytest.raises(
            ValueError,
            match=r"必須キー 'resistance_per_length' がありません",
        ):
            _loader(test_config, logger).load(spec)

    def test_duplicate_cable_series_name_raises(
        self,
        config: IConfig,
        logger: ILogger,
        tmp_path: Path,
    ) -> None:
        """ケーブルシリーズの name 重複で ValueError。"""
        root = self._basic_cable_root()
        root["cable_series"].append(self._basic_cable_entry("FeederIdeal"))
        catalog = tmp_path / "cable_dup_name.yaml"
        _write_yaml(catalog, root)
        test_config = _config_with_catalog_paths(
            config,
            cable_series_catalog_path=catalog,
        )
        spec = _make_spec(
            series_csv_path=self._write_series_csv(tmp_path),
        )
        with pytest.raises(
            ValueError,
            match=r"シリーズ名 'FeederIdeal' が重複",
        ):
            _loader(test_config, logger).load(spec)

    def test_cable_entry_without_name_raises(
        self,
        config: IConfig,
        logger: ILogger,
        tmp_path: Path,
    ) -> None:
        """ケーブルシリーズ entry の name 欠落で ValueError。"""
        root = self._basic_cable_root()
        nameless = self._basic_cable_entry()
        nameless.pop("name")
        root["cable_series"] = [nameless, self._basic_cable_entry()]
        catalog = tmp_path / "cable_no_name.yaml"
        _write_yaml(catalog, root)
        test_config = _config_with_catalog_paths(
            config,
            cable_series_catalog_path=catalog,
        )
        spec = _make_spec(
            series_csv_path=self._write_series_csv(tmp_path),
        )
        with pytest.raises(
            ValueError,
            match=r"cable_series\[\d+\] に name キーが",
        ):
            _loader(test_config, logger).load(spec)
