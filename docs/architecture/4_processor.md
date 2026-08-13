# シミュレーションロジック設計 - Processorコンポーネントと処理フロー

## 概要

本ドキュメントは、本シミュレーションエンジンにおけるProcessorコンポーネント（`src/im_cable_system/engine/processor/`）の構成と設計方針、および処理フローを定義する。

Pipelineコンポーネント（`5_pipeline.md`）がパイプライン全体の組み立てとステージの実行順序制御を担うのに対し、
Processorコンポーネントは各ステージ（Input/Execute/Output）の具体的な処理と、その処理内で使用するAlgorithm/Domainの
呼び出しを担当する。全体のレイヤー構造および依存関係は `0_component.md` を参照する。

## Processorコンポーネントの役割

シミュレーションパイプラインの各ステージの処理を**呼び出し**として実装する。各ステージのインターフェイスは引数・戻り値ともに **Dtos** を想定する。

Processor層の主な責務は以下の通りとする。

- **Dtos の走査**: 入力 Dtos を走査し、各要素（単一 Dto）に対する処理を Algorithm 層に委譲する
- **結果の集約**: Algorithm 層から返された結果を集約して出力 Dtos を構築する
- **オーケストレーターの呼び出し**: 各要素（単一 Dto）ごとに Algorithm 層のオーケストレーターを 1 回呼び出す
- **処理順序の委譲**: モデル構築・シミュレーション実行・検証などの詳細な処理順序は Algorithm 層に閉じる

ステージ内の具体的な処理（モデル構築・シミュレーション実行・検証など）の実装は **Algorithm層の責務** であり、Algorithm層は引数・戻り値に **単一 Dto** を想定する。Processor層は Algorithm 層のオーケストレーターを呼び出し、Dtos の走査と結果の集約に専念する。詳細は `3_algorithm.md` を参照する。

## データフロー概要

Processor 層のステージは `JobSpec(s) → InputDtos → ItmDtos → OutputDtos` の順で Dtos を受け渡す。実行時入力はファイル専用 DTO ではなく、実行モードごとのジョブ仕様である。入力側の型は**モードで単数・複数が異なる**（forward 系: `ForwardJobSpecs` = 複数、EstimateParams: `EstimateParamsJobSpec` = 単数）。出力側（`InputDtos` 以降）は全モード共通で Dtos（複数）に統一される。

1. **Input Stage**: ジョブ仕様（forward 系は `ForwardJobSpecs`、EstimateParams は `EstimateParamsJobSpec`）から InputDtos を構築する。Processor 層はジョブ仕様の各要素ごとに Algorithm 層の入力オーケストレーターを呼び出し、結果を集約して InputDtos を構築する。
2. **Execute Stage**: InputDtos を受け取り、各 InputDto ごとに Algorithm 層の実行オーケストレーターを呼び出して ItmDtos を生成する。
3. **Output Stage**: ItmDtos を受け取り、各 ItmDto ごとに Algorithm 層の出力オーケストレーターを呼び出して OutputDtos を生成・出力する。

## 共通インターフェイス

### 引数・戻り値の方針

Processor層の各ステージインターフェイスでは、**引数・戻り値ともに Dtos** を想定する。ステージ間のデータ受け渡しはすべてDtosで統一し、Pipeline層と整合する。

### IStage

すべてのステージの共通インターフェイス。

- `create()`: ファクトリーメソッド（ステージインスタンス生成）
- `process(dtos) -> Dtos`: ステージ処理の実行（入出力はDtos）

各ステージの引数・戻り値は Dtos であり、層・ステージごとに次のように完全に定義される。InputStage の入力型のみモードで異なる（下記）。

- InputStage: `process(ForwardJobSpecs) -> InputDtos`（forward 系） / `process(EstimateParamsJobSpec) -> InputDtos`（EstimateParams）
- ExecuteStage: `process(InputDtos) -> ItmDtos`
- OutputStage: `process(ItmDtos) -> OutputDtos`

