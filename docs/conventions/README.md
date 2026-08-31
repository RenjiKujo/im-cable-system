# 開発規約（再利用可能なルール集）

このフォルダは、特定プロジェクトに限定されない**設計・実装の取り決め**をまとめる。
データサイエンス／数値計算系の Python プロジェクトを主対象としつつ、
複数プロジェクトで使い回せる規約を記述する。

各ファイルは「一般原則（どのプロジェクトでも通用する考え方）」を本体とし、
プロジェクト固有の具体化（レイヤー名・ドメイン固有の例・実行コマンドなど）は
`> 例（このプロジェクトでの適用）` の引用で明示し、ルール本体と区別する。
本リポジトリでの実際の適用は [`docs/architecture/`](../architecture/) にある。

## なぜ規約を明文化するか

機械学習・数値計算を主題とするコードベースは、放置すると次の理由で急速に保守不能になりやすい。

- **抽象化が薄く**、計算式と入出力整形と I/O が一つの関数に同居する。
- **変更理由が異なるコードが同居**し、モデル追加のたびに広範囲を書き換える羽目になる。
- **数値的な破綻（ゼロ除算・発散・NaN 伝播）** が握りつぶされ、原因の特定が遅れる。

この規約は、これらを構造で防ぐために導入した取り決めである。
出発点は SOLID・Clean Architecture・GoF パターンといった一般的な設計知見だが、
**データサイエンス／最適化のコードに効くものを選び、再利用しやすい粒度で整理**している。

## 3 つの層

規約は抽象度で 3 層に分かれる。上の層ほど「なぜそう書くか」、下の層ほど「どう書くか」を扱う。

| 層 | 扱う範囲 | ドキュメント |
|---|---|---|
| **層 3: 横断概念** | コードベース全体を貫く構造・規則。層 2 の原則を、依存方向・数値・テストという具体的な軸へ落としたもの | [3_layering_and_imports.md](./3_layering_and_imports.md)<br>[4_numerical_robustness.md](./4_numerical_robustness.md)<br>[5_testing.md](./5_testing.md) |
| **層 2: 設計原則** | クラス単位の設計方針。何を抽象化し、どこで生成し、どう依存するか | [2_design_principles.md](./2_design_principles.md) |
| **層 1: 表記** | `ruff` / `pyright` で機械的に検証**できない**表記・命名・docstring | [1_code_style.md](./1_code_style.md) |

| ドキュメント | 内容 |
|---|---|
| [1_code_style.md](./1_code_style.md) | 命名・型ヒント・docstring・禁止事項・モジュール分割の目安 |
| [2_design_principles.md](./2_design_principles.md) | インターフェース駆動設計・抽象への依存・生成の分離（ファクトリー）・継承より委譲 |
| [3_layering_and_imports.md](./3_layering_and_imports.md) | レイヤー構成と一方向依存・公開窓口（ファサード）経由の import 規約 |
| [4_numerical_robustness.md](./4_numerical_robustness.md) | ゼロ除算・発散・NaN/inf の扱いを統一する数値ガード方針 |
| [5_testing.md](./5_testing.md) | 契約をテストで固定する方針・テストツリーの構成 |

## 正本マップ（どこを参照するか）

機械で強制できる項目は**設定ファイルが正本**であり、このフォルダには**再掲しない**。
このフォルダに書くのは、機械強制できない人手ルールと、「なぜその設定なのか」だけである。
設定値を知りたいときは常に下表の「機械強制（正本）」列を見る。

| 領域 | 機械強制（正本） | 人手ルール |
|---|---|---|
| 整形（行長・引用符・インデント幅） | `ruff.toml` の `[format]` / `line-length` | — |
| lint（命名・import 順・未使用・推奨イディオム・`print`） | `ruff.toml` の `[lint]` `select` / `ignore` | — |
| lint の緩和とその理由 | `ruff.toml` の `[lint.per-file-ignores]` | — |
| 型チェック | `pyproject.toml` の `[tool.pyright]` | [1_code_style.md](./1_code_style.md) の「型ヒント」 |
| テストの探索範囲・命名規約・マーカー | `pyproject.toml` の `[tool.pytest.ini_options]` | [5_testing.md](./5_testing.md) |
| docstring の書式 | **なし**（`ruff` の `D` は未採用。理由は `ruff.toml` の `[lint.pydocstyle]` 参照） | [1_code_style.md](./1_code_style.md) の「docstring・コメント」 |
| 関数・クラス・ファイルの行数／複雑度 | **なし**（`lizard` で随時点検） | [1_code_style.md](./1_code_style.md) の「モジュールサイズの目安」 |
| 数値ガードの比較演算子・NaN/inf の意味づけ | **なし** | [4_numerical_robustness.md](./4_numerical_robustness.md) |
| レイヤー間の依存方向・公開窓口経由の import | **なし** | [3_layering_and_imports.md](./3_layering_and_imports.md) |

## 置き場所の切り分け

| 種別 | 置き場所 |
|---|---|
| 一般原則（再利用対象） | この `docs/conventions/` |
| 機械強制できる設定値 | `ruff.toml` / `pyproject.toml`（上の正本マップ） |
| このリポジトリでの適用例 | [`docs/architecture/`](../architecture/) |
