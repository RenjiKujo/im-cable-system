# Outputアルゴリズムコンポーネント

## 概要

この文書は、Output アルゴリズムの主要コンポーネントと責務境界を示す。実装クラスの詳細はコードを正とし、ここでは公開向けに必要な構造だけを扱う。

## FigureBuildingOrchestrator

`FigureBuildingOrchestrator` は、図表生成の入口である。`ItmDto` と `ImSeriesPerformanceCurveDtos | None` を受け取り、利用可能な図表 DTO を `OutputFiguresDto` にまとめる。

主な責務は次の通り。

- `ItmDto` の参照軸が図表生成に必要な条件を満たすか確認する。
- シミュレーション結果から slip 軸・出力比軸の図表 DTO を生成する。
- カタログ性能カーブがある場合は、同じ軸の図表 DTO へ変換する。
- 生成できない図表は optional として扱い、呼び出し側が結果の有無を判断できるようにする。

## FiguresBuilder

図表の種類ごとの差分は Builder に分ける。

- **SlipAxisFiguresBuilder**: slip 軸上で、出力、入力電流、力率、効率を並べる。
- **OutputRatioAxisFiguresBuilder**: 出力比を x 軸にし、回転数、電流率、効率、力率を並べる。
- **ImPerformanceFiguresBuilder**: カタログ性能カーブを slip 軸の図表 DTO へ変換する。
- **OutputRatioAxisImPerformanceFiguresBuilder**: カタログ性能カーブを出力比軸の図表 DTO へ変換する。

この分割により、図表の追加や軸の変更を Orchestrator に集中させず、図表単位で変更できる。

## Export

グラフ描画は、`OutputDto` に含まれる図表 DTO を具体的な描画オブジェクトへ変換する責務を持つ。Output アルゴリズム本体は、描画ライブラリに依存しない図表 DTO の構築を優先し、描画・保存形式の差分を Export 側へ寄せる。

## DTO の位置付け

`OutputFiguresDto` は、生成済みの図表 DTO をまとめるコンテナである。`OutputDto` は、対象システム名と `OutputFiguresDto` を持つトップレベル DTO として扱う。

テーブル DTO は現時点では主要実装範囲外である。追加する場合も、図表 DTO と同じく、列・単位・値を持つ描画/出力ライブラリ非依存の DTO として設計する。
