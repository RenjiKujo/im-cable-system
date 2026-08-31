# シミュレーションロジック設計 - Algorithm層設計方針

> **この文書が正本である範囲**: Algorithm 層のフォルダ構成・ステージ内データフローの契約（各ステージの引数と戻り値）・オーケストレーター方式。
>
> **正本ではない（参照先）**: 設計原則一般（インターフェース・ファクトリー・生成の分離）は [`conventions/2_design_principles.md`](../conventions/2_design_principles.md)、各ステージの詳細は [`algorithm/`](./algorithm/) サブツリー、import 規約は [`conventions/3_layering_and_imports.md`](../conventions/3_layering_and_imports.md)。

## 概要

本ドキュメントは、本シミュレーションエンジンにおけるAlgorithm層（`src/im_cable_system/engine/algorithm/`）の構成と設計方針を定義する。
Algorithm層は、シミュレーションエンジンにおける具体的な計算処理・モデル実行等のコアロジックを実装する。

シミュレーション層固有のDTO設計方針については、`1_shared.md`を参照してください。
Domain層の設計方針については、`2_domain.md`を参照してください。

## Algorithm層の設計原則

### 一貫性の原則

- 同じレベルのアルゴリズムクラスは同じ設計原則に従う
- アルゴリズム横断で共通利用される処理は一貫した命名規則と構造を持つ

### 責務分離の原則

- **`input_algorithm/`**: Inputステージ用アルゴリズム（データ処理、データ検証、データ変換）
- **`execute_algorithm/`**: Executeステージ用アルゴリズム（シミュレーションモデル実行）
- **`output_algorithm/`**: Outputステージ用アルゴリズム（可視化、結果エクスポート、レポート生成、後段で用いるデータをまとめた OutputDto の生成（アセンブル））

### 各ステージにおけるデータの受け渡し（ステージ内データフロー）

シミュレーション共通の**ステージ内データフロー**を定義する重要な契約である。**Execute / Output ステージ**は、複数 DTO の分配・集約を Processor 層が担うため、Algorithm 層では**単一 DTO の入力・単一 DTO の出力**のみを扱う。一方**Input ステージ**は、ジョブ仕様から `InputDto` を構築する起点であり、実行モードによっては**複数の `InputDto`（`InputDtos`）を生成する**。各ステージの引数・戻り値は次のとおりであり、実装のインターフェース（各オーケストレーターの親IF）もこの受け渡しに従う。

- **Inputステージ（input_algorithm）**
  - 入出力: ジョブ仕様 1 本 → 出力 `InputDto` / `InputDtos`。実行モードにより生成件数が変わる（**forward**: 単一 `InputDto`、**estimate_params**: 候補の直積に対応する複数 `InputDto`（`InputDtos`））。
  - 契約: 共通親IF `IInputAlgorithmsOrchestrator` の `build_input_dto(input_data) -> InputDtoT`。インスタンス生成（`create`）はモードごとに必要引数が異なる（Forward は `reference_axes` が必要、EstimateParams は不要）ため共通IFには置かず、per-mode IF 側で定義する（LSP 違反を避けるため）。
  - 内部フロー: `_validate_job_spec`（ロード前の軽量チェック）→ `_load_data`（`LoadedDataT` 構築）→ `_assemble_input_dto`（`InputDtoT` 構築）→ `_validate_input_dto`（DTO 横断の整合検証）の順で実行。詳細は [`algorithm/input/`](./algorithm/input/0_overview.md) を参照。
- **Executeステージ（execute_algorithm）**
  - 入出力: 入力 **InputDto** 1 本 → 出力 **ItmDto** 1 本。
  - 契約: 全体実行オーケストレーターの `execute(input_dto) -> ItmDto`。
  - 内部フロー: build_model（InputDto → ItmDto）→ simulate（ItmDto → ItmDto）→ validate_itm_dto（ItmDto）の順で実行。
- **Outputステージ（output_algorithm）**
  - 入出力: 入力 **ItmDto** 1 本 → 出力 **OutputDto** 1 本。
  - 契約: 共通IF `IOutputOrchestrator` の `run(itm_dto) -> OutputDto`。実装はモード別（`orchestrate/` 配下の 3 クラス）。
  - 内部フロー: 変換（convert）→ 図・表・レポート生成（make_figure / make_table / make_report）→ 保存・表示（export_* / display_figure）。図・表・レポートは**ファイルへの side effect** として出力し、戻り値の `OutputDto` には載せない。詳細は [`algorithm/output/`](./algorithm/output/0_overview.md) を参照。

### 拡張性の原則

- 新しいモデル・アルゴリズムは Factory の分岐追加と実装クラスの追加で吸収し、
  上位層（Processor / Pipeline）は無改修とする（Open-Closed 原則）
- アルゴリズムの実装状況に応じて段階的に統合可能

