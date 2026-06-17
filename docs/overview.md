# シミュレーションロジック設計 - 俯瞰ビュー

## 概要

本プロジェクトは、**誘導電動機（IM）＋ケーブル系**の等価回路シミュレーション／
パラメータ推定エンジンである。IM・ケーブルの電気回路モデルに基づき、
電圧・電流・電力・特性値（回転速度・トルク・効率など）を計算し、
メーカー性能曲線への当てはめ（パラメータ推定）も行う。

本ドキュメントは、シミュレーションロジックの「俯瞰ビュー」を提供し、
各レイヤー・コンポーネントの詳細設計は `architecture/0_component.md`
および `architecture/1〜5_*.md` に委ねる。

## レイヤー構造と各層の責務

シミュレーションロジックは、以下のレイヤー構造（上位 → 下位への一方向依存）で
設計されている（詳細は `architecture/0_component.md` 参照）。

```text
pipeline → processor → algorithm → domain → shared
```

- **pipeline**: シミュレーション全体の実行パイプライン・制御（`architecture/5_pipeline.md`）
- **processor**: 各ステージ（Input/Execute/Output）で Dtos の処理フローを担当し、個別 Dto に対する処理は Algorithm 層へ委譲する（`architecture/4_processor.md`）
- **algorithm**: 各ステージで個別 Dto に対するコアロジック（モデル構築・電圧電流計算・特性値計算など）を実装する（`architecture/3_algorithm.md`、詳細は `architecture/algorithm/`）
- **domain**: 物理法則・電気計算・時系列集約などの共通ロジックとバリデーション（`architecture/2_domain.md`）
- **shared**: IM/ケーブル/システム向けの Input/Itm/Output DTO・共通設定・ユーティリティ（`architecture/1_shared.md`）

回路モデルの数式・YAML キー・実装の対応は `model_equations/index.md` を参照。

## 設計原則

- **責務分離**: 各レイヤーが明確な責務を持つ
- **依存関係の明確化**: 上位レイヤーから下位レイヤーへの一方向依存のみ許可
- **変更理由での分離**: 同じ理由で変更される要素を同じ場所に配置
- **拡張性**: インピーダンス可変モデル（励磁飽和・表皮効果・漏れ磁束飽和など）を追加しやすい設計
- **DTO を介したデータフロー**: 各ステージ間で DTO を介した明確なデータ受け渡し

これらの設計原則が、どのドキュメントで詳細化されているかの対応は次の通り。

- 責務分離・依存関係の明確化・レイヤー構造:
  - `architecture/0_component.md`, `architecture/5_pipeline.md`, `architecture/4_processor.md`
- DTO を介したデータフロー・DTO 命名規則:
  - `architecture/1_shared.md`, `architecture/4_processor.md`
- 物理法則・共通計算ロジック・バリデーション:
  - `architecture/2_domain.md`
- アルゴリズム構成・オーケストレーター・Strategy/Factory パターンの適用:
  - `architecture/3_algorithm.md`

## 設計パターン

### Strategy Pattern（主要パターン）

各ステージで動的にシミュレーションアルゴリズム（回路モデルなど）を選択可能にする。

### Factory Pattern（Strategy Pattern の補助）

Strategy Pattern で選択されるアルゴリズムの動的インスタンス化を実現。

### DTO Pattern

各ステージ間での DTO を介したデータ受け渡しを実現。
