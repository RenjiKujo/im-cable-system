"""Forward 系（CartesianGrid / OperatingPoints 共通）InputDto 組み立て。

モードによる分岐は持たない。``reference_axes`` をコンストラクタ引数で
受け取り、その指定どおりに ``ArrayLayoutDto`` を構築する。

SI 正規化・各種 DTO ビルダーは ``assemble_input_dto.common`` 配下の
リーフを直 import して共通利用する（``docs/conventions/3_layering_and_imports.md``
の「同一責務ツリー内はリーフ直 import 可」に該当）。
アセンブラレベルでは他経路と完全分離しており、別経路アセンブラ
への委譲は行わない。
"""

from __future__ import annotations

from im_cable_system.engine.algorithm.input_algorithm.assemble_input_dto.common.array_layout_builder import (  # noqa: E501
    build_array_layout,
)
from im_cable_system.engine.algorithm.input_algorithm.assemble_input_dto.common.cable_dto_builder import (  # noqa: E501
    build_cable_dto,
)
from im_cable_system.engine.algorithm.input_algorithm.assemble_input_dto.common.im_dto_builder import (  # noqa: E501
    build_im_dto,
)
from im_cable_system.engine.algorithm.input_algorithm.assemble_input_dto.common.performance_curve_dto_builder import (  # noqa: E501
    build_im_performance_curve_catalogs,
)
from im_cable_system.engine.algorithm.input_algorithm.assemble_input_dto.common.si_normalizer import (  # noqa: E501
    to_si_input_dto,
)
from im_cable_system.engine.algorithm.input_algorithm.assemble_input_dto.i_input_dto_assembler import (  # noqa: E501
    IInputDtoAssembler,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data.data_class.forward_input_loaded_data import (  # noqa: E501
    ForwardInputLoadedData,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ArrayKey,
    CableDto,
    ImCableSystemName,
)
from im_cable_system.engine.shared.dto.input import (
    InputDto,
)


class ForwardInputDtoAssembler(
    IInputDtoAssembler[ForwardInputLoadedData],
):
    """ロード済み中間表現から Forward 用 InputDto を構築する。

    CartesianGrid / OperatingPoints のいずれも同一の組み立て経路を用いる。
    参照軸 (``reference_axes``) はコンストラクタで受け取り、本クラスは
    その指定どおりに ``ArrayLayoutDto`` を作る。モード分岐は持たない。
    """

    def __init__(
        self,
        config: IConfig,
        logger: ILogger,
        reference_axes: list[ArrayKey],
    ) -> None:
        """初期化する。

        Args:
            config: 設定。開発ガイドライン（``docs/conventions/``）の
                「``IConfig`` / ``ILogger`` は属性として保持する」ルールに従い保持する
                （本クラスの ``assemble`` 内では現状参照しない）。
            logger: ロガー。同上の理由で保持する。
            reference_axes: ``ArrayLayoutDto.reference_axes`` に渡す軸の
                順序付きリスト。CartesianGrid 用なら 3 軸全部、
                OperatingPoints 用なら ``SLIP`` のみ、のように
                呼び出し側（orchestrate 層）が決める。
        """
        self._config: IConfig = config
        self._logger: ILogger = logger
        self._reference_axes: list[ArrayKey] = list(reference_axes)

    @classmethod
    def create(
        cls,
        config: IConfig,
        logger: ILogger,
        reference_axes: list[ArrayKey],
    ) -> ForwardInputDtoAssembler:
        """参照軸を明示してインスタンスを生成する。

        ``reference_axes`` は呼び出し側（orchestrate 層）が決める。
        CartesianGrid モードなら ``[SLIP, INPUT_LINE_VOLTAGE, FREQUENCY]``、
        OperatingPoints モードなら ``[SLIP]``、というようにモードごとの
        分岐は本クラスより上位（orchestrate 層）に閉じている。

        Args:
            config: 設定。
            logger: ロガー。
            reference_axes: ``ArrayLayoutDto.reference_axes`` に渡す軸の
                順序付きリスト。

        Returns:
            ForwardInputDtoAssembler: 生成されたインスタンス。
        """
        return cls(
            config=config,
            logger=logger,
            reference_axes=list(reference_axes),
        )

    def assemble(
        self,
        loaded_data: ForwardInputLoadedData,
    ) -> InputDto:
        """ロード結果から InputDto を返す。

        最終段で :func:`to_si_input_dto` を通し、内部に保持する物理量 DTO
        の単位を SI 基本単位（V / A / W / Hz / Ω / H / m / rad/s / Nm 等）
        に揃える。下流の processor / pipeline は受け取った時点で SI 基本
        単位だと仮定してよい。

        Args:
            loaded_data: ローダーが返した中間表現。

        Returns:
            InputDto: 組み立て結果（SI 基本単位に正規化済み）。

        Raises:
            ValueError:
                アセンブラー由来のエラーとして、以下の場合に発生する。
                - IM / Cable のモデル名、結線種別、等価回路種別、極数、
                  かご段数などがサポート外の Enum 値である。
                - かご段数と二次枝の構造が整合しない
                  （単一かごに ``secondary`` が無い、二重かごに
                  ``secondary_inner`` / ``secondary_outer`` が無い等）。

                DTO 由来のエラーとして、以下の場合にも発生する。
                - ``ImPrimaryModelDto`` / ``ImExcitationModelDto`` /
                  ``ImSecondaryModelDto`` / ``CableConductorModelDto`` の
                  モデル係数名が必須集合と一致しない、係数名が重複する、
                  または係数値に NaN / inf が含まれる。
                - ``ImPerformanceCurveCatalogDto`` で、``power`` と
                  ``torque`` と ``rotational_speed`` がすべて揃った状態で
                  ``P = T·ω`` の要素ごと整合性を満たさない
                  （3 系列すべての要素が finite なインデックスのみ比較対象。
                  いずれかが NaN/inf の要素は検証対象外）。
                - ``Float*Dto`` / ``Array*Dto`` / ``ImPerformanceCurveCatalogDto``
                  などの ``__post_init__`` で、単位・値域・配列長・必須系列
                  の契約違反が検出される。
        """
        im_dto = build_im_dto(loaded_data.im)
        cable_dto: CableDto | None = None
        if loaded_data.cable is not None:
            cable_dto = build_cable_dto(loaded_data.cable)
        layout = build_array_layout(
            loaded_data.axes,
            reference_axes=self._reference_axes,
        )
        im_pc_catalogs = build_im_performance_curve_catalogs(
            curve_loaded=loaded_data.im_performance_curve,
        )
        assembled = InputDto(
            name=ImCableSystemName(base=loaded_data.im_cable_system_name),
            array_layout=layout,
            im=im_dto,
            cable=cable_dto,
            im_pc_catalogs=im_pc_catalogs,
        )
        return to_si_input_dto(assembled)
