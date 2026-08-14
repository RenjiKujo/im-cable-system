"""Forward 系（CartesianGrid / OperatingPoints 共通）InputDto バリデータ。"""

from __future__ import annotations

from im_cable_system.engine.algorithm.input_algorithm.validate_input_dto.common.array_layout_checks import (  # noqa: E501
    check_line_voltage_real_constraints,
)
from im_cable_system.engine.algorithm.input_algorithm.validate_input_dto.common.cable_checks import (  # noqa: E501
    check_cable_section_lengths,
)
from im_cable_system.engine.algorithm.input_algorithm.validate_input_dto.common.grid_size_checks import (  # noqa: E501
    check_reference_axes_grid_size,
)
from im_cable_system.engine.algorithm.input_algorithm.validate_input_dto.common.im_checks import (  # noqa: E501
    check_im_values,
)
from im_cable_system.engine.algorithm.input_algorithm.validate_input_dto.common.si_execute_input_contract import (  # noqa: E501
    validate_array_layout_reference_axes_si_base_or_raise,
    validate_cable_section_lengths_si_base_or_raise,
    validate_cable_series_si_base_or_raise,
    validate_im_pc_catalogs_channels_si_base_or_raise,
    validate_im_series_si_base_or_raise,
)
from im_cable_system.engine.algorithm.input_algorithm.validate_input_dto.i_input_dto_validator import (  # noqa: E501
    IInputDtoValidator,
)
from im_cable_system.engine.shared.config import IConfig, ILogger, timer
from im_cable_system.engine.shared.dto.input import (
    InputDto,
)


class ForwardInputDtoValidator(IInputDtoValidator):
    """Forward 系（CartesianGrid / OperatingPoints 共通）InputDto バリデータ。

    モード分岐を持たず、``ArrayLayoutDto.reference_axes`` 軸の直積点数を
    含むすべてのチェックを ``reference_axes`` に従って一様に行う。
    SI 単位 / cross-field / grid size など経路非依存の検査は
    ``common/`` 配下のチェック関数を共通利用する。アセンブラ同様、
    Validator レベルでも他経路への委譲は行わない。

    検査の順序:

    1. 参照軸配列の SI 基本単位整合
    2. 線間電圧の実数制約（実部非負・虚部ゼロ。両経路共通）
    3. ``im.im_series`` の SI 基本単位整合と名板正値契約
    4. 性能カタログ（存在時）の SI 単位契約
    5. ケーブル（存在時）のシリーズ SI 単位・セクション長 SI / 正値
    6. ``reference_axes`` 直積グリッド点数の上限
    """

    def __init__(
        self,
        config: IConfig,
        logger: ILogger,
        max_reference_axes_grid_points: int,
    ) -> None:
        """初期化する。

        Args:
            config: 設定。開発ガイドライン（``docs/conventions/``）の
                「``IConfig`` / ``ILogger`` は属性として保持する」ルールに従い保持する。
            logger: ロガー。``@timer`` デコレータ（``logger=None``）が
                ``self._logger`` を参照するためにも用いる。
            max_reference_axes_grid_points: ``reference_axes`` 直積点数の上限。
                ``create`` で
                ``IConfig.input_validation_config.max_reference_axes_grid_points``
                から取り出す。
        """
        self._config: IConfig = config
        self._logger: ILogger = logger
        self._max_reference_axes_grid_points: int = (
            max_reference_axes_grid_points
        )

    @classmethod
    def create(
        cls,
        config: IConfig,
        logger: ILogger,
    ) -> ForwardInputDtoValidator:
        """バリデータを生成する。"""
        return cls(
            config=config,
            logger=logger,
            max_reference_axes_grid_points=(
                config.input_validation_config.max_reference_axes_grid_points
            ),
        )

    @timer(logger=None, line="#", min_duration=0.01)
    def validate(self, input_dto: InputDto) -> None:
        """組み立て後の InputDto を検証する。

        Args:
            input_dto: 検証対象。

        Raises:
            ValueError: いずれかの検査に失敗した場合。
        """
        validate_array_layout_reference_axes_si_base_or_raise(input_dto)
        check_line_voltage_real_constraints(input_dto)
        validate_im_series_si_base_or_raise(input_dto.im)
        check_im_values(input_dto)
        if len(input_dto.im_pc_catalogs) > 0:
            validate_im_pc_catalogs_channels_si_base_or_raise(
                input_dto.im_pc_catalogs
            )
        if input_dto.cable is not None:
            for section in input_dto.cable.sections.get_all():
                validate_cable_series_si_base_or_raise(section.series)
            validate_cable_section_lengths_si_base_or_raise(input_dto)
            check_cable_section_lengths(input_dto)
        check_reference_axes_grid_size(
            input_dto,
            max_grid_points=self._max_reference_axes_grid_points,
        )
