"""組み立て後 InputDto バリデーションの契約。

4 段フローの 4 段目 ``_validate_input_dto`` で使われる契約。
具象は :meth:`create` でインスタンスを生成し、:meth:`validate` で
組み立て済みの :class:`InputDto` を検証する。

検査の責務分担:
    パス存在等の事前検査は :mod:`...validate_job_spec`、
    ``LoadedData`` が作れないケースの raise は ``load_data`` 層、
    ``InputDto`` が作れないケースの raise は ``assemble_input_dto``
    層と各 DTO の ``__post_init__`` に分離している。
    ここでは **InputDto 化後でないと判定できない** 事柄（DTO 構造の
    整合、SI 単位、cross-field 整合、参照軸直積サイズ、経路固有の
    必須データ有無など）のみを対象とする。

Note:
    各経路の具象バリデータの ``create`` は ``config`` と ``logger`` のみで
    足りる。Forward 系では CartesianGrid / OperatingPoints の差を
    ``InputDto.array_layout.reference_axes`` から自動判別できるため
    実行モードごとに具象を分けず 1 クラスで両モードを賄い、
    EstimateParams 系も追加パラメータを必要としない。
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.input import (
    InputDto,
)


class IInputDtoValidator(ABC):
    """組み立て後の :class:`InputDto` を検証する契約。"""

    @classmethod
    @abstractmethod
    def create(
        cls,
        config: IConfig,
        logger: ILogger,
    ) -> IInputDtoValidator:
        """バリデータインスタンスを生成する。

        Args:
            config: 設定。
            logger: ロガー。

        Returns:
            IInputDtoValidator: 生成されたバリデータ。
        """
        raise NotImplementedError

    @abstractmethod
    def validate(self, input_dto: InputDto) -> None:
        """入力 DTO を検証する。

        Args:
            input_dto: 検証対象。

        Raises:
            ValueError: 検証に失敗した場合。
        """
        raise NotImplementedError