パイプラインは `create` 時に各ステージの `IStage.create` で Input / Execute / Output を組み立て、コンストラクタへ注入する。`run` は注入済みステージを順に実行するだけとする。

パイプラインからは **IStage のみ**が見える。各ステージ（Input/Execute/Output）はすべて `IStage` を実装し、
公開メソッドは `create` と `process(dtos)` のみとする。**現時点でステージ種別ごとの名目型（`IInputStage`, `IOutputStage` など）は未実装**であり、
各モードの具体クラス（例: `ForwardByCartesianGridInputStage`）が `IStage` を直接実装する。将来そうした名目型を
追加する場合も `IStage` を継承する設計とし、パイプラインは型としては `IStage` のみを参照する。
具体的なステージ実装の生成と実行は、Processor層のファクトリとパイプラインが制御する。

## 各ステージの役割

### InputStage

ジョブ仕様を受け取り、Algorithm 層の入力オーケストレーターを呼び出して InputDtos を構築・検証する。ジョブ仕様・入力 DTO の検証（`validate_job_spec` / `validate_input_dto`）も Algorithm 層に委譲する。

#### InputStage と IStage

InputStage の契約は `IStage[JobSpecT, InputDtos]` で表現する。`JobSpecT` は実行モードで異なり、**forward 系（CartesianGrid / OperatingPoints）は `ForwardJobSpecs`（複数）、EstimateParams は `EstimateParamsJobSpec`（単数）**を使う。EstimateParams は 1 つの統合ジョブ仕様から候補直積で複数 `InputDto` を生成するため、入力側は単数のままでよい（出力側の `InputDtos` は全モード共通）。引数・戻り値は Dtos（InputStage の入力のみ上記の例外）。
load / validate などは実装の内部（private）で `process(dtos)` から呼び、インターフェースには公開しない。

#### 処理フロー

**入力**:
- **JobSpecs**: 実行モードごとのジョブ仕様（ファイルパス・系列選択・推定設定などを含む）

**Processor層の役割**:
1. **走査**: ジョブ仕様の各要素を取り出す
2. **Algorithm層の呼び出し**: Algorithm 層の入力オーケストレーターを呼び出し、ジョブ仕様から `input_dto` を構築する
3. **結果の集約**: 生成された InputDto を集約して InputDtos を構築する

処理の詳細順序（データ読み込み→データ変換→データ検証）は Algorithm 層で定義・実装される。

**出力**:
- **InputDtos**: シミュレーション入力データ

### ExecuteStage

InputDtosを受け取り、各要素（単一 InputDto）ごとに Algorithm 層の実行オーケストレーターを呼び出してシミュレーション結果（ItmDtos）を生成する。**ステージ内の具体的な処理（モデル構築・シミュレーション実行・中間Dto検証）の実装はAlgorithm層の責務**であり、Processor層のExecuteStageは Algorithm 層の実行オーケストレーターの呼び出しと結果の集約に専念する。詳細は `3_algorithm.md` の「execute_algorithm における全体実行のオーケストレーション」を参照する。

#### ExecuteStage と IStage

ExecuteStage の契約は **IStage のみ**で表現する。型は `IStage[InputDtos, ItmDtos]`（ドメインにより具体型は異なる。
例: im_cable_system では `IStage[InputDtos, ItmDtos]`）。追加の公開メソッドは持たない。
`process(dtos)` で入力 Dtos を受け取り ItmDtos を返す。内部では、Dtos を走査し、各要素（単一 InputDto）ごとに Algorithm 層の実行オーケストレーターを呼び出し、結果を集約して ItmDtos を構築する。

#### 処理フロー（Processor層の責務）

**入力**:
- **InputDtos**: シミュレーション入力データ（Dtos）

