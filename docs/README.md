# 設計ドキュメント

## このドキュメント集について

誘導電動機（IM）＋ケーブル系シミュレーション／パラメータ推定エンジンの
**設計意図・前提条件**と、**等価回路モデルの数式と実装の対応**を明文化したもの。
クラス単位の処理詳細はコードに委ね、設計判断の理由・前提・拡張方針や、
理論（数式）と設定・実装のひも付けなど、コードだけでは追いにくい情報を中心に記述する。

## 全体像

本エンジンは、IM・ケーブルの電気回路モデルに基づき、電圧・電流・電力・特性値
（回転速度・トルク・効率など）を計算し、メーカー性能曲線への当てはめ
（パラメータ推定）も行う。実装は次のレイヤー構造（上位 → 下位への一方向依存）を採る。

```text
pipeline → processor → algorithm → domain → shared
```

各層の責務・依存先の一覧と、ディレクトリ構成との対応は
[architecture/0_component.md](./architecture/0_component.md) が正本。
依存方向と import の規約そのものは
[conventions/3_layering_and_imports.md](./conventions/3_layering_and_imports.md) にある。

## ドキュメント構成

```text
docs/
├── architecture/   … engine の層別設計
├── apps/           … engine 外側のクライアント層（ジョブ投入型 Web 面など）
├── conventions/    … 開発規約
└── model/          … 等価回路（構成・計算の流れ・数式・当てはめ）
```

### 等価回路モデル

入口: [model/README.md](./model/README.md)

- [構成と読む順](./model/README.md)
- [計算の流れ](./model/calculation.md)
- [数式 ↔ YAML キー ↔ 実装](./model/equations/index.md)
- [メーカー性能曲線との整合性](./model/curve_fitting_consistency.md)

### アーキテクチャ（このリポジトリ固有の設計）

- [アーキテクチャ（層別設計）](./architecture/) — `pipeline / processor / algorithm / domain / shared` の層別設計。詳細を要する Algorithm 層・Shared 層は配下にサブツリーを持つ。
  - [0_component.md](./architecture/0_component.md): コンポーネント構成・依存方向・ディレクトリ構成・Mermaid 表記ルール
  - [1_shared.md](./architecture/1_shared.md): Shared 層・DTO 設計方針・命名規則（詳細: [`shared/`](./architecture/shared/)）
  - [2_domain.md](./architecture/2_domain.md): Domain 層（物理法則・共通計算・検証）
  - [3_algorithm.md](./architecture/3_algorithm.md): Algorithm 層（オーケストレーター・Strategy/Factory）（詳細: [`algorithm/`](./architecture/algorithm/)）
  - [4_processor.md](./architecture/4_processor.md): Processor 層・ステージ処理フロー
  - [5_pipeline.md](./architecture/5_pipeline.md): Pipeline 層・実行管理

#### 詳細設計（厚い層）

- Algorithm 層: [input](./architecture/algorithm/input/0_overview.md) / [execute](./architecture/algorithm/execute/0_overview.md) / [output](./architecture/algorithm/output/0_overview.md)
- Shared 層: [DTO 設計方針](./architecture/shared/dto_principle.md) / [config パッケージ（設定・ロガー・@timer）](./architecture/shared/config_and_logger.md)

### 開発規約（プロジェクト横断）

- [開発規約](./conventions/) — 特定プロジェクトに限定されない設計・実装の取り決めを、抽象度で 3 層に整理したもの。**`ruff` / `pyright` の設定とドキュメントの役割分担（正本マップ）も[ここ](./conventions/README.md)にある。**
  - 層 1（表記）: [1_code_style.md](./conventions/1_code_style.md)
  - 層 2（設計原則）: [2_design_principles.md](./conventions/2_design_principles.md)
  - 層 3（横断概念）: [3_layering_and_imports.md](./conventions/3_layering_and_imports.md) / [4_numerical_robustness.md](./conventions/4_numerical_robustness.md) / [5_testing.md](./conventions/5_testing.md)

### apps（engine 外側のクライアント層）

- [apps/web — ジョブ投入型 Web 面](./apps/web/0_overview.md) — FastAPI + Streamlit + SQLAlchemy。`architecture/` が正本とする engine 5 層の対象外（`runner/` と同格の外側クライアント）。

## 新規開発時の参考順序

1. 上の「全体像」と [architecture/0_component.md](./architecture/0_component.md) でレイヤー構成を把握
2. [conventions/](./conventions/) で守るべき規約を確認（初回は README の正本マップから）
3. [model/](./model/README.md) で等価回路を把握し、該当スコープの [architecture/](./architecture/) を確認して実装

## ドキュメント更新時の注意

- アーキテクチャ変更時は関連ドキュメントを更新する
- クラス単位の処理詳細はコードに委ね、設計前提・判断理由や数式↔実装の対応を記載する
- 依存関係の変更は必ずドキュメントへ反映する
- `ruff.toml` / `pyproject.toml` で機械強制できる値をドキュメントへ再掲しない（[正本マップ](./conventions/README.md)を参照させる）
- **実装状況（未実装・未定・「現時点では対象外」等）を書かない。** 設計判断は陳腐化しないが、
  実装状況は数週間で古くなり、更新を強制する仕組みもないため放置されやすい
  （実例: [algorithm/output/](./architecture/algorithm/output/) がテーブル・レポート機能を
  「実装範囲外」と書いたまま数ヶ月放置されていた）。状態はコード側の `# TODO:` や Issue に置き、
  docs には「なぜその設計にしたか」という判断理由だけを書く。

## 関連リンク

- [プロジェクトルート README](../README.md)
