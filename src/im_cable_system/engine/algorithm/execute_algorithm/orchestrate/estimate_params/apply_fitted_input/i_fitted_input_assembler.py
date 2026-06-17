"""フィット結果を InputDto へ反映するアセンブラのインターフェース。"""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np

from im_cable_system.engine.algorithm.execute_algorithm.orchestrate.estimate_params.support.descriptor import (  # noqa: E501
    FittableParamDescriptor,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.input import (
    InputDto,
)


class IFittedInputAssembler(ABC):
    """フィット記述子と試行ベクトルを ``InputDto`` に埋め込む。"""

    @classmethod
    @abstractmethod
    def create(
        cls,
        config: IConfig,
        logger: ILogger,
    ) -> IFittedInputAssembler:
        """config と logger を受け取り、自身のインスタンスを生成する。

        Args:
            config: 設定オブジェクト。
            logger: ロガーオブジェクト。

        Returns:
            IFittedInputAssembler: 生成されたアセンブラ。
        """
        pass

    @abstractmethod
    def assemble(
        self,
        input_dto: InputDto,
        descriptors: list[FittableParamDescriptor],
        x: np.ndarray,
        im_count: int,
    ) -> InputDto:
        """記述子とベクトル x を反映した ``InputDto`` を返す。

        記述子からのパラメータ反映（IM / ケーブル）と InputDto への差し込みを
        一括で行う。置換照合用のケーブルシリーズ名は ``input_dto.cable`` から
        導出する。

        Args:
            input_dto: 元の入力 DTO。
            descriptors: フィット記述子列（先頭が IM、続けてケーブル）。
            x: 各記述子に対応するフィット後の物理値ベクトル。
            im_count: 先頭の IM 部記述子の個数。

        Returns:
            InputDto: フィット結果を埋め込んだ入力 DTO。

        Raises:
            ValueError: 長さ・ケーブル有無・セクション数・シリーズ名の不整合、
                または im_series 未埋め込みのとき。
        """
        pass