**Processor層の役割**:
1. **Dtos の走査**: InputDtos を走査し、各要素（単一 InputDto）を取り出す
2. **Algorithm層の呼び出し**: 各 InputDto ごとに Algorithm 層の実行オーケストレーターを 1 回呼び出し、`input_dto` を渡して `itm_dto` を受け取る
3. **結果の集約**: 各 InputDto から生成された ItmDto を集約して ItmDtos を構築する

処理の詳細順序（モデル構築→シミュレーション実行→中間Dto検証）は Algorithm 層で定義・実装される。

#### 実行方式の差し替え

ExecuteStage は複数 DTO の処理方式を `IDataProcessingStrategy` に委譲する。Strategy は「入力列に処理関数を適用し、結果列を入力順で返す」ことだけを契約とし、Algorithm 層の計算内容には依存しない。

逐次実行、スレッド並列、プロセス並列の違いは Strategy に閉じ込める。これにより、worker 数や timeout、並列化方式を変更しても、ExecuteStage の外部契約と Algorithm 層の計算ロジックを変えずに済む。

Strategy のテストでは、入力順の保証、例外伝播、timeout や worker 数などの設定反映を確認する。Processor から Algorithm への統合テストでは、詳細な数値一致よりも `InputDtos -> ItmDtos` の件数・順序・例外なく完了することを重視する。

**出力**:
- **ItmDtos**: シミュレーション中間データ（Dtos）

### OutputStage

ItmDtosを受取り、各要素（単一 ItmDto）ごとに Algorithm 層の出力オーケストレーターを呼び出して用途に応じたOutputDtosを生成し、その結果の可視化・出力を実行する。引数・戻り値はDtosとする。

#### OutputStage と IStage

OutputStage の契約は `IStage[ItmDtos, OutputDtos]` で表現する。引数・戻り値は Dtos。
convert などは実装の内部（private）で `process(dtos)` から呼び、インターフェースには公開しない。
`process(dtos)` で入力 Dtos を受け取り OutputDtos を返す。内部では、Dtos を走査し、各要素（単一 ItmDto）ごとに Algorithm 層の出力オーケストレーターを呼び出し、結果を集約して OutputDtos を構築する。

#### 処理フロー

**入力**:
- **ItmDtos**: シミュレーション中間データ（Dtos）

**Processor層の役割**:
1. **Dtos の走査**: ItmDtos を走査し、各要素（単一 ItmDto）を取り出す
2. **Algorithm層の呼び出し**: 各 ItmDto ごとに Algorithm 層の出力オーケストレーターを 1 回呼び出し、`itm_dto` を渡して `output_dto` を受け取る
3. **結果の集約**: 各 ItmDto から生成された OutputDto を集約して OutputDtos を構築する

処理の詳細順序（変換 → 図表・表・レポート生成 → エクスポート → OutputDto へのアセンブル）は Algorithm 層で定義・実装される。

**出力**:
- **OutputDtos**: シミュレーション出力データ
- **可視化結果**: グラフ、テーブル、レポート
- **エクスポートファイル**: シミュレーション結果ファイル

## その他の責務

- 各ステージ間のDtosを介したデータ受け渡し
- ステージ固有のエラーハンドリング

### パッケージ構成（Processor層）

```text
src/im_cable_system/engine/processor/
├── i_stage.py
├── input_stage/
├── execute_stage/
└── output_stage/
```

**インポート**: [`docs/conventions/3_layering_and_imports.md`](../conventions/3_layering_and_imports.md) を参照する。

## 依存関係

Processorコンポーネントは以下のコンポーネントに依存する：

- **algorithm**: algorithmのインターフェイスに依存（Strategy Pattern）
- **domain**: domainのインターフェイスに依存（判定処理、計算ロジック、検証ルールの取得）
- **shared**: sharedのDtos、ユーティリティ、設定に依存

詳細な依存関係については、`0_component.md`の「コンポーネントの依存関係」セクションを参照してください。
