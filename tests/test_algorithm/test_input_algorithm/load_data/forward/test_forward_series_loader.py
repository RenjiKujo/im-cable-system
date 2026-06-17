"""Forward 系列 TSV ローダ（``cable_conductor_model`` 列）のテスト。

``cable_conductor_model`` 列の解釈はシリーズ選択 TSV パーサの責務であり、
CartesianGrid / OperatingPoints の両モードで共通の
``series_selection_parser`` が処理する。本テストは CartesianGrid 用軸 TSV
を代表として、シリーズ TSV 由来の中間表現が正しく組み立つことを確認する。
"""

from __future__ import annotations

from pathlib import Path

import pytest

from im_cable_system.engine.algorithm.input_algorithm.load_data import (
    ForwardLoader,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
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
    series_csv_path: Path,
    axes_csv_path: Path,
) -> ForwardJobSpec:
    """テスト用の :class:`ForwardJobSpec` を生成する。"""
    return ForwardJobSpec(
        series_selection_path=series_csv_path,
        axes_path=axes_csv_path,
    )


def _loader(config: IConfig, logger: ILogger) -> ForwardLoader:
    return ForwardLoader.create(config=config, logger=logger)


class TestForwardSeriesLoaderConductorProfile:
    """cable_conductor_model 列のロードとバリデーション。"""

    def test_nocable_has_no_cable(
        self,
        config: IConfig,
        logger: ILogger,
    ) -> None:
        """nocable 系列は cable None。"""
        spec = _make_spec(
            series_csv_path=_series_forward_dir() / "basic01_nocable.tsv",
            axes_csv_path=(
                _axes_forward_by_cartesian_grid_dir() / "cartesian_grid_v1.tsv"
            ),
        )
        loaded = _loader(config, logger).load(spec)
        assert loaded.cable is None
        assert loaded.im.name == "Basic01"

    def test_cable_job_loads_basic01_profile(
        self,
        config: IConfig,
        logger: ILogger,
    ) -> None:
        """ケーブルあり ideal 系列は Basic01 導体モデル。"""
        spec = _make_spec(
            series_csv_path=(
                _series_forward_dir()
                / "slipdependent01_ideal_feeder30m_ideal_lead10m.tsv"
            ),
            axes_csv_path=(
                _axes_forward_by_cartesian_grid_dir() / "cartesian_grid_v1.tsv"
            ),
        )
        loaded = _loader(config, logger).load(spec)
        cable = loaded.cable
        assert cable is not None
        assert len(cable.sections) == 2
        assert cable.conductor_model == "BASIC"
        assert cable.sections[0].name == "FeederIdeal"
        assert cable.sections[1].name == "LeadIdeal"

    def test_cable_job_loads_current_dependent_skin_profile(
        self,
        config: IConfig,
        logger: ILogger,
    ) -> None:
        """CurrentDependent01 + Real ケーブルは CURRENT_DEPENDENT_SKIN_EFFECT_V1。"""
        spec = _make_spec(
            series_csv_path=(
                _series_forward_dir()
                / "currentdependent01_real_feeder30m_real_lead10m.tsv"
            ),
            axes_csv_path=(
                _axes_forward_by_cartesian_grid_dir() / "cartesian_grid_v1.tsv"
            ),
        )
        loaded = _loader(config, logger).load(spec)
        cable = loaded.cable
        assert cable is not None
        assert cable.conductor_model == "CURRENT_DEPENDENT_SKIN_EFFECT_V1"
        assert cable.conductor_model_params is not None

    def test_duplicate_cable_conductor_model_raises(
        self,
        config: IConfig,
        logger: ILogger,
        tmp_path: Path,
    ) -> None:
        """2 行目以降に cable_conductor_model を書くとエラー。"""
        series_path = tmp_path / "series_dup_profile.tsv"
        series_path.write_text(
            "im_cable_system_name\tTest\n\n"
            "im_series_name\tcable_series_name\tcable_length\t"
            "cable_conductor_model\n"
            "[-]\t[-]\t[m]\t[-]\n"
            "Basic01\tFeederIdeal\t30\tBasic01\n"
            "\tLeadIdeal\t10\tBasic01\n",
            encoding="utf-8",
        )
        spec = _make_spec(
            series_csv_path=series_path,
            axes_csv_path=(
                _axes_forward_by_cartesian_grid_dir() / "cartesian_grid_v1.tsv"
            ),
        )
        with pytest.raises(ValueError, match="1 つだけ"):
            _loader(config, logger).load(spec)

    def test_duplicate_im_series_name_raises(
        self,
        config: IConfig,
        logger: ILogger,
        tmp_path: Path,
    ) -> None:
        """2 行目以降に im_series_name を書くとエラー。

        ``im_series_name`` セルがテーブル全体で 1 つしか許されないこと
        （同一値・別値を問わず）を確認する。
        """
        series_path = tmp_path / "series_dup_im.tsv"
        series_path.write_text(
            "im_cable_system_name\tTest\n\n"
            "im_series_name\tcable_series_name\tcable_length\t"
            "cable_conductor_model\n"
            "[-]\t[-]\t[m]\t[-]\n"
            "Basic01\tFeederIdeal\t30\tBasic01\n"
            "Basic01\tLeadIdeal\t10\n",
            encoding="utf-8",
        )
        spec = _make_spec(
            series_csv_path=series_path,
            axes_csv_path=(
                _axes_forward_by_cartesian_grid_dir() / "cartesian_grid_v1.tsv"
            ),
        )
        with pytest.raises(
            ValueError,
            match="im_series_name はテーブル全体で 1 つだけ指定してください",
        ):
            _loader(config, logger).load(spec)

    def test_legacy_esp_assembly_name_is_not_used(
        self,
        config: IConfig,
        logger: ILogger,
        tmp_path: Path,
    ) -> None:
        """旧メタキー esp_assembly_name は Forward 系では扱わない。"""
        series_path = tmp_path / "series_legacy_meta.tsv"
        series_path.write_text(
            "esp_assembly_name\tTest\n\n"
            "im_series_name\tcable_series_name\tcable_length\t"
            "cable_conductor_model\n"
            "[-]\t[-]\t[m]\t[-]\n"
            "Basic01\n",
            encoding="utf-8",
        )
        spec = _make_spec(
            series_csv_path=series_path,
            axes_csv_path=(
                _axes_forward_by_cartesian_grid_dir() / "cartesian_grid_v1.tsv"
            ),
        )
        with pytest.raises(ValueError, match="im_cable_system_name"):
            _loader(config, logger).load(spec)

    def test_legacy_cable_length_ft_column_is_not_used(
        self,
        config: IConfig,
        logger: ILogger,
        tmp_path: Path,
    ) -> None:
        """旧列 cable_length_ft は Forward 系では扱わない。"""
        series_path = tmp_path / "series_legacy_length_column.tsv"
        series_path.write_text(
            "im_cable_system_name\tTest\n\n"
            "im_series_name\tcable_series_name\tcable_length_ft\t"
            "cable_conductor_model\n"
            "[-]\t[-]\t[ft]\t[-]\n"
            "Basic01\tFeederIdeal\t30\tBasic01\n",
            encoding="utf-8",
        )
        spec = _make_spec(
            series_csv_path=series_path,
            axes_csv_path=(
                _axes_forward_by_cartesian_grid_dir() / "cartesian_grid_v1.tsv"
            ),
        )
        with pytest.raises(ValueError, match="cable_length 列"):
            _loader(config, logger).load(spec)

    def test_cable_row_can_appear_before_im_series_name(
        self,
        config: IConfig,
        logger: ILogger,
        tmp_path: Path,
    ) -> None:
        """ケーブル行は im_series_name の後ろにある必要はない。

        ``im_series_name`` はテーブル全体で 1 つだけ確定すればよく、
        ケーブル区間は行順ではなくテーブル全体の IM に紐づく。
        """
        series_path = tmp_path / "series_cable_before_im.tsv"
        series_path.write_text(
            "im_cable_system_name\tTest\n\n"
            "im_series_name\tcable_series_name\tcable_length\t"
            "cable_conductor_model\n"
            "[-]\t[-]\t[m]\t[-]\n"
            "\tFeederIdeal\t30\tBasic01\n"
            "Basic01\n",
            encoding="utf-8",
        )
        spec = _make_spec(
            series_csv_path=series_path,
            axes_csv_path=(
                _axes_forward_by_cartesian_grid_dir() / "cartesian_grid_v1.tsv"
            ),
        )
        loaded = _loader(config, logger).load(spec)
        assert loaded.im.name == "Basic01"
        assert loaded.cable is not None
        assert loaded.cable.sections[0].name == "FeederIdeal"

    def test_cable_length_unit_is_preserved_verbatim_at_loader(
        self,
        config: IConfig,
        logger: ILogger,
        tmp_path: Path,
    ) -> None:
        """ケーブル長単位は Loader 段で ``strip()`` のみで保持される。

        ``axes_parser`` と同じ責務分担で、Loader 段では角括弧
        ``[...]`` を剥がさず、表記揺れの吸収（``feet``→``ft`` 等）も
        行わない。角括弧剥がしは ``assemble_input_dto`` 段の
        ``cable_dto_builder._normalize_unit_cell`` が担い、単位値域
        の妥当性は ``FloatLengthDto.__post_init__`` が担う。

        本テストは Loader 単体で、角括弧つきの単位文字列
        （``[furlong]``）が ``[furlong]`` のままケーブル区間に
        保持されることを確認する。
        """
        series_path = tmp_path / "series_unknown_unit.tsv"
        series_path.write_text(
            "im_cable_system_name\tTest\n\n"
            "im_series_name\tcable_series_name\tcable_length\t"
            "cable_conductor_model\n"
            "[-]\t[-]\t[furlong]\t[-]\n"
            "Basic01\tFeederIdeal\t30\tBasic01\n",
            encoding="utf-8",
        )
        spec = _make_spec(
            series_csv_path=series_path,
            axes_csv_path=(
                _axes_forward_by_cartesian_grid_dir() / "cartesian_grid_v1.tsv"
            ),
        )
        loaded = _loader(config, logger).load(spec)
        cable = loaded.cable
        assert cable is not None
        assert cable.sections[0].length_unit == "[furlong]"

    def test_empty_cable_length_unit_is_preserved_verbatim_at_loader(
        self,
        config: IConfig,
        logger: ILogger,
        tmp_path: Path,
    ) -> None:
        """単位行のセルが空ならば Loader 段でも空文字列のまま保持される。

        既定 ``ft`` への自動補完は行わない（``axes_parser`` と同等の
        ``strip()`` のみ）。
        """
        series_path = tmp_path / "series_empty_unit.tsv"
        series_path.write_text(
            "im_cable_system_name\tTest\n\n"
            "im_series_name\tcable_series_name\tcable_length\t"
            "cable_conductor_model\n"
            "[-]\t[-]\t\t[-]\n"
            "Basic01\tFeederIdeal\t30\tBasic01\n",
            encoding="utf-8",
        )
        spec = _make_spec(
            series_csv_path=series_path,
            axes_csv_path=(
                _axes_forward_by_cartesian_grid_dir() / "cartesian_grid_v1.tsv"
            ),
        )
        loaded = _loader(config, logger).load(spec)
        cable = loaded.cable
        assert cable is not None
        assert cable.sections[0].length_unit == ""


