"""estimate_params 系（統合 TSV）ファイルローダー。

1 ジョブ（:class:`EstimateParamsJobSpec`）= 1 つの統合 TSV。本ローダーは、
統合 TSV と :class:`IConfig` 経由の探索境界 YAML から、候補モデル軸の直積
要素ごとに :class:`EstimateParamsInputLoadedData` を 1 件ずつ構築し、その
タプルを返す。engine 層 DTO は構築せず、``assemble_input_dto`` 層に委ねる。
``raise`` するのは :class:`EstimateParamsInputLoadedData` を作れないケース
のみで、値レベルの検証は DTO ``__post_init__`` と ``_validate_input_dto``
に寄せる
（:class:`...load_data.i_data_loader.IInputDataLoader` の契約に従う）。

直積展開の for ループを本ローダーに閉じる理由:
    候補軸    （``im_primary`` / ``im_excitation`` /
    ``im_secondary(single|double_inner|double_outer)`` /
    ``cable_conductor``）や ``cable_length`` ・ single/double cage の
    どちらを生成するかは統合 TSV をパースしないと分からない。よって
    直積展開は Loader が担い、Orchestrator には
    ``tuple[EstimateParamsInputLoadedData, ...]`` を返す。
    Orchestrator 側で直積を組もうとすると、本ローダーの内部手順
    （parse → bounds load → axes/perf 構築 → iter_combos → build one）を
    Orchestrator に漏らす必要があり、責務が濁るため避ける。Orchestrator
    以降は LoadedData / InputDto 集合に対する単純な for（Assembler /
    Validator への 1 件ずつのディスパッチ）のみを担う。
"""

from __future__ import annotations

