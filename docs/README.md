# 設計ドキュメント

## このドキュメント集について

誘導電動機（IM）＋ケーブル系シミュレーション／パラメータ推定エンジンの
**設計意図・前提条件**と、**等価回路モデルの数式と実装の対応**を明文化したもの。
クラス単位の処理詳細はコードに委ね、設計判断の理由・前提・拡張方針や、
理論（数式）と設定・実装のひも付けなど、コードだけでは追いにくい情報を中心に記述する。

## ドキュメント構成

### ⭐ 差別化点（本エンジン固有の価値）
- [等価回路モデル: 数式 ↔ YAML キー ↔ 実装](./model_equations/index.md) — 等価回路の各インピーダンスモデルについて、数式（理論）・設定 YAML の係数キー・実装コードを 1 対 1 で対応づけた索引。インピーダンス可変モデルを支える中心ドキュメント（全体像の把握は下記「俯瞰・アーキテクチャ」から）。
- [EstimateParams: メーカー性能曲線との整合性](./estimate_params_curve_fitting_consistency.md) — パフォーマンスカーブ 4 量 `(|I|, P_out, cosφ, η)` がモデルと原理的に完全一致しない理由、残差重みの設計方針、カタログ品質の切り分け。

### 俯瞰・アーキテクチャ
- [シミュレーションロジック俯瞰ビュー](./overview.md) — エンジン全体像とレイヤー構造。
- [アーキテクチャ（層別設計）](./architecture/) — `pipeline / processor / algorithm / domain / shared` の層別設計。詳細を要する Algorithm 層・Shared 層は配下にサブツリーを持つ。
  - [0_component.md](./architecture/0_component.md): コンポーネント構成・依存方向・Mermaid 表記ルール
  - [1_shared.md](./architecture/1_shared.md): Shared 層・DTO 設計方針・命名規則（詳細: [`shared/`](./architecture/shared/)）
  - [2_domain.md](./architecture/2_domain.md): Domain 層（物理法則・共通計算・検証）
  - [3_algorithm.md](./architecture/3_algorithm.md): Algorithm 層（オーケストレーター・Strategy/Factory）（詳細: [`algorithm/`](./architecture/algorithm/)）
  - [4_processor.md](./architecture/4_processor.md): Processor 層・ステージ処理フロー
  - [5_pipeline.md](./architecture/5_pipeline.md): Pipeline 層・実行管理

### 詳細設計（厚い層）
- Algorithm 層: [input](./architecture/algorithm/input/0_overview.md) / [execute](./architecture/algorithm/execute/0_overview.md) / [output](./architecture/algorithm/output/0_overview.md)
- Shared 層: [DTO 設計方針](./architecture/shared/dto_principle.md) / [config パッケージ（設定・ロガー・@timer）](./architecture/shared/config_and_logger.md)

### 開発ガイドライン（横断規約）
- [開発ガイドライン](./rules/) — 設計原則・レイヤリングと import 規約・コーディングスタイル・数値計算の堅牢化・テスト方針。コードベース全体に一貫して適用する取り決め。

## 新規開発時の参考順序

1. [俯瞰ビュー](./overview.md) で全体像を把握
2. [architecture/0_component.md](./architecture/0_component.md) でレイヤー構成を理解
3. 該当スコープの詳細設計（`architecture/`（`algorithm/`・`shared/` 含む）, `model_equations/`）を確認して実装

## ドキュメント更新時の注意

- アーキテクチャ変更時は関連ドキュメントを更新する
- クラス単位の処理詳細はコードに委ね、設計前提・判断理由や数式↔実装の対応を記載する
- 依存関係の変更は必ずドキュメントへ反映する

## 関連リンク

- [プロジェクトルート README](../README.md)
