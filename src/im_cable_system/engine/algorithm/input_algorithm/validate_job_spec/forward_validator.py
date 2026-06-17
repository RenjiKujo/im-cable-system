"""Forward 系（CartesianGrid / OperatingPoints 共通）ジョブ spec バリデータ。

``ForwardJobSpec`` の各パス（必須 2 本 + optional 性能曲線）が通常ファイル
として存在することのみを検証する。モードによる分岐は持たない。
"""

from __future__ import annotations

from im_cable_system.engine.algorithm.input_algorithm.validate_job_spec.i_job_spec_validator import (  # noqa: E501
    IJobSpecValidator,
)
from im_cable_system.engine.algorithm.input_algorithm.validate_job_spec.path_checks import (  # noqa: E501
    check_path_is_file,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.job_spec.forward import (
    ForwardJobSpec,
)


class ForwardJobSpecValidator(IJobSpecValidator[ForwardJobSpec]):
    """Forward 系（CartesianGrid / OperatingPoints 共通）ジョブ spec バリデータ。

    検査対象は次のとおり。

    - 必須 2 パス（シリーズ選択 / 軸 TSV）がそれぞれ通常ファイル
      として存在すること。
    - optional の ``performance_curve_path`` が指定されている場合、
      通常ファイルとして存在すること。
      未指定（``None``）の場合は読み込みをスキップする前提で通過する。
    - カタログ YAML は Config の責務として ``ForwardLoader`` で解決する。
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
    ) -> ForwardJobSpecValidator:
        """バリデータを生成する。"""
        return cls(config=config, logger=logger)

    def validate(self, job_spec: ForwardJobSpec) -> None:
        """ジョブ spec のパス存在を検証する。

        Args:
            job_spec: 1 ジョブ分のパス束。

        Raises:
            ValueError: いずれかのパスが未指定、または通常ファイルとして
                存在しない場合。
        """
        check_path_is_file(
            job_spec.series_selection_path, "シリーズ選択ファイル"
        )
        check_path_is_file(job_spec.axes_path, "軸ファイル")
        if job_spec.performance_curve_path is not None:
            check_path_is_file(
                job_spec.performance_curve_path,
                "性能曲線ファイル",
            )