class TestForwardSeriesLoaderHeaderValidation:
    """シリーズ選択 TSV のヘッダ・テーブル構造のバリデーション。"""

    def test_multiple_im_series_name_header_rows_raise(
        self,
        config: IConfig,
        logger: ILogger,
        tmp_path: Path,
    ) -> None:
        """``im_series_name`` で始まるヘッダ行は 1 つだけ許可される。

        2 つ以上書くとテーブル境界が決まらないため ``ValueError``。
        """
        series_path = tmp_path / "series_dup_header_row.tsv"
        series_path.write_text(
            "im_cable_system_name\tTest\n\n"
            "im_series_name\tcable_series_name\tcable_length\t"
            "cable_conductor_model\n"
            "[-]\t[-]\t[m]\t[-]\n"
            "Basic01\tFeederIdeal\t30\tBasic01\n"
            "\n"
            "im_series_name\tcable_series_name\tcable_length\t"
            "cable_conductor_model\n"
            "[-]\t[-]\t[m]\t[-]\n"
            "Basic02\n",
            encoding="utf-8",
        )
        spec = _make_spec(
            series_csv_path=series_path,
            axes_csv_path=(
                _axes_forward_by_cartesian_grid_dir() / "cartesian_grid_v1.tsv"
            ),
        )
        with pytest.raises(
            ValueError,
            match="im_series_name ヘッダ行が複数あります",
        ):
            _loader(config, logger).load(spec)

    def test_duplicate_table_column_raises(
        self,
        config: IConfig,
        logger: ILogger,
        tmp_path: Path,
    ) -> None:
        """テーブルヘッダで必須列が重複していると ``ValueError``。"""
        series_path = tmp_path / "series_dup_column.tsv"
        series_path.write_text(
            "im_cable_system_name\tTest\n\n"
            "im_series_name\tcable_series_name\tcable_length\t"
            "cable_series_name\tcable_conductor_model\n"
            "[-]\t[-]\t[m]\t[-]\t[-]\n"
            "Basic01\tFeederIdeal\t30\tFeederIdeal\tBasic01\n",
            encoding="utf-8",
        )
        spec = _make_spec(
            series_csv_path=series_path,
            axes_csv_path=(
                _axes_forward_by_cartesian_grid_dir() / "cartesian_grid_v1.tsv"
            ),
        )
        with pytest.raises(
            ValueError,
            match=r"必須列 'cable_series_name' が複数",
        ):
            _loader(config, logger).load(spec)
