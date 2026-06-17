"""Forward 系 性能曲線 TSV ローダの構造バリデーションテスト。

``performance_curve_parser`` 単体での挙動を ``ForwardLoader`` 経由で
確認する。メタ表の ``name`` セルの空・重複や、曲線ヘッダの列重複など、
構造・スキーマ違反が ``ValueError`` として上がることを担保する。

責務スコープの注記:
    本テストは **Loader 段の責務（単位文字列を ``strip()`` のみで raw
    保持する）** を確定する。``[%]`` / ``[-]`` のような比率単位の TSV を
    Loader 単体テストが許容しているのは、**経路ごとの単位ポリシー判定が
    Assembler 段の責務** であり、Loader はそれに先んじて raise しないと
    いう責務分離（``ImPerformanceCurveLoadedData`` の docstring 参照）に
    従っているため。したがって、ここで ``[%]`` / ``[-]`` の TSV が読めて
    も Forward 経路全体として許容されることは意味しない。Forward
    Assembler は ``power`` / ``current`` / ``torque`` 列の比率単位を
    ``ValueError`` で拒否する（テストは
    ``test_forward_performance_curve_dto_builder_unit_rejection`` および
    ``test_forward_loader_assembler_unit_pair`` 参照）。
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
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
    performance_curve_path: Path,
) -> ForwardJobSpec:
    return ForwardJobSpec(
        series_selection_path=(_series_forward_dir() / "basic01_nocable.tsv"),
        axes_path=(
            _axes_forward_by_cartesian_grid_dir() / "cartesian_grid_v1.tsv"
        ),
        performance_curve_path=performance_curve_path,
    )


def _loader(config: IConfig, logger: ILogger) -> ForwardLoader:
    return ForwardLoader.create(config=config, logger=logger)


_CURVE_HEADER = (
    "rotational_speed\tpower\tcurrent\tpower_factor\tefficiency\n"
    "[rpm]\t[-]\t[%]\t[-]\t[-]\n"
    "1500\t0.01\t12.0\t0.10\t0.30\n"
)


def _meta_prefix(
    poles_line: str = "poles\t4\t-\n",
    supply_freq_line: str = "supply_frequency\t50\tHz\n",
    supply_volt_line: str = "supply_voltage\t115.47\tV\n",
    name_line: str = "im_performance_curve_name\tTest\n",
) -> str:
    return (
        name_line
        + "name\tvalue\tunit\n"
        + poles_line
        + supply_freq_line
        + supply_volt_line
        + "\n"
    )


class TestForwardPerformanceCurveLoaderMetaValidation:
    """性能曲線 TSV のメタ表バリデーション。"""

    def test_empty_name_cell_in_meta_raises(
        self,
        config: IConfig,
        logger: ILogger,
        tmp_path: Path,
    ) -> None:
        """メタ表に ``name`` セルが空の行があるとエラー。

        従来は空 ``name`` を空キー ``""`` として meta dict に格納し、
        後段で混乱の原因になっていた。LoadData 段で弾く。
        """
        path = tmp_path / "pc_empty_name.tsv"
        path.write_text(
            "im_performance_curve_name\tTest\n"
            "name\tvalue\tunit\n"
            "poles\t4\t-\n"
            "\t99\t-\n"
            "supply_frequency\t50\tHz\n"
            "supply_voltage\t115.47\tV\n"
            "\n" + _CURVE_HEADER,
            encoding="utf-8",
        )
        spec = _make_spec(performance_curve_path=path)
        with pytest.raises(
            ValueError,
            match="name セルが空の行があります",
        ):
            _loader(config, logger).load(spec)

    def test_duplicate_meta_key_raises(
        self,
        config: IConfig,
        logger: ILogger,
        tmp_path: Path,
    ) -> None:
        """メタ表で同じキーが 2 回現れるとエラー。"""
        path = tmp_path / "pc_dup_meta.tsv"
        path.write_text(
            "im_performance_curve_name\tTest\n"
            "name\tvalue\tunit\n"
            "poles\t4\t-\n"
            "poles\t6\t-\n"
            "supply_frequency\t50\tHz\n"
            "supply_voltage\t115.47\tV\n"
            "\n" + _CURVE_HEADER,
            encoding="utf-8",
        )
        spec = _make_spec(performance_curve_path=path)
        with pytest.raises(
            ValueError,
            match=r"メタ表にキー 'poles' が重複",
        ):
            _loader(config, logger).load(spec)


class TestForwardPerformanceCurveLoaderHeaderValidation:
    """性能曲線 TSV の曲線ヘッダバリデーション。"""

    def test_duplicate_curve_column_raises(
        self,
        config: IConfig,
        logger: ILogger,
        tmp_path: Path,
    ) -> None:
        """曲線ヘッダで必須列が重複しているとエラー。"""
        path = tmp_path / "pc_dup_col.tsv"
        path.write_text(
            _meta_prefix()
            + "rotational_speed\tpower\tpower\tcurrent\tpower_factor\t"
            "efficiency\n"
            "[rpm]\t[-]\t[-]\t[%]\t[-]\t[-]\n"
            "1500\t0.01\t0.01\t12.0\t0.10\t0.30\n",
            encoding="utf-8",
        )
        spec = _make_spec(performance_curve_path=path)
        with pytest.raises(
            ValueError,
            match=r"列 'power' が複数",
        ):
            _loader(config, logger).load(spec)


class TestForwardPerformanceCurveLoaderFlexibleColumns:
    """rotational_speed + 他列のうち 1 本以上で読めることの確認。"""

    def test_rotational_speed_only_raises(
        self,
        config: IConfig,
        logger: ILogger,
        tmp_path: Path,
    ) -> None:
        """``rotational_speed`` 単独だと残差にもプロットにも使えないためエラー。"""
        path = tmp_path / "pc_rpm_only.tsv"
        path.write_text(
            _meta_prefix() + "rotational_speed\n[rpm]\n1500\n",
            encoding="utf-8",
        )
        spec = _make_spec(performance_curve_path=path)
        with pytest.raises(
            ValueError,
            match=r"少なくとも 1 列が必要",
        ):
            _loader(config, logger).load(spec)

    def test_rotational_speed_missing_raises(
        self,
        config: IConfig,
        logger: ILogger,
        tmp_path: Path,
    ) -> None:
        """``rotational_speed`` 欠落はエラー。"""
        path = tmp_path / "pc_no_rpm.tsv"
        path.write_text(
            _meta_prefix() + "power\tcurrent\tpower_factor\tefficiency\n"
            "[-]\t[%]\t[-]\t[-]\n"
            "0.01\t12.0\t0.10\t0.30\n",
            encoding="utf-8",
        )
        spec = _make_spec(performance_curve_path=path)
        with pytest.raises(
            ValueError,
            match=r"必須列 'rotational_speed' がありません",
        ):
            _loader(config, logger).load(spec)

    def test_rotational_speed_plus_current_only_loads(
        self,
        config: IConfig,
        logger: ILogger,
        tmp_path: Path,
    ) -> None:
        """``rotational_speed`` + ``current`` のみで loaded data が組み立つ。

        ``power`` / ``power_factor`` / ``efficiency`` / ``torque`` は
        ``None`` のまま残る。
        """
        path = tmp_path / "pc_current_only.tsv"
        path.write_text(
            _meta_prefix() + "rotational_speed\tcurrent\n"
            "[rpm]\t[%]\n"
            "1500\t12.0\n"
            "1490\t15.0\n",
            encoding="utf-8",
        )
        spec = _make_spec(performance_curve_path=path)
        loaded = _loader(config, logger).load(spec)
        pc = loaded.im_performance_curve
        assert pc is not None
        assert pc.rotational_speed.shape == (2,)
        assert pc.current is not None
        assert pc.current.shape == (2,)
        assert pc.power is None
        assert pc.power_unit is None
        assert pc.power_factor is None
        assert pc.efficiency is None
        assert pc.torque is None

    def test_rotational_speed_plus_torque_only_loads(
        self,
        config: IConfig,
        logger: ILogger,
        tmp_path: Path,
    ) -> None:
        """``rotational_speed`` + ``torque`` のみでも loaded data が組み立つ。

        ``power`` が ``None`` のまま読まれ、assembler 側で ``P = T·ω`` の
        逆算が行われることを別テストで確認する。
        """
        path = tmp_path / "pc_torque_only.tsv"
        path.write_text(
            _meta_prefix() + "rotational_speed\ttorque\n"
            "[rpm]\t[N*m]\n"
            "1500\t1.0\n"
            "1490\t2.0\n",
            encoding="utf-8",
        )
        spec = _make_spec(performance_curve_path=path)
        loaded = _loader(config, logger).load(spec)
        pc = loaded.im_performance_curve
        assert pc is not None
        assert pc.torque is not None
        assert pc.torque.shape == (2,)
        assert pc.power is None
        assert pc.current is None

    def test_rotational_speed_plus_power_only_loads(
        self,
        config: IConfig,
        logger: ILogger,
        tmp_path: Path,
    ) -> None:
        """``rotational_speed`` + ``power`` のみで loaded data が組み立つ。

        ``current`` / ``power_factor`` / ``efficiency`` / ``torque`` は
        ``None`` のまま残り、``power`` のみ非 None になる。
        """
        path = tmp_path / "pc_power_only.tsv"
        path.write_text(
            _meta_prefix() + "rotational_speed\tpower\n"
            "[rpm]\t[-]\n"
            "1500\t0.01\n"
            "1490\t0.02\n",
            encoding="utf-8",
        )
        spec = _make_spec(performance_curve_path=path)
        loaded = _loader(config, logger).load(spec)
        pc = loaded.im_performance_curve
        assert pc is not None
        assert pc.rotational_speed.shape == (2,)
        assert pc.power is not None
        assert pc.power.shape == (2,)
        assert pc.power_unit is not None
        assert pc.current is None
        assert pc.power_factor is None
        assert pc.efficiency is None
        assert pc.torque is None

    def test_rotational_speed_plus_power_factor_only_loads(
        self,
        config: IConfig,
        logger: ILogger,
        tmp_path: Path,
    ) -> None:
        """``rotational_speed`` + ``power_factor`` のみで loaded data が組み立つ。"""
        path = tmp_path / "pc_pf_only.tsv"
        path.write_text(
            _meta_prefix() + "rotational_speed\tpower_factor\n"
            "[rpm]\t[-]\n"
            "1500\t0.85\n"
            "1490\t0.80\n",
            encoding="utf-8",
        )
        spec = _make_spec(performance_curve_path=path)
        loaded = _loader(config, logger).load(spec)
        pc = loaded.im_performance_curve
        assert pc is not None
        assert pc.rotational_speed.shape == (2,)
        assert pc.power_factor is not None
        assert pc.power_factor.shape == (2,)
        assert pc.power_factor_unit is not None
        assert pc.power is None
        assert pc.current is None
        assert pc.efficiency is None
        assert pc.torque is None

    def test_rotational_speed_plus_efficiency_only_loads(
        self,
        config: IConfig,
        logger: ILogger,
        tmp_path: Path,
    ) -> None:
        """``rotational_speed`` + ``efficiency`` のみで loaded data が組み立つ。"""
        path = tmp_path / "pc_eff_only.tsv"
        path.write_text(
            _meta_prefix() + "rotational_speed\tefficiency\n"
            "[rpm]\t[-]\n"
            "1500\t0.90\n"
            "1490\t0.85\n",
            encoding="utf-8",
        )
        spec = _make_spec(performance_curve_path=path)
        loaded = _loader(config, logger).load(spec)
        pc = loaded.im_performance_curve
        assert pc is not None
        assert pc.rotational_speed.shape == (2,)
        assert pc.efficiency is not None
        assert pc.efficiency.shape == (2,)
        assert pc.efficiency_unit is not None
        assert pc.power is None
        assert pc.current is None
        assert pc.power_factor is None
        assert pc.torque is None


class TestForwardPerformanceCurveLoaderObservedNanCells:
    """観測列の空セルは ``np.nan`` として保持される（torque 含む）。"""

    def test_observed_empty_cells_become_nan(
        self,
        config: IConfig,
        logger: ILogger,
        tmp_path: Path,
    ) -> None:
        """``power`` / ``current`` 列の空セルが ``np.nan`` で読まれる。"""
        path = tmp_path / "pc_observed_nan.tsv"
        path.write_text(
            _meta_prefix() + "rotational_speed\tpower\tcurrent\n"
            "[rpm]\t[-]\t[%]\n"
            "1500\t0.01\t12.0\n"
            "1490\t\t15.0\n"
            "1480\t0.03\t\n",
            encoding="utf-8",
        )
        spec = _make_spec(performance_curve_path=path)
        loaded = _loader(config, logger).load(spec)
        pc = loaded.im_performance_curve
        assert pc is not None
        assert pc.power is not None
        assert np.isnan(pc.power[1])
        np.testing.assert_allclose(pc.power[[0, 2]], [0.01, 0.03])
        assert pc.current is not None
        assert np.isnan(pc.current[2])
        np.testing.assert_allclose(pc.current[[0, 1]], [12.0, 15.0])

    def test_torque_column_empty_cell_now_allowed_as_nan(
        self,
        config: IConfig,
        logger: ILogger,
        tmp_path: Path,
    ) -> None:
        """``torque`` 列の空セルは ``np.nan`` で許容される（旧仕様の raise から変更）。"""
        path = tmp_path / "pc_torque_nan.tsv"
        path.write_text(
            _meta_prefix() + "rotational_speed\ttorque\n"
            "[rpm]\t[Nm]\n"
            "1500\t1.0\n"
            "1490\t\n"
            "1480\t3.0\n",
            encoding="utf-8",
        )
        spec = _make_spec(performance_curve_path=path)
        loaded = _loader(config, logger).load(spec)
        pc = loaded.im_performance_curve
        assert pc is not None
        assert pc.torque is not None
        assert np.isnan(pc.torque[1])
        np.testing.assert_allclose(pc.torque[[0, 2]], [1.0, 3.0])

    def test_non_numeric_observed_cell_still_raises(
        self,
        config: IConfig,
        logger: ILogger,
        tmp_path: Path,
    ) -> None:
        """非空かつ非数値の観測セルは ``ValueError`` のまま。"""
        path = tmp_path / "pc_bad_value.tsv"
        path.write_text(
            _meta_prefix() + "rotational_speed\tpower\n[rpm]\t[-]\n1500\tabc\n",
            encoding="utf-8",
        )
        spec = _make_spec(performance_curve_path=path)
        with pytest.raises(ValueError):
            _loader(config, logger).load(spec)
