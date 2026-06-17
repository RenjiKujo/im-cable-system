# Executeアルゴリズム概要


Execute は ExecuteStage が利用するアルゴリズムである。オーケストレーターは **1 つのインターフェース** `IForwardExecutionOrchestrator` を定義し、その実装として **forward（順計算）** の **Direct**（電流依存なし）と **Iteration**（電流依存あり）の 2 種を提供する。パラメータ推定は別インターフェースとして `orchestrate/estimate_params/` 配下に配置する。いずれも「どの実装を使うか」はファクトリー（オーケストレーター）の分岐で決まる。

## 1. forward（順計算）（入口: 運転条件、出口: ItmDto）

- **forward（順計算）**: 1 本の `InputDto`（slip あり）に対して build_model → simulate → validate_itm_dto を実行し、`ItmDto` を返す。実装は **Direct**（電流依存なし）と **Iteration**（電流依存あり）の 2 種で、配置は `orchestrate/forward/`。

Processor 層からは `IForwardExecutionOrchestrator` のみが見え、`ForwardExecutionOrchestratorFactory.create(...)` で Direct / Iteration いずれかの実装を取得する。

## 2. パラメータ推定

**別インターフェース**（`IEstimateParamsExecutionOrchestrator`）を `orchestrate/estimate_params/` 配下に配置する。入口に **パフォーマンス曲線が必須**であり、指定モデルでインピーダンスやそのパラメータが不足している場合（または Config で指定した場合）に、目標パフォーマンス曲線に合うようにパラメータを推定する。出口は **推定パラメータ** と、推定値で求めた中間 DTO。

**カタログとの整合性問題と推定方針**は別途まとめている。`(|I|, P_{\mathrm{out}}, \cos\varphi, \eta)` がモデル自由度との関係で過剰決定になっていること、カタログ側が自己無矛盾ではないこと、それらを踏まえた残差設計（重み・吸収パラメータ）の方針は [`estimate_params_curve_fitting_consistency.md`](./estimate_params_curve_fitting_consistency.md) を参照。

- データフロー: [1_data_flow.md](./1_data_flow.md)
- コンポーネント詳細: [2_component.md](./2_component.md)
- 設計原則: [3_design_principles.md](./3_design_principles.md)
- テスト戦略: [4_test_strategy.md](./4_test_strategy.md)
- パラメータ推定とパフォーマンスカーブの整合性問題: [estimate_params_curve_fitting_consistency.md](./estimate_params_curve_fitting_consistency.md)
