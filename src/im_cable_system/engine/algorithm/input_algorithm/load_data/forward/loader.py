"""Forward 系（CartesianGrid / OperatingPoints 共通）ファイルローダー。

``ForwardJobSpec`` と ``IConfig`` の各パスからファイルを読み込み、
``ForwardInputLoadedData`` を構築する。モードによる分岐は持たない。
CartesianGrid / OperatingPoints の意味の違い（直積 / co-indexed）は
``assemble_input_dto`` 段の ``reference_axes`` 指定で表現される。
"""

from __future__ import annotations

from im_cable_system.engine.algorithm.input_algorithm.load_data.data_class.forward_input_loaded_data import (  # noqa: E501
    ForwardInputLoadedData,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data.forward.axes_parser import (  # noqa: E501
    parse_axes,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data.forward.cable_catalog_parser import (  # noqa: E501
    parse_cable_from_catalog,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data.forward.im_catalog_parser import (  # noqa: E501
    parse_im_from_catalog,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data.forward.performance_curve_parser import (  # noqa: E501
    parse_performance_curve_optional,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data.forward.series_selection_parser import (  # noqa: E501
    parse_series_selection,
)
from im_cable_system.engine.algorithm.input_algorithm.load_data.i_data_loader import (  # noqa: E501
    IInputDataLoader,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.job_spec.forward import (
    ForwardJobSpec,
)


class ForwardLoader(
    IInputDataLoader[
        ForwardJobSpec,
        ForwardInputLoadedData,
    ],
):
    """Forward 系（CartesianGrid / OperatingPoints 共通）ローダー。

    1 ジョブ分の ``ForwardJobSpec`` を受け、軸 TSV / シリーズ選択 TSV /
    IM 性能曲線 TSV と Config 経由のカタログ YAML を読み込み、
    ``ForwardInputLoadedData`` を返す。engine 層 DTO は
    構築せず、``assemble_input_dto`` 層に委ねる。raise するのは
    ``ForwardInputLoadedData`` を作れないケースのみで、値レベルの
    検証は DTO ``__post_init__`` と ``_validate_input_dto`` に寄せる。
    """

    def __init__(self, config: IConfig, logger: ILogger) -> None:
        """初期化する。

        Args:
            config: カタログ YAML パスなどを解決する設定。
            logger: ロガー。開発ガイドライン（``docs/rules/``）の
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
    ) -> ForwardLoader:
        """ローダーを生成する。"""
        return cls(config=config, logger=logger)

    def load(
        self,
        input_data: ForwardJobSpec,
    ) -> ForwardInputLoadedData:
        """spec の各パスからファイルを読み込み、中間表現を返す。

        読み込み対象は次のファイルである。

        - ``series_selection_path``: シリーズ選択 TSV。
        - ``axes_path``: 評価点軸 TSV。
        - Config の ``get_im_series_catalog_file_path()``:
          IM カタログ YAML。
        - Config の ``get_cable_series_catalog_file_path()``:
          ケーブルカタログ YAML。
        - ``performance_curve_path``: IM 性能曲線 TSV。``None`` の場合は
          読み込みをスキップし、戻り値の ``im_performance_curve`` も
          ``None`` になる。

        ここで扱う例外は、ファイルの読み取りと入力ファイル構造の破綻
        （``ForwardInputLoadedData`` が作れないケース）に限る。
        ロード後の意味的整合性は、DTO ``__post_init__`` および
        オーケストレーターの ``_validate_input_dto`` で検証する。

        Args:
            input_data: 1 ジョブ分のパス束（``ForwardJobSpec``）。

        Returns:
            ForwardInputLoadedData: パース済み中間表現。
            ``im_cable_system_name`` / ``im`` / ``cable`` / ``axes`` と、
            optional の ``im_performance_curve`` を含む。

        Raises:
            ValueError: 下記いずれかの形式・スキーマ違反を検出した場合。
                メッセージは違反個所を特定できる粒度で組み立てる
                （ファイルパスや該当キー名を含める）。

                シリーズ選択 TSV
                    （:mod:`series_selection_parser`）

                    - ファイル構造:

                        - ``im_series_name`` というキーで始まるテーブル
                          ヘッダ行がファイル中に 1 つも見つからない。
                        - ``im_series_name`` で始まるテーブルヘッダ行が
                          2 つ以上ある（テーブルは 1 つだけを想定する）。
                        - ヘッダ行のあと、単位行・データ行が揃わず
                          ``header + 2`` 行未満で終わっている。

                    - 必須列・必須キー:

                        - テーブルヘッダに ``im_series_name`` /
                          ``cable_series_name`` /
                          ``cable_conductor_model`` のいずれかが無い。
                        - テーブルヘッダに ``cable_length`` が無い。
                        - テーブルヘッダで上記 4 列の必須列のいずれかが
                          重複している。
                        - メタブロックに ``im_cable_system_name``
                          が無い、もしくは値が空。

                    - データ行の意味的不整合:

                        - ``im_series_name`` セルが 2 行以上に
                          指定されている（同一値・別値を問わず）。
                        - ``im_series_name`` セルが 1 行も埋まらず
                          シリーズ名が確定できない。
                        - 同一行内で ``cable_series_name`` と
                          ``cable_length`` の片方のみ埋まっている。
                        - ``cable_length`` セルが ``float()`` で
                          数値に変換できない。
                        - ``cable_conductor_model`` セルが 2 行
                          以上に指定されている（束につき 1 つ）。
                        - ケーブル区間が 1 つ以上あるのに
                          ``cable_conductor_model`` が空のまま。
                        - ケーブル区間が無いのに
                          ``cable_conductor_model`` が指定された。

                    なお、ケーブル長単位セルは LoadData 段では
                    ``axes_parser`` と同じく ``strip()`` のみで保持し、
                    角括弧 ``[...]`` 表記の剥がしや表記揺れの吸収
                    （``feet``→``ft`` 等）、空セル時の既定 ``ft`` 補完
                    のいずれも行わず、ここでは ``ValueError`` を
                    投げない。``[m]``/``[furlong]``/空文字列なども
                    そのまま ``SeriesSelectionCableRow.length_unit``
                    に乗る。角括弧剥がしは ``assemble_input_dto`` 段の
                    ``forward.unit_normalizer.normalize_loaded_unit_cell``
                    が、値域妥当性は ``FloatLengthDto.__post_init__`` および
                    ``_validate_input_dto`` がそれぞれ担う。

                軸 TSV
                    （:mod:`axes_parser`）

                    - ヘッダ行・単位行・データ行のいずれかが
                      不足し、ファイル全体で 3 行未満になっている。
                    - ヘッダに ``slip`` / ``frequency`` /
                      ``input_line_voltage`` の必須 3 列のいずれかが
                      欠落 / 重複している。
                    - 非空のデータ行の幅が必須 3 列を満たさない
                      （空行は黙ってスキップするが、部分的に埋まった
                      短い行はエラーとして扱う）。
                    - 必須列のセルが ``float()`` で数値に変換できない。

                IM カタログ YAML
                    （:mod:`im_catalog_parser` / :mod:`yaml_utils`）

                    - YAML ルートがマッピングでない
                      （ファイル先頭がスカラ／配列、または空など）。
                    - ルートに ``im_series`` リストが無い。
                    - ``im_series`` リスト中に非マッピングの要素が
                      混じっている（空 entry ``- `` 等）。
                    - ``im_series`` リスト中の entry に ``name`` キーが
                      無い、または ``name`` が空文字列。
                    - ``im_series`` リスト中で同じ ``name`` が
                      2 回以上現れる（重複）。
                    - シリーズ選択で指定した ``im_series_name`` が
                      ``im_series`` リスト中の ``name`` に
                      一致しない。
                    - シリーズエントリに ``poles`` /
                      ``connection_type`` / ``circuit_type`` /
                      ``nameplate`` / ``primary`` / ``excitation``
                      のいずれかが欠落。
                    - ``nameplate`` ブロックに ``voltage`` /
                      ``current`` / ``power`` / ``frequency`` の
                      いずれかが欠落、または ``{value, unit}`` の
                      片方が無い。
                    - ``primary`` / ``excitation`` / ``secondary*``
                      ブロックに ``model`` / ``resistance`` /
                      ``inductance`` のいずれかが欠落、または
                      ``{value, unit}`` の片方が無い。
                    - シリーズエントリの ``cage_multiplicity`` が
                      ``DOUBLE_CAGE`` のとき ``secondary_inner`` /
                      ``secondary_outer`` のどちらかが欠落。
                    - 上記以外のとき ``secondary`` 自体が欠落、
                      またはマッピングでない。
                    - ``model`` ブロックに ``name`` が無い。
                    - ``model.params`` がリストでない、各要素が
                      マッピングでない、または ``name`` / ``value``
                      が欠落。

                ケーブルカタログ YAML
                    （:mod:`cable_catalog_parser` / :mod:`yaml_utils`）

                    シリーズ選択にケーブル区間がある場合のみ参照する
                    （区間 0 のときは catalog を開かない）。

                    - YAML ルートがマッピングでない。
                    - ルートに ``cable_series`` リストが無い。
                    - ``cable_series`` リスト中に非マッピングの要素が
                      混じっている（空 entry ``- `` 等）。
                    - ``cable_series`` リスト中の entry に ``name``
                      キーが無い、または ``name`` が空文字列。
                    - ``cable_series`` リスト中で同じ ``name`` が
                      2 回以上現れる（重複）。
                    - シリーズ選択で参照した
                      ``cable_series_name`` が ``cable_series`` リスト
                      中の ``name`` に一致しない。
                    - ``cable_series`` の entry に ``shape_type`` /
                      ``conductor`` / ``ground`` のいずれかが欠落。
                    - ``conductor`` / ``ground`` ブロックの必須キー
                      （``resistance_per_length`` /
                      ``inductance_per_length`` /
                      ``resistance_length`` /
                      ``capacitance_per_length``）のいずれかが欠落、
                      または ``{value, unit}`` の片方が無い。
                    - ルートに ``cable_conductor_models`` マッピングが
                      無い、または対象プロファイルキーが
                      ``cable_conductor_models`` に存在しない。
                    - ``cable_conductor_models`` の対象 entry に
                      ``name`` が無い、または ``params`` の各要素に
                      ``name`` / ``value`` が無い。
                    - ``cable_conductor_model_profile`` が解決時点で
                      ``None`` ／空文字（シリーズ選択側の異常を
                      ケーブルカタログパース時に検知した場合）。

                IM 性能曲線 TSV
                    （:mod:`performance_curve_parser`、
                    ``performance_curve_path`` が ``None`` の場合は
                    全件スキップ）

                    - メタブロック:

                        - 1 行目が空、または先頭セルが
                          ``im_performance_curve_name`` 以外。
                        - ``im_performance_curve_name`` の値セルが空。
                        - 2 行目（メタ表ヘッダ）が
                          ``name,value,unit`` で始まらない。
                        - メタ表の各行が ``name,value,unit`` の 3 列
                          に満たない。
                        - メタ表の ``name`` セルが空。
                        - メタ表の同じ ``name`` キーが 2 回以上現れる
                          （重複、``im_performance_curve_name`` との
                          衝突も含む）。
                        - メタ表の直後に区切りの空行が無い。
                        - メタ表に ``poles`` / ``supply_frequency`` /
                          ``supply_voltage`` のいずれかが欠落。
                        - メタ表の ``value`` セルが ``float()`` で
                          数値に変換できない。

                    - 曲線テーブル:

                        - メタ表のあとに曲線ヘッダ行が無い。
                        - 曲線ヘッダの直後に単位行が無い。
                        - 曲線ヘッダに ``rotational_speed`` 列が欠落。
                        - 曲線ヘッダに ``power`` / ``current`` /
                          ``power_factor`` / ``efficiency`` /
                          ``torque`` のいずれも無い（``rotational_speed``
                          以外に少なくとも 1 本の従属列が必要）。
                        - 曲線ヘッダで ``rotational_speed`` /
                          ``power`` / ``current`` / ``power_factor`` /
                          ``efficiency`` / ``torque`` のいずれかが
                          重複している。
                        - データ行の値セルが ``float()`` で数値に
                          変換できない（観測列の **空セル** は
                          ``np.nan`` として保持し ``ValueError`` には
                          しない。``torque`` 列も同様に空セル → NaN
                          を許容する。NaN→0 変換と mask 抽出は
                          ``assemble_input_dto`` 段で行う）。

                        欠落していてもエラーにならない列
                        （``power`` / ``current`` / ``power_factor`` /
                        ``efficiency`` / ``torque``）は、
                        ``ImPerformanceCurveLoadedData`` の対応
                        フィールドが ``None`` になる。``torque`` 列だけが
                        ある場合は ``assemble_input_dto`` 段で
                        ``power_w = T·ω`` として機械出力を逆算し、
                        ``ImPerformanceCurveCatalogDto.power_series`` に
                        詰める。

                値レベルの検証（空配列、有限性、値域、``poles`` の
                正整数性、単位文字列の妥当性、配列長一致など）は
                LoadData では行わず、``assemble_input_dto`` 段の DTO
                ``__post_init__`` および ``_validate_input_dto`` に
                寄せる。
            FileNotFoundError: ``series_selection_path`` / ``axes_path`` /
                Config から解決したカタログ YAML パス、および ``None``
                でない ``performance_curve_path`` のいずれかが存在しない
                場合。
            OSError: 権限不足やエンコーディング不一致など、上記以外の
                ファイル I/O エラーが発生した場合。
        """
        spec = input_data
        axes = parse_axes(spec.axes_path)
        selection = parse_series_selection(spec.series_selection_path)
        im_catalog_path = self._config.get_im_series_catalog_file_path()
        cable_catalog_path = self._config.get_cable_series_catalog_file_path()
        im_loaded = parse_im_from_catalog(
            catalog_path=im_catalog_path,
            series_name=selection.table.im_series_name,
        )
        cable_loaded = parse_cable_from_catalog(
            catalog_path=cable_catalog_path,
            cable_rows=selection.table.cable_rows,
            cable_bundle_label=selection.meta.cable_bundle_label,
            conductor_model_profile=selection.table.cable_conductor_model_profile,
        )
        im_performance_curve = parse_performance_curve_optional(
            path=spec.performance_curve_path,
        )
        return ForwardInputLoadedData(
            im_cable_system_name=selection.meta.im_cable_system_name,
            im=im_loaded,
            cable=cable_loaded,
            axes=axes,
            im_performance_curve=im_performance_curve,
        )
