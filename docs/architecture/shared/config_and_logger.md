# config パッケージ（設定・ロガー・@timer）

IM ケーブルシステムの**実行時設定とロガーの公開窓口**です。
`IConfig` / `Config` と同梱 `config.yaml` の仕様の正本としてこのドキュメントを使います
（クラス・YAML 側の docstring/コメントは契約と概要のみに留めています）。

> 対象パッケージ: `src/im_cable_system/engine/shared/config/`。
> 本書中の `schema/` / `decorators/` / `config.yaml` 等の相対パスは、
> このパッケージディレクトリ基準で読みます。

## 公開 API と import 方針

層外（algorithm / processor / pipeline / tests）からは、
**`im_cable_system.engine.shared.config` ルートから直接 import** します。
`schema/` や `decorators/` 配下を直接掘る必要はありません。

公開しているのは次の 4 グループです（個々のクラス名は `__init__.py` の `__all__` を正とする）。

1. **設定本体・ロガー**: `Config` / `IConfig` / `Logger` / `ILogger` / `load_config` / `load_yaml_root_dict`。
2. **横断デコレータ**: `timer`。
3. **検証済みスナップショット dataclass**: `ConfigSnapshot` と各セクションの設定 dataclass。
4. **Enum**: `Severity`, `LogLevel`, `DataProcessingMethod`, `ConvergenceCriterion` など。

ファクトリ（`*ConfigFactory` / `ConfigSnapshotFactory`）と内部 utility（`_parsers`）は
**層外へ非公開**です。生成は `Config.create` に一本化しているため、層外から個別 factory を
呼ぶ動機はありません。

```python
from im_cable_system.engine.shared.config import Config, IConfig, Severity
```

## 設計方針: fail-fast バリデーション

`Config.create` は内部で `ConfigSnapshotFactory` が YAML 全体を検証・正規化し、
検証済みの dataclass（`ConfigSnapshot`）を保持します。各 `IConfig` プロパティは
このスナップショットへの薄い attribute アクセスを返すだけで、`dict.get(...)` の連鎖や
デフォルト値の重複定義を持ちません。

- YAML に書き間違い（Enum 外の文字列、非数値、負値など）があれば、Pipeline 実行を待たず
  `Config.create` の時点で、原因キー（フルパス）と受け取った値を含む `ValueError` で停止します。
- 利用側（Validator / Strategy / Orchestrator）は `config.<section>.<field>` の attribute
  アクセスだけで完結します。
- 新しい設定キーは `schema/<section>.py` に dataclass / Enum / factory を足し、
  `ConfigSnapshot` と `ConfigSnapshotFactory` を更新するだけで済みます。

### 「既定値」の 2 種類

- **同梱 `config.yaml` の値**: パッケージ同梱 YAML に実際に書かれている値。
  別の YAML を渡さない限り実行時に使われます。
- **コード側フォールバック**: YAML キーが**欠損**したときに `Config` が返す最終防衛線の値。
  同梱 `config.yaml` は全項目を埋めているため通常は使われません。
  **値が存在するが不正**な場合はフォールバックを使わず `Config.create` で `ValueError`（fail-fast）。

## クイックスタート

```python
from pathlib import Path
from im_cable_system.engine.shared.config import Config

# 同梱 config.yaml を使う
config = Config.create()

# クライアント側の設定ファイルを明示する
config = Config.create(config_file_path=Path("path/to/config.yaml"))
```

`Config.create` の引数はすべてキーワード専用です。`config_file_path` は内部で `resolve()` され、
以降の YAML 相対パス解決の基準になります。

## パス解決（2 段フォールバック）

外部 YAML や dump 出力先のパスは、次の優先順位で解決します。

| 対象 | 1 段目（`Config.create` 引数） | 2 段目（`config.yaml` キー） |
| --- | --- | --- |
| 設定ファイル本体 | `config_file_path` | パッケージ同梱 `config.yaml` |
| IM / ケーブルシリーズカタログ | `im_series_catalog_file_path`, `cable_series_catalog_file_path` | `series_catalog_for_forward_simulation.{im,cable}_file_path` |
| IM / ケーブル境界・初期値 YAML | `im_bounds_and_init_file_path`, `cable_bounds_and_init_file_path` | `bounds_and_init_for_estimation_parameters.{im,cable}_file_path` |
| dump 出力ベースディレクトリ | `dump_base_dir`（**絶対パス必須**） | `dump.base_dir` |

- 1 段目・2 段目とも未指定なら、対応する getter が `ValueError` を送出します。
- `config.yaml` 上の相対パスは、**その `config.yaml` の親ディレクトリ基準**で解決します。
- Config はパス解決までを担い、カタログ・境界 YAML の読み込みと DTO 変換は利用側の責務です。

