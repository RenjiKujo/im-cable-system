# DTO設計原則

## 目的・スコープ

本ドキュメントは、im_cable_system における **入口（Input）→ 中間（Itm）→ 出口（Output）** の DTO ステージ構成と、各ステージの責務・命名規則を俯瞰することを目的とする。各 DTO のフィールド単位の契約は実装（dataclass の定義・docstring）を正とする。

- Processor 層・Algorithm 層の両方で参照される DTO を、ステージ別（Input / Itm / Output）に整理する。
- 新規モードの追加時や DTO 変更時は、本ドキュメントを実装と同期させて一貫性を保つ。

## ステージ別の責務（共通方針）

| ステージ | クラス | 責務 |
|----------|--------|------|
| **Input** | `InputDto` / `InputDtos` | 入口の契約（必須軸・参照軸の制約）を保持。モード別のサブクラスは作らず、`reference_axes` の指定でモードを切り替える。 |
| **Itm** | `ItmDto` / `ItmDtos` | **全モード共通**。モデル（build_model 結果）とシミュレーション結果（simulate 結果）を内包し、Output 変換の共通ソースとなる。 |
| **Output** | `OutputDto` / `OutputDtos` | **全モード同型**。入力原値とシミュレーション結果の生量を併せ持ち、図表・表はここから派生計算する。 |

- Input / Itm / Output いずれも単一のトップレベル DTO で 3 モード（`ForwardByCartesianGrid` / `EstimateParams` / `ForwardByOperatingPoints`）を表現する。
- **モードの決定**は実行エントリポイント／ジョブスペック（`forward_by_cartesian_grid.py` / `estimate_params.py` / `forward_by_operating_points.py`）が行う。
- `array_layout.reference_axes` は **DTO の形（出力の表示形）** を決める軸で、モード判別そのものではない。forward 系2モードの違いは `reference_axes` の選び方だけ（grid=`[SLIP, INPUT_LINE_VOLTAGE, FREQUENCY]` / 時系列=`[SLIP]`）。`EstimateParams` は grid と同じ参照軸になり得るため、`reference_axes` だけでは `ForwardByCartesianGrid` と区別できない。

## 共通前提

- **命名規則**: 単体の DTO クラスは `*Dto`、そのコレクションは `*Dtos`（`BaseEntityDto` 派生で `name` を識別属性とする）。
- **DTO 属性名**: Python フィールドは `snake_case`（例: `im_primary_current`, `array_layout`）。
- **不変性**: トップレベル DTO は `@dataclass(frozen=True)`。
- **Enum の命名**（`shared/dto/generic/im_cable_system` 配下の `array` / `im` / `cable` サブパッケージ）:
  - **Enum メンバー名**: 常に `UPPER_SNAKE_CASE`。
  - **Enum の値**は用途で次の二系統に分ける（無理に一種類に揃えない）。

    | 用途 | 値の形式 | 例 |
    |------|----------|-----|
    | 配列レイアウト・TSV 列・電流取得のキー | `lower_snake_case`（必要なら `attr.segment`） | `ArrayKey.SLIP` → `"slip"`、`CONDUCTOR_CURRENT_PIE_SINGLE` → `"conductor_current.pie_single"` |
    | モデル種別・カタログ `model.name`・ファクトリ分岐 | `UPPER_SNAKE` | `ImPrimaryModelType.BASIC` → `"BASIC"` |

  - **π ケーブル辞書キー**（`PieCableConductorKey` = `pie_single` / `PieCableGroundKey` = `pie_upstream`・`pie_downstream`）は配列用セグメントとして**小文字**。`ArrayKey` のドット付きキーと連結して使う。
  - **IM 専用の配列キー列挙は置かない**。二次側は `ItmImModelDto` の構造化属性 + 二次枝 `ImSecondaryCageBranchType`（`SINGLE` / `INNER` / `OUTER`）+ 配列契約 `ArrayKey` で表す（`PieCable*Key` だけが π 辞書専用）。
  - **識別子**（`ImCableSystemName` / `ImName` / `ImSeriesName` 等）は別枠（ジョブ名・系列名・個体名。軸名ルールとは独立）。
- **モデル DTO の `name`**: `ImPrimaryModelDto` 等は `Im*ModelType` / `ConductorModelType` の **Enum のみ**を保持する（`str` との union は取らない）。YAML・CSV からの文字列はカタログ読込・`parse_*` 等の境界で列挙に変換してから DTO に渡す。`get_name()` はカタログ互換の `UPPER_SNAKE` 文字列を返す。
- **参照軸の契約**: 独立入力（`SLIP` / `FREQUENCY` / `INPUT_LINE_VOLTAGE`）のみ `reference_axes` に置ける（`ArrayKey.reference_axes_members()`）。電流系は回路から決まる結果のため、参照軸には**含めない**。

