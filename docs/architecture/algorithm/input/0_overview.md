# Inputアルゴリズム概要

## 概要

Input アルゴリズムは、ジョブ仕様（ファイルパス束や統合 TSV）から、Execute が扱える `InputDto` / `InputDtos` を構築・検証する。Processor 層 InputStage から実行モードごとのオーケストレーター経由で呼び出される。

物理計算は持たず、「読み込めるか・組み立てられるか・整合しているか」を段階的に確認することに責務を絞る。

## 実装範囲

現時点の Input は、次の 2 つの実行モードを対象とする。

- **forward**: 1 ジョブ分のパス束から単一の `InputDto` を構築する。CartesianGrid / OperatingPoints の差は参照軸（`reference_axes`）の選び方だけで吸収する。
- **estimate_params**: 1 つの統合 TSV から、候補の直積に対応する複数 `InputDto`（`InputDtos`）を構築する。

いずれも `build_input_dto` を入口とし、内部で `_validate_job_spec -> _load_data -> _assemble_input_dto -> _validate_input_dto` の 4 段を順に実行する（いずれも外部非公開の private メソッド。パッケージ名としては underscore なしの `validate_job_spec/` 等を使う）。

## 関連ドキュメント

- データフロー: [`1_data_flow.md`](./1_data_flow.md)
- コンポーネント: [`2_component.md`](./2_component.md)
- 設計前提: [`3_design_principles.md`](./3_design_principles.md)
- テスト方針: [`4_test_strategy.md`](./4_test_strategy.md)
