"""estimate_params 用・ジョブ spec バリデータ（最低限）。

統合 TSV のパス存在を確認する。境界 YAML は Runner が Config に注入するため、
JobSpec では扱わない。
"""

from __future__ import annotations

from im_cable_system.engine.algorithm.input_algorithm.validate_job_spec.i_job_spec_validator import (  # noqa: E501
    IJobSpecValidator,
)
from im_cable_system.engine.algorithm.input_algorithm.validate_job_spec.path_checks import (  # noqa: E501
    check_path_is_file,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.job_spec.estimate_params import (
    EstimateParamsJobSpec,
)


class EstimateParamsJobSpecValidator(IJobSpecValidator[EstimateParamsJobSpec]):
    """estimate_params 経路用・ジョブ spec バリデータ。

    統合 TSV の存在を検査する。
    """

    def __init__(self, config: IConfig, logger: ILogger) -> None:
        """初期化する。

        本クラスは ``validate`` の中で ``config`` / ``logger`` を参照しないが、
        開発ガイドライン（``docs/rules/``）の「``IConfig`` / ``ILogger`` は属性として保持する」
        ルールに従い保持する。
        """
        self._config: IConfig = config
        self._logger: ILogger = logger

    @classmethod
    def create(
        cls,
        config: IConfig,
        logger: ILogger,
    ) -> EstimateParamsJobSpecValidator:
        """バリデータを生成する。"""
        return cls(config=config, logger=logger)

    def validate(self, job_spec: EstimateParamsJobSpec) -> None:
        """ジョブ spec を検証する。

        Args:
            job_spec: 1 ジョブ分の spec（統合 TSV 1 つ）。

        Raises:
            ValueError: 統合 TSV が未指定または存在しない場合。
        """
        check_path_is_file(job_spec.input_tsv_path, "統合入力 TSV")