## dump 出力先の方針

pip install 後のパッケージ内部へ dump が書き出される事故を防ぐため、
同梱 `config.yaml` には `dump.base_dir` を**置きません**。dump を使うクライアントは、
`Config.create(dump_base_dir=Path("/abs/path"))`（絶対パス必須）か、
クライアント側 `config.yaml` の `dump.base_dir`（絶対パス、または親 Dir 基準の相対パス）で
出力先を指定します。どちらも未指定なら `get_dump_base_dir()` が `ValueError` を送出します。

各ブロックの `enabled` は同梱 `config.yaml`・コード側フォールバックともすべて `False` です
（dump は明示的に有効化したクライアントだけが書き出す方針）。実際に書き出す直前に
`get_dump_base_dir()` で絶対パスを取得する責務は呼び出し側にあります。

## YAML スキーマ（責務 × ステージ）

`config.yaml` は責務軸（トップキー）とステージ軸の二軸で構成します。

**責務軸（トップキー）**

- `project_info`: プロジェクト名、バージョン、文字コード、タイムゾーン。
- `logging`: ログレベルとログフォーマット。
- `series_catalog_for_forward_simulation`: Forward 用シリーズカタログのパス。
- `bounds_and_init_for_estimation_parameters`: EstimateParams 用境界・初期値のパス。
- `dump`: 各ステージの dump 設定。
- `calculation`: 各ステージの計算設定。

**ステージ軸（`dump` / `calculation` の下位）**

- `input`: 入力 DTO 構築・入力 DTO dump。
- `execute`: 計算実行、検証、数値安定化、EstimateParams 最適化。
- `output`: グラフ表示、図表・テーブル・report・出力 DTO dump。

**スコープ外**

- モード（`ForwardByCartesianGrid` / `EstimateParams`）は YAML に持ちません。
  Pipeline クラスが分かれており、選択時点でモードが確定します。
- ジョブ単位で変わるデータ（シリーズ選択 TSV、軸 TSV、性能曲線 TSV）は `config.yaml` に置かず、
  `JobSpec` 経由で渡します。

## `IConfig` API 一覧

返り値はすべて `schema/` 配下の frozen dataclass / Enum / `Path` です。
各 dataclass のフィールド詳細は `schema/<section>.py` を参照してください。

| API | 読み取り元 YAML キー | 返り値 |
| --- | --- | --- |
| `config_file_path` (property) | – | `Path`（`resolve()` 済み） |
| `project_info` (property) | `project_info` | `ProjectInfoConfig` |
| `logging_config` (property) | `logging` | `LoggingConfig` |
| `get_im_series_catalog_file_path()` | `series_catalog_for_forward_simulation.im_file_path` | `Path` |
| `get_cable_series_catalog_file_path()` | `series_catalog_for_forward_simulation.cable_file_path` | `Path` |
| `get_im_bounds_and_init_file_path()` | `bounds_and_init_for_estimation_parameters.im_file_path` | `Path` |
| `get_cable_bounds_and_init_file_path()` | `bounds_and_init_for_estimation_parameters.cable_file_path` | `Path` |
| `dump_data_config` (property) | `dump.{input,execute,output}.*` | `DumpDataConfig`（`base_dir` を含まない） |
| `get_dump_base_dir()` | `dump.base_dir` | `Path`（絶対パス） |
| `input_validation_config` (property) | `calculation.input.validation` | `InputValidationConfig` |
| `data_processing` (property) | `calculation.execute.data_processing` | `DataProcessingConfig` |
| `numerical_guard_config` (property) | `calculation.execute.numerical_guard` | `NumericalGuardConfig` |
| `validation_config` (property) | `calculation.execute.validation` | `ValidationConfig` |
| `current_estimation_config` (property) | `calculation.execute.current_estimation` | `CurrentEstimationConfig` |
| `estimate_params_calculation_config` (property) | `calculation.execute.estimate_params` | `EstimateParamsConfig` |
| `output_figures_config` (property) | `calculation.output.figures` | `OutputFiguresConfig` |

`DumpDataConfig` は `figures` / `tables` / `reports` / `dtos`（`input_dtos` / `itm_dtos` /
`output_dtos`）のサブブロックを持ちます。`reports` は estimate_params 用の構造化レポートで、
セクションごとに `filename_pattern` を持ちます。

## エラー仕様

