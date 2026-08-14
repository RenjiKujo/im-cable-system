"""estimate_params 用 InputDto バリデータ。

``common/`` 配下の経路非依存チェック一式を通したうえで、
EstimateParams 固有のチェック（性能曲線カタログが空でないこと）を
末尾に追加する。具象 Validator 同士の委譲は行わず、共有する検査関数を
``common/`` に集約する。

検査の順序は経路間で揃え、

1. 参照軸配列の SI 基本単位整合
2. 線間電圧の実数制約（実部非負・虚部ゼロ）
3. ``im.im_series`` の SI 基本単位整合と名板正値契約
4. 性能カタログ（存在時）の SI 単位契約
5. ケーブル（存在時）のセクション数が 1・シリーズ SI 単位・
   セクション長 SI / 正値
6. ``reference_axes`` 直積グリッド点数の上限
7. **EstimateParams 固有**: 性能カタログが 1 件以上存在すること

EstimateParams 固有のケーブル契約:
    パラメータフィットでは「ケーブル無し」または「1 区間ケーブル」のみを
    想定する（:mod:`...execute_algorithm.orchestrate.estimate_params`
    の入力リゾルバと同じ前提）。``cable`` が存在する場合はセクション数を
    1 に限定し、0 個・複数個はいずれも ``ValueError`` とする。
"""

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
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ImPerformanceCurveCatalogDtos,
)
from im_cable_system.engine.shared.dto.input import (
    InputDto,
)


def _validate_im_pc_catalogs_non_empty_or_raise(
    im_pc_catalogs: ImPerformanceCurveCatalogDtos,
) -> None:
    """パラメータ推定では参照曲線が必須。"""
    if len(im_pc_catalogs) < 1:
        raise ValueError(
            "estimate_params: im_pc_catalogs には1件以上の性能曲線カタログが必要です。"
        )


def _validate_single_cable_section_or_raise(input_dto: InputDto) -> None:
    """ケーブルがある場合、セクション数は 1 に限る。

    パラメータフィットは 1 区間ケーブルのみを想定するため、``cable`` が
    存在するならセクション数を 1 に固定する。``cable`` が ``None`` の場合は
    何もしない。

    Args:
        input_dto: 検証対象 InputDto。

    Raises:
        ValueError: ``cable`` が存在し、かつセクション数が 1 以外の場合。
    """
    cable = input_dto.cable
    if cable is None:
        return
    section_count = len(cable.sections.get_all())
    if section_count != 1:
        raise ValueError(
            "estimate_params: ケーブルがある場合のセクション数は 1 に"
            f"限りますが、{section_count} 個が指定されました。"
        )


class EstimateParamsInputDtoValidator(IInputDtoValidator):
    """estimate_params 経路用・組み立て後 InputDto バリデータ。

    ``common/`` 配下の経路非依存チェック一式を通したうえで、
    EstimateParams 固有の「性能曲線カタログが空でないこと」を末尾に
    追加する。検査順序・内容は Forward 経路と揃えるが、具象 Validator
    同士の委譲は行わない。
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
            max_reference_axes_grid_points: ``reference_axes`` 直積点数
                の上限。``create`` で
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
    ) -> EstimateParamsInputDtoValidator:
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
        """組み立て済み :class:`InputDto` を検証する。

        Args:
            input_dto: オーケストレーターが組み立てた入力 DTO。

        Raises:
            ValueError: いずれかの検査に失敗した場合。
                EstimateParams 固有の失敗条件として、性能曲線カタログが
                空のとき、およびケーブルがあるのにセクション数が 1 以外
                （0 個・複数個）のとき raise する。それ以外の検査内容
                （SI 単位、cross-field、grid size）は経路非依存の
                ``common/`` チェックに従う。
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
            _validate_single_cable_section_or_raise(input_dto)
            for section in input_dto.cable.sections.get_all():
                validate_cable_series_si_base_or_raise(section.series)
            validate_cable_section_lengths_si_base_or_raise(input_dto)
            check_cable_section_lengths(input_dto)
        check_reference_axes_grid_size(
            input_dto,
            max_grid_points=self._max_reference_axes_grid_points,
        )
        _validate_im_pc_catalogs_non_empty_or_raise(input_dto.im_pc_catalogs)