### 依存関係の原則

- Algorithm層はDomain層とShared層にのみ依存する
- Algorithm層内部のサブディレクトリ間での依存は許可されるが、循環依存は禁止

## Algorithm層のフォルダ管理方針

Algorithm層は、責務と利用者ごとにフォルダを分割する。**「どのステージの、どのシミュレーションタイプのアルゴリズムか」が一目で分かる単位**で分割する。

### トップレベルAlgorithm構造

```
src/im_cable_system/engine/algorithm/
├── input_algorithm/
│   ├── i_input_algorithms_orchestrator.py
│   ├── load_data/            … 読み込み・パース
│   ├── assemble_input_dto/   … InputDto 組み立て
│   ├── validate_job_spec/    … ジョブ仕様検証
│   ├── validate_input_dto/   … 入力 DTO 検証
│   └── orchestrate/          … モード別オーケストレーター
├── execute_algorithm/
│   ├── i_execute_algorithms_orchestrator.py
│   ├── build_model/          … InputDto → ItmDto（モデル構築）
│   ├── simulate/             … ItmDto → ItmDto（電圧電流・電力・特性値）
│   ├── validate_itm_dto/     … 中間 DTO 検証
│   └── orchestrate/          … モード別（forward / estimate_params）
└── output_algorithm/
    ├── i_output_orchestrator.py
    ├── convert/ make_figure/ make_table/ make_report/
    ├── export_figure/ export_table/ export_report/ display_figure/
    └── orchestrate/          … モード別オーケストレーター
```

ステージ（Input / Execute / Output）で大きく分割し、各ステージ内はオーケストレーターのインターフェース（親IF）と `orchestrate/` のモード別実装でフローを規定する。各ステージの詳細なデータフロー・コンポーネントは [`algorithm/`](./algorithm/) のサブツリーを参照する。

### パッケージ運用（Algorithm層）

- 実装モジュールがあるディレクトリには `__init__.py` を置く（責務の docstring、必要なら公開窓口）。
- Processor 等の外部から呼ぶ入口は、主に各 `orchestrate/__init__.py` およびステージ用 I/F モジュールとする。

**インポート・パッケージ運用**: [`docs/conventions/3_layering_and_imports.md`](../conventions/3_layering_and_imports.md) を参照する。

## Algorithm層の実装原則

### インターフェースと実装の分離

Algorithm層のクラスは、インターフェースと実装を分離する設計方針に従う。

- **インターフェース**: `I*` で始まる名前（例: `IImModelBuilder`）
- **実装クラス**: インターフェースを実装するクラス（例: `SingleCageImModelBuilder`）

### ファクトリーメソッドによるインスタンス生成

Algorithm層のクラスは、実装の選択（分岐）がある場合にファクトリーメソッド（`create()`）によりインスタンスを生成する。分岐がなければ必須ではない。

引数の粒度は設計原則（[`docs/conventions/2_design_principles.md`](../conventions/2_design_principles.md) の「生成はファクトリーに集約する」）に従う。分岐が単純なときは列挙・フラグなどを明示するのが第一選択。分岐が複雑、またはオーケストレーターでの取り出し重複を避けるため、DTO（または必要なサブグラフのみ）を渡してファクトリー内で分岐条件を導出してもよい。その場合は docstring で分岐根拠を明記し、分岐組合せを単体テストでカバーする。

```python
class IImModelBuilder(ABC):
    @classmethod
    @abstractmethod
    def create(
        cls, config: IConfig, logger: ILogger
    ) -> IImModelBuilder:
        pass

class SingleCageImModelBuilder(IImModelBuilder):
    @classmethod
    def create(
        cls, config: IConfig, logger: ILogger
    ) -> IImModelBuilder:
        return cls(config=config, logger=logger)
```

### オーケストレーターによる処理統括

Algorithm層では、各処理ステップの実行を司る**オーケストレーター**を存在させることで、プロセッサー側で細かく処理の順番を規定しなくて良いようにする。

- **オーケストレーター**: 複数の処理ステップを統括し、処理の順序を管理するクラス
- **メリット**: プロセッサー層はオーケストレーターを呼び出すだけで、詳細な処理順序を意識する必要がない
- **Pipeline/Processorとの関係**: Pipelineはステージの組み立てと順序制御を行い、Processorは各ステージで適切なオーケストレーターを選択して呼び出す。オーケストレーター内部でDomain・Sharedを利用した具体的な計算ロジックを実行する。

**オーケストレーターの例**:
各計算（電圧電流・電力・特性値など）ごとに専用のインターフェース（例: `IPowerCalculationOrchestrator`, `ICharacteristicsCalculationOrchestrator`）を定義し、実装クラスがそれを実装する。各オーケストレーターの具体的な処理順序・コンポーネントは [`algorithm/execute/`](./algorithm/execute/0_overview.md) を参照する。
