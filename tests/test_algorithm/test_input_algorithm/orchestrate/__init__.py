"""Input オーケストレーターのテスト窓口。

現状はパイプラインごとに happy path（valid な spec を渡し、
``build_input_dto`` が ``InputDto`` を返すこと）の smoke テストのみ。

TODO:
    本ディレクトリに **error cases**（不備ありインプットを各段で弾く検証）を
    追加する。現在の happy path だけでは「動線が通ること」しか担保できておらず、
    4 段フロー（``_validate_job_spec`` → ``_load_data`` →
    ``_assemble_input_dto`` → ``_validate_input_dto``）のバリデーション設計が
    機能していることを証明できていない。

    追加方針:
        - ファイル分離: パイプラインごとに
          ``test_<pipeline>_orchestrator_errors.py`` を本ディレクトリ配下の
          各サブディレクトリに新設する。
        - 1 ケース = 1 関数。関数名で「どの段で何を弾くか」を表現する
          （例: ``test_validate_job_spec_rejects_missing_series_selection_path``）。
        - ``pytest.raises(ValueError, match=...)`` で日本語メッセージのキー部分
          まで仕様化する。
        - 不備データは既存ファイルを書き換えず、必ず ``tmp_path`` に
          valid フィクスチャを書き出し、1 箇所だけ壊すヘルパーを通す。
        - ``parametrize`` は最初は控え、メッセージが case ごとに違うことを
          担保しやすい 1 関数 1 ケースで始める。

    各オーケストレーターでカバーすべきケース（最低限）:

    forward_by_cartesian_grid:
        - ``_validate_job_spec``: 各 path が存在しない / ディレクトリを指している。
        - ``_load_data``: 性能曲線 TSV から ``poles`` 行を削除、曲線ヘッダから
          ``rotational_speed`` を欠落、単位行が空セル、メタブロックの後に
          空行が無い、など各 parser のキーエラーパス（``LoadedData`` が
          作れないケース）。
        - ``_assemble_input_dto`` / DTO ``__post_init__``: 参照軸配列の
          非有限要素、空配列、長さ 0（``__post_init__`` で弾く）。
        - ``_validate_input_dto``: SI 単位整合、性能曲線 cross-DTO 整合、
          定格 vs supply 乖離 warning。

    forward_by_operating_points:
        - ``_validate_job_spec``: 同上。
        - ``_load_data``: ``operating_points`` TSV の列名違い、単位行欠落、
          数値非変換セル。
        - ``_validate_input_dto``: ``slip`` / ``frequency`` /
          ``input_line_voltage`` の長さ不一致。

    estimate_params:
        - ``_validate_job_spec``: 各 YAML / TSV パスが存在しない。
        - ``_load_data``: 1 行目が ``im_performance_curve_name`` 以外、
          ``fixed_model_key`` セクション欠落、``model_candidate_axis``
          で必須軸（``im_primary`` / ``im_excitation`` /
          ``im_secondary``）の候補が全部空、性能曲線ヘッダ欠落、
          境界 YAML が dict ではない、など。
        - ``_assemble_input_dto`` 前段の候補モデル組合せ解決:
          成分数違い・整数化失敗・範囲外インデックス・
          必須軸 0、ケーブル長>0 で cable_idx=0 の組合せ。
          これは resolver 単体テストを別途切る方が責務が綺麗。
        - ``_validate_input_dto``: 参照軸電圧 < 0、性能曲線 cross-DTO 整合、
          グリッド点数上限超過、ケーブルセクション長下限割れ、
          定格 vs supply 乖離 warning。

    なお、各層単体での error テスト（``validate_job_spec/`` /
    ``validate_input_dto/`` 配下や、将来必要なら ``load_data/`` 配下の
    parser 単体）は本ディレクトリの error テストとは独立に置いてよい。
    ただし「ユーザー視点で弾けることの担保」は本ディレクトリの
    orchestrator error テストを正とする。
"""
