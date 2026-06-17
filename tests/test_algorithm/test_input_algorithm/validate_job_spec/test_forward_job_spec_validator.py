"""Forward 系（CartesianGrid / OperatingPoints 共通）ジョブ spec バリデータの単体テスト。

4 段フロー 1 段目 ``_validate_job_spec`` の契約を担保する。
正常系で通ること、および各必須パス・optional パスの不在を
**メッセージまで仕様化** して弾くことを確認する。

両モードは ``ForwardJobSpec`` / ``ForwardJobSpecValidator`` を共有し、
軸 TSV のレイアウトの違いだけが入力ファイル側にある。本テストでは
CartesianGrid 用軸 TSV と OperatingPoints 用軸 TSV の双方を
``axes_path`` に指定して、いずれも同じバリデータで通ることを確認する。
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from im_cable_system.engine.algorithm.input_algorithm.validate_job_spec import (
    ForwardJobSpecValidator,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.job_spec.forward import (
    ForwardJobSpec,
)
from tests.test_algorithm.test_input_algorithm._input_algorithm_helpers import (
    input_files_dir,
)


def _cartesian_grid_axes_path() -> Path:
    return (
        input_files_dir()
        / "axes_forward_by_cartesian_grid"
        / "cartesian_grid_v1.tsv"
    )


def _operating_points_axes_path() -> Path:
    return (
        input_files_dir()
        / "axes_forward_by_operating_points"
        / "operating_points_v1.tsv"
    )


def _make_spec(axes_path: Path) -> ForwardJobSpec:
    return ForwardJobSpec(
        series_selection_path=(
            input_files_dir() / "series_forward" / "basic01_nocable.tsv"
        ),
        axes_path=axes_path,
    )


def _make_validator(
    config: IConfig,
    logger: ILogger,
) -> ForwardJobSpecValidator:
    return ForwardJobSpecValidator.create(config=config, logger=logger)


class TestForwardJobSpecValidatorAcceptsValidSpec:
    """正常系: 両モードの軸 TSV のいずれでも通ることを確認する。"""

    def test_accepts_cartesian_grid_axes_path(
        self,
        config: IConfig,
        logger: ILogger,
    ) -> None:
        """CartesianGrid 用軸 TSV を指定した spec が通る。"""
        _make_validator(config, logger).validate(
            _make_spec(_cartesian_grid_axes_path()),
        )

    def test_accepts_operating_points_axes_path(
        self,
        config: IConfig,
        logger: ILogger,
    ) -> None:
        """OperatingPoints 用軸 TSV を指定した spec が通る。"""
        _make_validator(config, logger).validate(
            _make_spec(_operating_points_axes_path()),
        )

    def test_accepts_existing_optional_performance_curve_path(
        self,
        config: IConfig,
        logger: ILogger,
    ) -> None:
        """optional の performance_curve_path が実在ファイルなら通る。"""
        spec = replace(
            _make_spec(_cartesian_grid_axes_path()),
            performance_curve_path=(
                input_files_dir()
                / "im_performance_curve"
                / "currentdependent03_50Hz_115V.tsv"
            ),
        )
        _make_validator(config, logger).validate(spec)


class TestForwardJobSpecValidatorRejectsMissingPaths:
    """各必須パス・optional パスの不在を ValueError で弾く。"""

    def test_rejects_missing_series_selection_path(
        self,
        config: IConfig,
        logger: ILogger,
        tmp_path: Path,
    ) -> None:
        """series_selection_path が不在なら ValueError。"""
        spec = replace(
            _make_spec(_cartesian_grid_axes_path()),
            series_selection_path=tmp_path / "no_such_series.tsv",
        )
        with pytest.raises(
            ValueError,
            match="シリーズ選択ファイル がファイルとして存在しません",
        ):
            _make_validator(config, logger).validate(spec)

    def test_rejects_missing_axes_path(
        self,
        config: IConfig,
        logger: ILogger,
        tmp_path: Path,
    ) -> None:
        """axes_path が不在なら ValueError。"""
        spec = replace(
            _make_spec(_cartesian_grid_axes_path()),
            axes_path=tmp_path / "no_such_axes.tsv",
        )
        with pytest.raises(
            ValueError,
            match="軸ファイル がファイルとして存在しません",
        ):
            _make_validator(config, logger).validate(spec)

    def test_rejects_specified_but_missing_performance_curve_path(
        self,
        config: IConfig,
        logger: ILogger,
        tmp_path: Path,
    ) -> None:
        """performance_curve_path が指定されていて不在なら ValueError。"""
        spec = replace(
            _make_spec(_cartesian_grid_axes_path()),
            performance_curve_path=tmp_path / "no_such_curve.tsv",
        )
        with pytest.raises(
            ValueError,
            match="性能曲線ファイル がファイルとして存在しません",
        ):
            _make_validator(config, logger).validate(spec)


class TestForwardJobSpecValidatorRejectsNonePaths:
    """必須パスが ``None`` の場合に ValueError で弾く。"""

    def test_rejects_none_series_selection_path(
        self,
        config: IConfig,
        logger: ILogger,
    ) -> None:
        """series_selection_path が未指定なら ValueError。"""
        spec = replace(
            _make_spec(_cartesian_grid_axes_path()),
            series_selection_path=None,  # type: ignore[arg-type]
        )
        with pytest.raises(
            ValueError, match="シリーズ選択ファイル が指定されていません"
        ):
            _make_validator(config, logger).validate(spec)

    def test_rejects_none_axes_path(
        self,
        config: IConfig,
        logger: ILogger,
    ) -> None:
        """axes_path が未指定なら ValueError。"""
        spec = replace(
            _make_spec(_cartesian_grid_axes_path()),
            axes_path=None,  # type: ignore[arg-type]
        )
        with pytest.raises(
            ValueError,
            match="軸ファイル が指定されていません",
        ):
            _make_validator(config, logger).validate(spec)
