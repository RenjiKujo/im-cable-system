"""EstimateParamsInputStage の疎通テスト（最小構成）。

1 つの統合 TSV（``input_for_estimate_params.tsv``）から候補軸の直積分の
InputDto 束が返る経路のみを確認する。``cable_conductor_model`` 軸には
``NONE`` 候補（ケーブル無し）と実モデル候補が混在しており、両者がそれぞれ
``cable=None`` / ``cable is not None`` の :class:`InputDto` を作ることを
確認する。詳細なロード・組み立て・検証ロジックは algorithm 層で別途カバー
される。
"""

from __future__ import annotations

from pathlib import Path

from im_cable_system.engine.processor.input_stage import (
    EstimateParamsInputStage,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.input import InputDto
from im_cable_system.engine.shared.job_spec.estimate_params import (
    EstimateParamsJobSpec,
)


def _make_job_spec(input_files_dir: Path) -> EstimateParamsJobSpec:
    """フル統合 TSV を指す JobSpec。"""
    return EstimateParamsJobSpec(
        input_tsv_path=(
            input_files_dir
            / "estimate_params"
            / "input_for_estimate_params.tsv"
        ),
    )


def test_process_returns_candidate_product_input_dtos(
    config: IConfig,
    logger: ILogger,
    input_files_dir: Path,
) -> None:
    """1 ジョブ spec から候補直積分の InputDto 束が返る。

    候補数: primary=3, excitation=3, secondary_single=4,
    secondary_double_inner=4, secondary_double_outer=4,
    cable_conductor=4（NONE + 3 モデル）。単一かご 3*3*4*4=144 件と
    二重かご 3*3*4*4*4=576 件で合計 720 件になる。
    """
    spec = _make_job_spec(input_files_dir)

    stage = EstimateParamsInputStage.create(config=config, logger=logger)
    inputs = stage.process(spec)

    dtos = inputs.get_all()
    assert len(dtos) == 720
    assert all(isinstance(dto, InputDto) for dto in dtos)
    # 直積の先頭は cable_conductor 候補先頭の ``NONE`` に対応し、cable は ``None``。
    assert dtos[0].cable is None
    # ``NONE`` 以外の候補も含まれるので、cable を持つ InputDto も存在する。
    assert any(dto.cable is not None for dto in dtos)