from im_cable_system.engine.algorithm.input_algorithm.load_data.data_class.estimate_params_input_loaded_data import (  # noqa: E501
    EstimateParamsInputLoadedData,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data.estimate_params.axes_builder import (  # noqa: E501
    build_axes_loaded_data_from_performance_curve,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data.estimate_params.bounds_yaml_parser import (  # noqa: E501
    load_cable_parameter_fit_descriptor_bounds,
    load_im_parameter_fit_descriptor_bounds,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data.estimate_params.cable_loaded_data_builder import (  # noqa: E501
    build_cable_loaded_data,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data.estimate_params.cartesian_product import (  # noqa: E501
    EstimateParamsModelCombo,
    iter_model_combos,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data.estimate_params.fixed_section_helpers import (  # noqa: E501
    fixed_required_int,
    resolve_cable_length,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data.estimate_params.im_loaded_data_builder import (  # noqa: E501
    build_im_loaded_data,
    build_nameplate,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data.estimate_params.performance_curve_loaded_data_builder import (  # noqa: E501
    build_im_performance_curve_loaded_data,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data.estimate_params.unified_input_parser import (  # noqa: E501
    parse_unified_estimate_params_csv,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data.i_data_loader import (  # noqa: E501
    IInputDataLoader,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.job_spec.estimate_params import (
    EstimateParamsJobSpec,
)


class EstimateParamsLoader(
    IInputDataLoader[
        EstimateParamsJobSpec,
        tuple[EstimateParamsInputLoadedData, ...],
    ],
):
    """estimate_params 系（統合 TSV）ローダー。

    1 ジョブ分の :class:`EstimateParamsJobSpec` を受け、統合 TSV と Config
    経由の IM / Cable 探索境界 YAML を読み込み、候補軸の直積要素ごとに
    :class:`EstimateParamsInputLoadedData` を構築して tuple で返す。engine
    層 DTO は構築せず、``assemble_input_dto`` 層に委ねる。raise するのは
    :class:`EstimateParamsInputLoadedData` を作れないケースのみで、値レベル
    の検証は DTO ``__post_init__`` と ``_validate_input_dto`` に寄せる。
    """

    def __init__(self, config: IConfig, logger: ILogger) -> None:
        """初期化する。

        Args:
            config: 探索境界 YAML パスを解決する設定。
            logger: ロガー。開発ガイドライン（``docs/conventions/``）の
                「``IConfig`` / ``ILogger`` は属性として保持する」ルールに従い保持する
                （本クラスの ``load`` 内では現状参照しない）。
        """
        self._config: IConfig = config
        self._logger: ILogger = logger

    @classmethod
    def create(
        cls,
        config: IConfig,
        logger: ILogger,
    ) -> EstimateParamsLoader:
        """ローダーを生成する。"""
        return cls(config=config, logger=logger)

    def load(
        self,
        input_data: EstimateParamsJobSpec,
    ) -> tuple[EstimateParamsInputLoadedData, ...]:
        """統合 TSV と探索境界 YAML から直積展開済み LoadedData タプルを返す。

        読み込み対象は次のファイルである。

        - ``input_data.input_tsv_path``: 統合 TSV
          （``unified_input_parser`` でセクション分割）。
        - Config の ``get_im_bounds_and_init_file_path()``:
          IM 探索境界 YAML（``bounds_yaml_parser``）。
        - Config の ``get_cable_bounds_and_init_file_path()``:
          ケーブル探索境界 YAML（``bounds_yaml_parser``）。

        ここで扱う例外は、ファイル読み取りと入力ファイル構造の破綻
        （:class:`EstimateParamsInputLoadedData` を作れないケース）に限る。
        ロード後の意味的整合性は DTO ``__post_init__`` および
        オーケストレーターの ``_validate_input_dto`` で検証する。

        Args:
            input_data: 1 ジョブ分のパス束（:class:`EstimateParamsJobSpec`）。

        Returns:
            tuple[EstimateParamsInputLoadedData, ...]: 直積要素数分の
            中間表現。各要素は :attr:`im_cable_system_name` / :attr:`im` /
            :attr:`cable` / :attr:`axes` / :attr:`im_performance_curve` を
            含む。

        Raises:
            ValueError: 下記いずれかの形式・スキーマ違反を検出した場合。
                メッセージは違反個所を特定できる粒度で組み立てる
                （ファイルパスや該当キー名を含める）。

                統合 TSV
                    （:mod:`unified_input_parser`）

                    - 1 行目が空、または先頭セルが
                      ``im_performance_curve_name`` 以外。
                    - ``im_performance_curve_name`` の値セルが空。
                    - ``nameplate`` ヘッダ行（``nameplate,value,unit``）
                      が無い、または 2 回以上現れる。
                    - ``supply`` ヘッダ行（``supply,value,unit``）が無い、
                      または 2 回以上現れる。
                    - ``fixed_model_key`` ヘッダ行が無い。
                    - ``model_candidate_axis`` ヘッダ行が無い。
                    - ``model_candidate_axis`` に既知ラベル以外の行が
                      混じる。
                    - ``model_candidate_axis`` で同一ラベルが 2 行以上
                      現れる。``im_secondary(single)`` /
                      ``im_secondary(double_inner)`` /
                      ``im_secondary(double_outer)`` は **独立した軸** と
                      して保持されるため、それぞれの重複はエラー
                      となる。
                    - 必須軸 ``im_primary`` / ``im_excitation`` が
                      空。
                    - 二次軸が ``im_secondary(single)`` も
                      ``im_secondary(double_inner) と
                      im_secondary(double_outer) の両方`` も指定されて
                      いない。
                    - ``im_secondary(double_inner)`` と
                      ``im_secondary(double_outer)`` の片方だけが
                      指定されている（二重かごは両軸の指定が必要）。
                    - 性能曲線テーブルの ``rotational_speed`` ヘッダ行が
                      見つからない。
                    - 性能曲線テーブルの単位行が無い。

                fixed_model_key
                    （:mod:`fixed_section_helpers`）

                    - 必須キー ``im_poles`` / ``im_circuit_type`` /
                      ``im_connection_type`` のいずれかが欠落。
                    - ``im_poles`` が ``int()`` で変換できない。
                    - ``cable_length`` 指定がありつつ ``float()`` で
                      変換できない（未指定は許容、ケーブル無し扱い）。
                    - ``cable_length`` が負値
                      （``<= 0`` は ``build_cable_loaded_data`` で
                      「ケーブル無し」に丸められる挙動だが、負値だと
                      silent failure になるため Loader 層で raise する）。

                nameplate / supply
                    （:mod:`im_loaded_data_builder` /
                    :mod:`performance_curve_loaded_data_builder`）

                    - ``nameplate`` に ``input_line_voltage`` /
                      ``input_line_current`` / ``output_power`` /
                      ``frequency`` のいずれかが無い。
                    - ``supply`` に ``frequency`` / ``voltage`` の
                      いずれかが無い。

                性能曲線テーブル
                    （:mod:`performance_curve_loaded_data_builder`）

                    - 必須列 ``rotational_speed`` が欠落。
                    - ``power`` / ``current`` / ``power_factor`` /
                      ``efficiency`` / ``torque`` のいずれの観測列も無い。
                    - 曲線ヘッダで ``rotational_speed`` /
                      ``power`` / ``current`` / ``power_factor`` /
                      ``efficiency`` / ``torque`` のいずれかの列が
                      重複している。
                    - ``rotational_speed`` セルが空（独立軸として
                      未観測点は許容しない）。
                    - データ行の値セルが ``float()`` で数値に変換
                      できない（観測列の **空セル** は ``np.nan`` と
                      して保持し ``ValueError`` にしない。NaN→0 変換と
                      mask 抽出は ``assemble_input_dto`` 段で行う）。

                探索境界 YAML
                    （:mod:`bounds_yaml_parser`）

                    - YAML のルートがマッピングでない。
                    - :meth:`ImParameterFitDescriptorBounds.from_estimation_document`
                      / :meth:`CableParameterFitDescriptorBounds.from_estimation_document`
                      側のスキーマ違反
                      （各 ``ParameterFitDescriptorBounds`` 仕様参照）。

                値レベルの検証（空配列、有限性、値域、``poles`` の正整数性、
                単位文字列の妥当性、配列長一致など）は LoadData では行わず、
                ``assemble_input_dto`` 段の DTO ``__post_init__`` および
                ``_validate_input_dto`` に寄せる。
            FileNotFoundError: 統合 TSV、または Config から解決した境界
                YAML のいずれかが存在しない場合。
            OSError: 権限不足やエンコーディング不一致など、上記以外の
                ファイル I/O エラーが発生した場合。
        """
        parsed = parse_unified_estimate_params_csv(
            input_data.input_tsv_path.resolve(),
        )
        im_bounds = load_im_parameter_fit_descriptor_bounds(
            self._config.get_im_bounds_and_init_file_path(),
        )
        cable_bounds = load_cable_parameter_fit_descriptor_bounds(
            self._config.get_cable_bounds_and_init_file_path(),
        )

        nameplate = build_nameplate(parsed)
        poles = fixed_required_int(parsed, "im_poles")
        perf_curve = build_im_performance_curve_loaded_data(parsed, poles=poles)
        axes = build_axes_loaded_data_from_performance_curve(perf_curve)
        cable_length, cable_length_unit = resolve_cable_length(parsed)
        # cable_length が指定されていても導体候補が空、または候補軸が
        # ``NONE`` のみのときは、``cartesian_product`` 側でケーブル無し扱い
        # （``combo.cable_conductor is None``）になる。
        include_cable = (
            cable_length > 0.0 and len(parsed.candidate_cable_conductor) > 0
        )

        built: list[EstimateParamsInputLoadedData] = []
        for combo in iter_model_combos(parsed, include_cable=include_cable):
            system_name = _build_system_name(
                perf_curve_name=parsed.im_performance_curve_name,
                combo=combo,
            )
            name_discriminator = _build_name_discriminator(combo)
            im_name = _build_im_name(combo)
            cable_name = _build_cable_name(combo)
            im_loaded = build_im_loaded_data(
                parsed=parsed,
                combo=combo,
                bounds=im_bounds,
                nameplate=nameplate,
                im_name=im_name,
            )
            cable_loaded = build_cable_loaded_data(
                combo=combo,
                cable_length=cable_length,
                cable_length_unit=cable_length_unit,
                bounds=cable_bounds,
                cable_name=cable_name,
                section_name=f"{cable_name}_section_0",
            )
            built.append(
                EstimateParamsInputLoadedData(
                    im_cable_system_name=system_name,
                    name_discriminator=name_discriminator,
                    im=im_loaded,
                    cable=cable_loaded,
                    axes=axes,
                    im_performance_curve=perf_curve,
                ),
            )
        return tuple(built)


def _build_system_name(
    *,
    perf_curve_name: str,
    combo: EstimateParamsModelCombo,
) -> str:
    """``ImCableSystemName`` 用文字列を組み立てる。

    形式: ``{perf}_{p}_{e}_{ss}_{sdo}_{sdi}_{fw}_{sl}_{c}``。
    IM 軸（``fw`` / ``sl`` 含む）をまとめ、ケーブルを末尾に置く既存の組み立て順に
    従う。採用しない軸は ``0``（``fw`` / ``sl`` は必ず採用されるため常に ``1`` 以上）。
    """
    return f"{perf_curve_name}_{_build_name_discriminator(combo)}"


def _build_name_discriminator(combo: EstimateParamsModelCombo) -> str:
    """``ImCableSystemName.discriminator`` 用文字列を組み立てる。

    形式: ``{p}_{e}_{ss}_{sdo}_{sdi}_{fw}_{sl}_{c}``（``_build_system_name`` から
    ``perf_curve_name`` プレフィックスを除いたもの）。``im_cable_system_name``
    を文字列分解して求めるのではなく、同じ ``combo`` から並行して組み立てる。
    """
    return (
        f"{combo.primary_index}"
        f"_{combo.excitation_index}"
        f"_{combo.secondary_single_index}"
        f"_{combo.secondary_double_outer_index}"
        f"_{combo.secondary_double_inner_index}"
        f"_{combo.friction_windage_index}"
        f"_{combo.stray_load_index}"
        f"_{combo.cable_conductor_index}"
    )


def _build_im_name(combo: EstimateParamsModelCombo) -> str:
    """``ImSeriesName`` 用文字列を組み立てる。

    形式: ``IM_{p}_{e}_{ss}_{sdo}_{sdi}_{fw}_{sl}``。採用しない軸は ``0``
    （``fw`` / ``sl`` は必ず採用されるため常に ``1`` 以上）。
    """
    return (
        f"IM"
        f"_{combo.primary_index}"
        f"_{combo.excitation_index}"
        f"_{combo.secondary_single_index}"
        f"_{combo.secondary_double_outer_index}"
        f"_{combo.secondary_double_inner_index}"
        f"_{combo.friction_windage_index}"
        f"_{combo.stray_load_index}"
    )


def _build_cable_name(combo: EstimateParamsModelCombo) -> str:
    """``CableSeriesName`` 用文字列を組み立てる。

    形式: ``Cable_{c}``。ケーブル無しのときは ``Cable_0``。
    """
    return f"Cable_{combo.cable_conductor_index}"