## `name`（`ImCableSystemName`）の構造: 識別子と表示名の合成

`InputDto` / `ItmDto` / `OutputDto` はいずれも `name: ImCableSystemName` を
1 つだけ持つ。これは「1 つの対象に付いた 1 つの名前」ではなく、性質の異なる
2 つの識別（**測定対象**の識別と**計算ランの**識別）を 1 つの値オブジェクトに
合成したものである。

| 概念 | `ImCableSystemName` の属性 | 対応する対象 | 使ってよい場面 |
|------|------|------|----------------|
| 表示名 | `base`（`get_base()`） | 測定対象（例: 1 本の性能曲線）。1 run に 1 つ | 図タイトルなど、人が読む表示だけ |
| 識別子 | `discriminator` を含む `value`（`get_value()`） | 計算ラン（例: 1 つのモデル構造候補）。1 対象に対し複数あり得る | ファイル名、CSV 行識別子（`InputDtos`/`ItmDtos`/`OutputDtos` の `get_by_name`）、report キー |

EstimateParams は `model_candidate_axis` の直積展開により、1 つの性能曲線
（測定対象）から複数のモデル候補組み合わせ（計算ラン）を生成する
（**1 対象 : N ラン**）。`get_value()` は各ランを一意に区別する識別子として
候補インデックスを `discriminator` に含めるが、図タイトルにインデックスを
出すとカタログ名との対応が読み取りにくい。そこで `get_base()` が
候補インデックスを除いた表示名（測定対象の名前）を返し、表示側だけがこれを
参照する。forward は 1 対象 : 1 ラン（`discriminator = None`）に退化する
特殊ケースであり、このとき `get_value() == get_base()` になる。

- **`get_base()` の戻り値を識別子として使わない**。`InputDtos`/`ItmDtos`/
  `OutputDtos` の検索キー・出力ファイル名は常に `get_value()` を使う。
  同一 run 内で複数の候補が同じ `get_base()` を共有するため、これを
  ファイル名やコレクションの検索キーに使うと、`BaseEntityDto._get_from_list`
  が最初の一致を返すだけで重複を検出しないため、常に先頭の候補しか
  参照できなくなる。
- **`ImCableSystemName.value` を文字列分解して `discriminator` を導出しない**。
  候補インデックスの個数はモデル軸の追加で変わり得る（実例: 摩擦・風損／
  漂遊負荷損の軸追加で `value` の `_` 区切り要素数が 6→8 に変化した）。
  `discriminator` は呼び出し側（`estimate_params/loader.py` の `combo`）から
  直接組み立てる。`base` は EstimateParams・forward いずれも性能曲線名
  （`parsed.im_performance_curve_name` 相当）に由来し、`discriminator` と
  同じ `combo`／パース結果から独立に取得する（`value` から prefix を
  剥がして求めない）。両者が正しく組み合わさっていることは、テストの
  不変条件（`dto.name.get_value() == loaded_data.im_cable_system_name`）
  で固定している。
- **フィールドを 1 つに保つ**。`InputDto` に `name` と並べて別オブジェクトの
  兄弟フィールドを追加しない（両者は常にペアで構築・伝播され、独立に
  変わることがないため、分ける利点がない一方で「取り違えても型検査を
  通る」「片方だけ渡し忘れる」というリスクだけが残る）。
  `fitted_input_assembler.py` や `iteration_forward_execution_orchestrator.py`
  は推定・反復のたびに `InputDto` / `ItmDto` を作り直すが、`name` は 1 つの
  必須フィールドなので渡し忘れは basedpyright が全構築点で検出する。

## モード別の差分

| モード | Input | Itm | Output |
|--------|-------|-----|--------|
| **ForwardByCartesianGrid** | `InputDto`。参照軸 `[SLIP, INPUT_LINE_VOLTAGE, FREQUENCY]`（グリッド）。 | 共通。 | `OutputDto`。slip 軸グリッド表示。 |
| **EstimateParams** | `InputDto` + `im_pc_catalogs`（推定ターゲット）。 | 共通。完了時に `estimate_params_fit_summary` を付与。反復中は forward 結果を再利用。 | `OutputDto`。`estimate_params_fit_summary` あり。 |
| **ForwardByOperatingPoints** | `InputDto`。参照軸 `[SLIP]`（時系列）。 | 共通。 | `OutputDto`。index 時系列表示。 |