| 状況 | 例外 |
| --- | --- |
| `Config.create(dump_base_dir=...)` が相対パス | `ValueError`（`__init__` で検出） |
| YAML 値が型ミスマッチ / Enum 値域外 / 制約違反（正値必須に `0`、`inf`/`NaN` 等） | `ValueError`（`Config.create` で検出。fail-fast） |
| トップキーが dict でない | `ValueError`（`Config.create` で検出。fail-fast） |
| カタログ／境界 YAML のパスが 1 段目・2 段目とも未指定 | 該当 `get_*_file_path()` が `ValueError` |
| `get_dump_base_dir()` のパスが 1 段目・2 段目とも未指定または空文字 | `ValueError` |

## ロガーと `@timer` の方針

`Logger` / `ILogger` / `@timer` は、**ログ重複を避け、想定外エラーは最上位境界で 1 度だけ
記録する**方針で運用します。Pipeline / Processor / Algorithm で `@timer` が層をまたいで
重なっても、同じ例外が層数分だけ ERROR に重複しません。

### Logger の構成

`Logger.create(config: IConfig)` で取得します。YAML を読み直さず、`Config.create` 時点で
検証済みの `config.logging_config` / `config.project_info` を attribute アクセスで取り出すだけです
（YAML 解釈は Config に一本化）。

```python
from im_cable_system.engine.shared.config import Config, Logger

config = Config.create(config_file_path=path)
logger = Logger.create(config)
```

`config.config_file_path` をキーにキャッシュするため、同じ設定ファイルから複数回
`Logger.create` を呼んでも stdlib `Handler` が二重登録されません。

### ログレベルの使い分け

| レベル | 用途 | 主な出し手 |
| --- | --- | --- |
| `INFO` | 正常系。`@timer` の `[start]` / `[end]` / `[abort]` | `@timer`、Runner、各層のキー処理 |
| `WARNING` | 続行可能だが伝えたい状況（軽微なフォールバック等） | アルゴリズム層 |
| `ERROR` | 続行できない異常（バリデーション失敗など） | Runner（最上位境界） |
| `ERROR`（traceback 付き）| 想定外の例外。`logger.exception(...)` でスタックトレース自動付与 | Runner（最上位境界） |

### `@timer` の出力

| 状況 | レベル | 内容 |
| --- | --- | --- |
| 正常終了 | `INFO` | `[start] <qualname>` / `[end] <qualname> NN.NN seconds` |
| 例外発生 | `INFO` | `[start] <qualname>` / `[abort] <qualname> NN.NN seconds` |
| `min_duration` 未満で正常終了 | （出力なし）| 閾値を超えたときだけ `[start]` / `[end]` |
| `min_duration` 未満で例外 | `INFO` | `[start]` / `[abort]` を必ず出す |

- 例外時も `@timer` は `ERROR` を出さず、例外メッセージ本文も載せません（多層での重複回避）。
- `[abort]` は「この境界を例外が突き抜けた」事実のみを示し、中身は最上位境界の
  `logger.exception(...)` がスタックトレースとして集約します。

### Runner（最上位境界）のエラー方針

| 種類 | キャッチ対象 | ログ呼び出し | 終了コード |
| --- | --- | --- | --- |
| 想定済みの入力不備 | `ValueError` | `logger.error("validation failed: %s", exc)` | `2` |
| 想定外の例外（バグ・環境問題）| `Exception` | `logger.exception("unexpected error ...")` | `1` |
| 正常終了 | – | `logger.info(...)` | `0` |

中間層（Pipeline / Processor / Algorithm）は基本的に `ValueError` を投げて止めるだけで、
ログは `@timer` の `INFO [abort]` に任せます。結果として 1 例外あたり、各層に
`INFO [abort]` が 1 行ずつ・Runner に `ERROR` が 1 行だけ残り、「どこで止まったか」と
「本当の原因」が 1 か所に集約されます。

**禁則**: 中間層で同じ例外をログ→`raise` する／`logger.error(...)` を直接呼ぶのは原則禁止
（`@timer` の `[abort]` と重複するため）。コンテキストを残したいときは `logger.warning(...)` を使います。

## ファイルごとの責務

- `__init__.py`: 公開窓口。公開シンボルを `__all__` でまとめる。
- `i_app_config.py` / `app_config.py`: `IConfig` の契約と `Config` の実装
  （`ConfigSnapshotFactory` で検証・正規化した dataclass を返す facade）。
- `config.yaml`: パッケージ同梱の既定設定。
- `schema/`: 検証済みスナップショットの dataclass / Enum / セクション factory / 集約 factory。
  dataclass・Enum・`ConfigSnapshot` は `__init__.py` から再エクスポートし、factory と
  `_parsers` は層外非公開。
- `i_app_logger.py` / `app_logger.py`: `ILogger` の契約と実装（stdlib `logging` を内包）。
- `decorators/timer.py`: `@timer` デコレータ（方針は本書のロガー節を参照）。
- `config_reader.py`: YAML 読み込みの共通部品。
