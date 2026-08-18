"""estimate_params 用 InputDto 組み立て。

EstimateParams の InputStage では :class:`EstimateParamsInputLoadedData`
を 1 件受け取り、対応する :class:`InputDto` を 1 件返す。本クラスは
EstimateParams 経路の組み立てを自己完結で行い、他経路アセンブラへの
委譲は行わない（読者の混乱を避けるため、アセンブラレベルでは経路を
完全分離する方針）。

1. 性能曲線の比率単位列（``power[-]`` / ``current[%]``）を、同じ統合
   TSV に併載されている名盤値で **絶対単位** に変換
   （:func:`convert_ratio_columns_to_absolute`）。
2. ``assemble_input_dto.common`` 配下の各ビルダーを直接呼び出し、
   ``InputDto`` の各構成要素（``ImDto`` / ``CableDto`` / ``ArrayLayoutDto``
   / ``ImPerformanceCurveCatalogDtos``）を組み立てる。
3. 上記を組み合わせて :class:`InputDto` を構築し、最終段で
   :func:`to_si_input_dto` を通して SI 基本単位に揃える。

``reference_axes`` は EstimateParams 固定の
``[SLIP, FREQUENCY, INPUT_LINE_VOLTAGE]`` を内部で指定する。

ratio→absolute 変換を本クラスに置く理由:
    共通の性能曲線ビルダー
    （``assemble_input_dto.common.performance_curve_dto_builder``）は
    **絶対単位前提・比率単位拒否** で設計されている。EstimateParams の
    統合 TSV では名盤と観測曲線が同じファイルに併載され、比率単位での
    入力が許容されるため、共通ビルダーに渡す直前で名盤値を用いた
    ratio→absolute 変換を行う。ビルダー側に flag を増やすより責務分離
    が明確になる。

経路間の共有粒度（設計方針）:
    アセンブラ自体は経路ごとに完全分離するが、内部で利用する各
    ステップ機能（``build_im_dto`` / ``build_cable_dto`` /
    ``build_array_layout`` / ``build_im_performance_curve_catalogs`` /
    ``to_si_input_dto``）は ``assemble_input_dto.common`` 配下に置き、
    両経路で共有する。
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
from im_cable_system.engine.algorithm.input_algorithm.assemble_input_dto.estimate_params.perf_curve_unit_converter import (  # noqa: E501
    convert_ratio_columns_to_absolute,
)
from im_cable_system.engine.algorithm.input_algorithm.assemble_input_dto.i_input_dto_assembler import (  # noqa: E501
    IInputDtoAssembler,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data.data_class.estimate_params_input_loaded_data import (  # noqa: E501
    EstimateParamsInputLoadedData,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data.data_class.im_performance_curve_loaded_data import (  # noqa: E501
    ImPerformanceCurveLoadedData,
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

_REFERENCE_AXES: list[ArrayKey] = [
    ArrayKey.SLIP,
    ArrayKey.FREQUENCY,
    ArrayKey.INPUT_LINE_VOLTAGE,
]


def _ratio_to_absolute(
    loaded_data: EstimateParamsInputLoadedData,
) -> ImPerformanceCurveLoadedData:
    """性能曲線の比率列を絶対単位に変換した中間表現を返す。

    EstimateParams の統合 TSV は名盤と観測曲線が併載されているため、
    ``power[-]`` / ``current[%]`` が許容される。共通の性能曲線ビルダー
    は絶対単位前提のため、ビルダー呼び出し前に必ず本変換を通す。
    """
    return convert_ratio_columns_to_absolute(
        loaded_data.im_performance_curve,
        loaded_data.im.nameplate,
    )


class EstimateParamsAssembler(
    IInputDtoAssembler[EstimateParamsInputLoadedData],
):
    """1 件の中間表現から 1 件の :class:`InputDto` を組み立てる。

    直積展開（複数 LoadedData → 複数 InputDto）はオーケストレーターが担う。
    本クラスは「LoadedData 1 件 → InputDto 1 件」の純な変換だけを行う。
    各ステップ機能（``ImDto`` / ``CableDto`` / ``ArrayLayoutDto`` /
    ``ImPerformanceCurveCatalogDtos`` のビルダー、SI 正規化）は
    ``assemble_input_dto.common`` 配下のリーフを共通利用する。
    アセンブラレベルでは他経路と完全分離しており、別経路アセンブラ
    への委譲は行わない。
    """

    def __init__(
        self,
        config: IConfig,
        logger: ILogger,
    ) -> None:
        """初期化する。

        Args:
            config: 設定。開発ガイドライン（``docs/conventions/``）の
                「``IConfig`` / ``ILogger`` は属性として保持する」ルールに従い保持する
                （本クラスの ``assemble`` 内では現状参照しない）。
            logger: ロガー。同上の理由で保持する。
        """
        self._config: IConfig = config
        self._logger: ILogger = logger
        self._reference_axes: list[ArrayKey] = list(_REFERENCE_AXES)

    @classmethod
    def create(
        cls,
        config: IConfig,
        logger: ILogger,
    ) -> EstimateParamsAssembler:
        """インスタンスを生成する。

        ``reference_axes`` は EstimateParams 固定で
        ``[SLIP, FREQUENCY, INPUT_LINE_VOLTAGE]`` を内部で指定する。
        """
        return cls(config=config, logger=logger)

    def assemble(
        self,
        loaded_data: EstimateParamsInputLoadedData,
    ) -> InputDto:
        """1 件の :class:`EstimateParamsInputLoadedData` から InputDto を返す。

        手順:

        1. 性能曲線の比率列を絶対単位に変換。
        2. 共通ビルダーで ``ImDto`` / ``CableDto`` / ``ArrayLayoutDto`` /
           ``ImPerformanceCurveCatalogDtos`` を構築。
        3. :class:`InputDto` を組み立て、:func:`to_si_input_dto` で SI 基本
           単位に揃える。

        Args:
            loaded_data: ローダーが構築した中間表現（候補組み合わせ 1 件分）。

        Returns:
            InputDto: SI 基本単位に正規化済みの組み立て結果。

        Raises:
            ValueError:
                EstimateParams 固有のエラーとして、以下の場合に発生する。
                - 性能曲線の ratio→absolute 変換時、名盤の ``power_unit`` /
                  ``current_unit`` が ``ACTIVE_POWER_FACTORS`` /
                  ``CURRENT_FACTORS`` に登録されていないサポート外単位
                  である（:func:`convert_ratio_columns_to_absolute`）。

                共通ビルダー由来のエラーとして、以下の場合にも発生する。
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
        absolute_pc = _ratio_to_absolute(loaded_data)
        im_dto = build_im_dto(loaded_data.im)
        cable_dto: CableDto | None = None
        if loaded_data.cable is not None:
            cable_dto = build_cable_dto(loaded_data.cable)
        layout = build_array_layout(
            loaded_data.axes,
            reference_axes=self._reference_axes,
        )
        im_pc_catalogs = build_im_performance_curve_catalogs(
            curve_loaded=absolute_pc,
        )
        assembled = InputDto(
            name=ImCableSystemName(
                base=loaded_data.im_performance_curve.name,
                discriminator=loaded_data.name_discriminator,
            ),
            array_layout=layout,
            im=im_dto,
            cable=cable_dto,
            im_pc_catalogs=im_pc_catalogs,
        )
        return to_si_input_dto(assembled)
