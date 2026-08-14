# Outputアルゴリズム概要

## 概要

Output アルゴリズムは、Execute で得た単一 `ItmDto` を `OutputDto` へ変換し、
図・表・レポートをファイルへ出力する。物理計算そのものから、可視化・保存の
責務を切り離すための層である。

Processor 層 OutputStage から、実行モードごとのオーケストレーター経由で
呼び出される。

## 実装範囲

3 つの実行モードそれぞれに、専用のオーケストレーターを持つ。

- **ForwardByCartesianGrid**: 供給条件 (V, f) をサブプロット軸、slip または
  出力比を横軸とする性能図（2 種）と、参照軸直積を long 形式へ展開した表。
- **ForwardByOperatingPoints**: 運転点（リスト番号）を横軸とする性能図と、
  運転点ごとの特性量を並べた表。
- **EstimateParams**: ForwardByCartesianGrid と同じ図・表に加え、推定固有の
  構造化レポート（フィット要約 CSV ＋ 推定モデル catalog YAML ＋ 数値安定化
  イベント CSV）。

いずれも `run(itm_dto)` を入口とし、内部で
`convert → make_figure → make_table →（EstimateParams のみ）make_report` を
実行しながら、config で有効化された出力だけを保存・表示する。

## 図表専用 DTO を持たない設計

図・表・レポートは `OutputDto` の生量（`array_layout` / `result` /
`im_pc_catalogs`）から**都度派生計算**する。中間の図表専用 DTO は作らない。

図（matplotlib `Figure`）・表（pandas `DataFrame`）・レポート（`ReportDto`）は
オーケストレーター内で build ステップから export ステップへ渡すだけの一時
artifact であり、**戻り値の `OutputDto` には載せない**。ファイルへの出力は
side effect として扱う。

## 関連ドキュメント

- データフロー: [`1_data_flow.md`](./1_data_flow.md)
- コンポーネント: [`2_component.md`](./2_component.md)
- 設計方針: [`3_design_principles.md`](./3_design_principles.md)
- テスト方針: [`4_test_strategy.md`](./4_test_strategy.md)
