# シミュレーションロジック設計 - SharedコンポーネントとDTO設計方針

> **この文書が正本である範囲**: Shared 層の役割・提供要素・DTO パッケージ構成（層レベル）。
>
> **正本ではない（参照先）**: DTO の命名規則・属性・モード別差分は [`shared/dto_principle.md`](./shared/dto_principle.md)、数値ガードは [`conventions/4_numerical_robustness.md`](../conventions/4_numerical_robustness.md)、import 規約は [`conventions/3_layering_and_imports.md`](../conventions/3_layering_and_imports.md)。

## 概要

本ドキュメントは、**シミュレーション全体で汎用的に参照される共通ルール**を定義する。Sharedコンポーネント（`src/im_cable_system/engine/shared/`）の構成とDTO設計方針について、共通する原則のみを記載し、具体的なクラス名・属性名・パッケージ名などは**例として示すに留める**。各シミュレーションタイプ固有の詳細は、当該シミュレーションタイプのドキュメントを参照すること。

## Sharedコンポーネントの役割

全コンポーネントで共通利用されるデータ構造（DTO）・設定・ジョブ仕様・推定仕様・
数値安定化イベント集計・ログ／横断デコレータ等を提供する。

## 設計方針

Shared層は、基本的なデータクラス（DTO）に限定し、計算ロジックはDomain層に配置する。

## 提供する要素

### データ構造（DTO）

InputDto、ItmDto、OutputDtoなどのSimulationエンジン用DTOを提供する。

詳細は「DTO設計方針」セクションを参照してください。

### 設定・ログ・横断デコレータ

シミュレーション実行に必要な設定（`IConfig` / `Config`）、ロガー（`ILogger` /
`Logger`）、および横断デコレータ（`@timer`）を提供する。詳細は
[`shared/config_and_logger.md`](./shared/config_and_logger.md) を参照する。

### ジョブ仕様（`job_spec/`）

実行モード別のジョブ仕様を提供する（`ForwardJobSpec` / `ForwardJobSpecs` /
`EstimateParamsJobSpec`）。

### 推定仕様（`estimate_params_fit_spec/`）

パラメータ推定の探索境界・初期値仕様を提供する（`ParameterFitSpec` / `InitMethod` /
`ImParameterFitDescriptorBounds` / `CableParameterFitDescriptorBounds` /
`ImSubsystemName` / `ImPrimaryModelName` / `ImExcitationModelName` /
`ImSecondaryModelName` / `ImFrictionWindageModelName` / `ImStrayLoadModelName` /
`CableConductorModelName`）。
Input（初期値決定）と Execute（探索境界決定）の**両ステージから参照される横断責務**
である。

### 数値安定化イベント集計（`numerical_stability/`）

シミュレーション中の数値安定化イベントを集計する（`NumericalStabilityAccumulator`
ほか）。

## DTO設計方針（層レベル）

Shared 層は、各ステージ間のデータ受け渡しを担う DTO を提供する。ここでは**層レベルの方針**のみを示し、**命名規則・属性・モード別の差分などの詳細は [`shared/dto_principle.md`](./shared/dto_principle.md) を正とする**（重複記載を避ける）。

### 責務分離の原則
- **InputDto**: シミュレーションへの入力データのみを保持する。
- **ItmDto**: 中間処理データ（モデル構築結果・シミュレーション結果）を保持し、処理段階に応じて段階的に構築する。
- **OutputDto**: 出力・可視化のもととなる結果データを保持する。

### 設計原則
- DTO は値・単位・状態の保持と単位変換のみを担う。数値ガード（クランプ）・数値安定化イベント記録は持たない
  （判定規則の正本は [`conventions/4_numerical_robustness.md`](../conventions/4_numerical_robustness.md)、
  発火は domain / algorithm 層の責務）。
- 拡張時は新規ドメインをオプショナル属性として追加し、既存コードへの影響を最小化する。
- 命名規則・不変性など、上記以外の詳細は [`shared/dto_principle.md`](./shared/dto_principle.md) を正とする。

### 汎用DTOとの関係

Simulationエンジン用 DTO（`input/` / `itm/` / `output/`）は、汎用 DTO（`shared/dto/generic/`）を参照して構築される。汎用 DTO は Simulationエンジン用 DTO を参照しない（依存は一方向）。汎用 DTO（値オブジェクト）の実体は `src/im_cable_system/engine/shared/dto/generic/` を参照すること。

### DTO パッケージ構成（Shared層）

```
src/im_cable_system/engine/shared/dto/
├── generic/    … 汎用 DTO（physical_quantity / entity / interfaces / im_cable_system など）
├── input/      … 入力 DTO の公開窓口
├── itm/        … 中間 DTO の公開窓口（model / simulation_result のサブパッケージを含む）
└── output/     … 出力 DTO の公開窓口（図表専用 DTO は持たない）
```

**インポート**: 層間・DTO の import 窓口は [`docs/conventions/3_layering_and_imports.md`](../conventions/3_layering_and_imports.md) を参照する。

## 依存関係

Sharedコンポーネントは他のコンポーネントに依存しない。

詳細な依存関係については、`0_component.md`の「コンポーネントの依存関係」セクションを参照してください。
