# Outputアルゴリズム概要

## 概要

Output アルゴリズムは、Execute で得た `ItmDto` を可視化・比較用の `OutputDto` へ整形する。物理計算そのものから、グラフ・レポート向けのデータ整形を切り離すための層である。

im_cable_system では、forward の結果と IM カタログ性能カーブを比較する図表生成を主な対象とする。

## 実装範囲

現時点の Output は、図表生成とグラフ描画を中心に実装している。

- `ItmDto` から slip 軸性能カーブを生成する。
- `ItmDto` から出力比軸性能カーブを生成する。
- カタログ性能カーブを同じ軸の図表 DTO へ変換する。
- シミュレーション曲線とカタログ曲線を重ねて表示する。

テーブル出力やファイル形式ごとの出力制御は、必要になった段階で追加する。

## 関連ドキュメント

- データフロー: [`1_data_flow.md`](./1_data_flow.md)
- コンポーネント: [`2_component.md`](./2_component.md)
- 設計方針: [`3_design_principles.md`](./3_design_principles.md)
- テスト方針: [`4_test_strategy.md`](./4_test_strategy.md)
