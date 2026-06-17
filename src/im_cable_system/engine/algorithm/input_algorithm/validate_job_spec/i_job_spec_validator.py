"""ジョブ spec の最小バリデーション契約。

4 段フローの 1 段目 ``_validate_job_spec`` で使われる契約。
具象は :meth:`create` でインスタンスを生成し、:meth:`validate` で
パス存在チェックなど **ファイルを開く前に確認できる検査** のみを行う。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from im_cable_system.engine.shared.config import IConfig, ILogger

JobSpecT = TypeVar("JobSpecT")


class IJobSpecValidator(ABC, Generic[JobSpecT]):
    """ジョブ spec を検証する契約。

    Generic 型引数:
        JobSpecT: :meth:`validate` が受け取るモード固有のジョブ spec 型。
    """

    @classmethod
    @abstractmethod
    def create(
        cls,
        config: IConfig,
        logger: ILogger,
    ) -> IJobSpecValidator[JobSpecT]:
        """バリデータインスタンスを生成する。

        Args:
            config: 設定。
            logger: ロガー。

        Returns:
            IJobSpecValidator: 生成されたバリデータ。
        """
        raise NotImplementedError

    @abstractmethod
    def validate(self, job_spec: JobSpecT) -> None:
        """ジョブ spec を検証する。

        Args:
            job_spec: 検証対象のジョブ spec。

        Raises:
            ValueError: 検査に失敗した場合。
        """
        raise NotImplementedError
