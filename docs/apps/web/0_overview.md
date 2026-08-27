# apps/web — ジョブ投入型 Web 面

> **この文書が正本である範囲**: Web クライアント層（FastAPI + Streamlit +
> SQLAlchemy）の構成・ジョブディレクトリのレイアウト・ジョブライフサイクル
> （状態遷移）・DB スキーマ・API 表面・engine との境界。
>
> **正本ではない（参照先）**: engine のレイヤー構造は
> [`../../architecture/0_component.md`](../../architecture/0_component.md)、
> CLI の終了コード規約（Runner エラー方針）は
> [`../../architecture/shared/config_and_logger.md`](../../architecture/shared/config_and_logger.md)。

## 位置づけ

`apps/web/` は `runner/` と同じく engine（`src/im_cable_system/engine/`）の外側の
クライアントであり、`docs/architecture/0_component.md` が正本とする 5 層構造
（`pipeline → processor → algorithm → domain → shared`）の対象外である。
**engine は 1 行も変更しない。** 計算は `runner/` 配下の run_*.py を subprocess として
起動し、結果はファイル経由（`dump_base_dir` 配下）で受け渡す。ブラウザからジョブを
投げ、すぐ `job_id` を受け取り、完了を待たずに離れ、あとから状態と成果物を見る
ことを目的とする。

## ディレクトリと依存方向

```text
apps/web/
├── runner_gateway/
├── store/
├── engine_contract/
├── api/
├── ui/
└── presets/
```

依存は上から下への一方向のみである。

```text
ui (Streamlit) --HTTP--> api (FastAPI) --> store (SQLAlchemy)
                                        --> runner_gateway --subprocess--> runner/run_*.py
                                        --> engine_contract
```

- `ui` は HTTP クライアント（`httpx`）以外の依存を持たない。engine・
  `apps.web.api`・`apps.web.runner_gateway`・`apps.web.store` のいずれも
  import しない。
- `api` は `store`（ジョブ台帳）と `runner_gateway`（subprocess 実行）と
  `engine_contract`（engine 入出力ファイル契約の写し）に依存する。engine の
  公開窓口（`im_cable_system.estimate_params` 等）やリーフ実装には直接依存しない
  ——触るのは `runner/` 配下の run_*.py の CLI 契約（引数名と終了コード）と、
  成果物 YAML を**表示目的で読む**こと（DB には持たない）だけである。
- `runner_gateway` は HTTP も DB も import しない。
- `engine_contract` は葉（依存の行き止まり）。stdlib と `yaml` 以外に依存しない。

`docs/conventions/3_layering_and_imports.md` は「実装モジュールを置く
ディレクトリには**原則** `__init__.py` を置く」と定めるが、次の 2 種は
意図的に置かない。どちらも「import される側ではない」ためである。

- `ui/pages/`: Streamlit のマルチページ規約が、ファイル名そのものを
  ページ順序と表示名に使う。パッケージ化すると規約から外れる。
- `tests/` 配下の fake runner 置き場（`test_web/api/data/fake_runners/`、
  `test_web/runner_gateway/data/`）: subprocess から起動される単体
  スクリプトで、import 対象ではない。

## runner_gateway — subprocess を回す薄い皮

```text
apps/web/runner_gateway/
├── settings.py
├── job_layout.py
├── command_builder.py
├── executor.py
└── artifacts.py
```

- `settings.py`: `RunnerGatewaySettings`。python 実行パス・`jobs_root`・
  並行数・壁時計タイムアウトを環境変数から読む（未設定はリポジトリ内既定値。
  変数名は下の「環境変数」節）。`repo_root` と `runner/` の配置は自モジュール
  位置からの相対で固定し、環境変数では変えられない。
- `job_layout.py`: `JobLayout` の作成、アップロードのサニタイズ保存、
  config.yaml のマテリアライズ（プリセット＋上書きのマージ、または丸ごと
  アップロード）、来歴（`cmd.json`）の記録、ジョブディレクトリの削除
  （`jobs_root` 配下であることを検証してから `rmtree`）。
- `command_builder.py`: `JobMode` ごとの argv 組み立て。catalog / bounds は
  必ず絶対パスで載せる純関数。
- `executor.py`: subprocess の起動・壁時計タイムアウト・キャンセル
  （terminate → 猶予後 kill）・`run.log` 書き出し。終了コードを
  `JobStatus` / `ErrorKind` へ写す。
- `artifacts.py`: `outputs/` の走査（`ArtifactInfo`）とパストラバーサル検証。

### catalog / bounds を必ず明示的に渡す

`Config` は `series_catalog_for_forward_simulation.*` /
`bounds_and_init_for_estimation_parameters.*` の相対パスを、その
`config.yaml` 自身の親ディレクトリ基準で解決する。API がプリセットや
アップロードされた `config.yaml` を `<job_dir>/config.yaml` へマテリアライズ
すると、プリセット内の相対参照は別の場所を指してしまう。回避策として
パスを書き換えるのではなく、既存の CLI 引数（`--im-catalog` /
`--cable-catalog` / `--im-bounds` / `--cable-bounds`）で常に絶対パスを
明示する。未アップロード時の既定値は、同梱の `src/im_cable_system/catalog/`
および `src/im_cable_system/bounds_and_init/` 配下の YAML である
（`RunnerGatewaySettings` の `*_default` プロパティ）。

## ジョブディレクトリのレイアウト

`<jobs_root>/<job_id>/` 配下に次を持つ。`job_id` は uuid4 hex。

- `inputs/`: アップロードされた入力（basename をサニタイズして保存）。
- `config.yaml`: api がマテリアライズした設定（プリセット＋上書き、または
  丸ごとアップロード）。
- `cmd.json`: 実際に実行した argv と、gateway が**追加で設定した**環境変数
  （来歴。成果物メタではない。「この結果を CLI で再現する」がそのまま可能に
  なる）。subprocess は `os.environ` を継承するが、継承分は記録しない
  ——サーバの環境変数を丸ごと書き出すと、来歴ファイルが秘密の持ち出し口に
  なるため。再現に要るのは差分だけである。
- `run.log`: subprocess の stdout + stderr のマージ（engine のログは全部
  stderr）。
- `outputs/`: `--dump-base-dir` の実体。配下に `figures/` `tables/`
  `reports/` `dtos/` が並ぶ。

`jobs_root` の既定は `<repo_root>/local_jobs/`。sqlite（`jobs.sqlite3`）も
ジョブディレクトリもこの配下に閉じ、ディレクトリごと gitignore する。

### 環境変数

いずれも未設定で動く（既定値はリポジトリ内に閉じる）。値の正本は
`runner_gateway/settings.py`（API 側）と `ui/api_client.py`（UI 側）。

| 変数 | 効く先 | 役割 |
|---|---|---|
| `IM_CABLE_SYSTEM_PYTHON` | API | runner を起動する python。未設定なら `<repo_root>/.venv/bin/python`、無ければ実行中の python |
| `IM_CABLE_SYSTEM_JOBS_ROOT` | API | ジョブディレクトリと sqlite の置き場所。相対値でも絶対パスへ解決して保持する |
| `IM_CABLE_SYSTEM_MAX_CONCURRENT_JOBS` | API | 同時実行数の上限（`asyncio.Semaphore`） |
| `IM_CABLE_SYSTEM_JOB_TIMEOUT_SECONDS` | API | ジョブ 1 本の壁時計タイムアウト（秒） |
| `IM_CABLE_SYSTEM_API_BASE_URL` | UI | Streamlit が叩く API の基点。API と UI を別ホスト・別ポートで動かすときに要る |

`jobs_root` は絶対パスで保持する。相対のままだと `--dump-base-dir` に相対パスが
載って engine が弾き、台帳の `job_dir` / `output_dir` を絶対パスとする契約
（下の DB スキーマ）も破れるため。

アップロードされた `config.yaml` に `dump.base_dir` が含まれていても、
config マテリアライズ時にそのキーを削除する（CLI 引数 `--dump-base-dir` を
優先させるため）。削除した事実は `run.log` 冒頭に記録する。

## ジョブの削除

終端（`succeeded` / `failed` / `cancelled`）のジョブだけ削除できる。
実行中（`queued` / `running`）は **409** で拒否する（先にキャンセルさせる）。
`DELETE /api/jobs/{job_id}` は `delete_job_dir` でジョブディレクトリを消し、
その後に台帳行を消す（逆順だと「行は無いのに実体が残る」孤児になる）。
`job_dir` が `jobs_root` 配下であることを `is_relative_to` で検証してから
`rmtree` する。

## 成果物の把握 — 走査のみ

`GET /api/jobs/{job_id}/artifacts` が `outputs/` を実行時に走査し、
`ArtifactInfo`（`kind` / `rel_path` / `size_bytes` / `modified_at`）を返す。
`kind` は `outputs/` からの相対パスの第 1 セグメント（`figures` / `tables` /
`reports` / `dtos`）。DB にもマニフェストにも持たないため、
`filename_pattern` や `sub_dir` を config でどう変えても追従不要である。

本体（`GET /api/jobs/{job_id}/artifacts/{rel_path}`）は、解決後のパスが
`output_dir` の配下であることを確認してから返す（パストラバーサル対策）。
`?disposition=inline|attachment` で `Content-Disposition` を切り替える
（省略時は `inline`。PNG の別タブ閲覧を保ち、`attachment` は保存専用）。

## store — ジョブ台帳（SQLAlchemy）

テーブルは `jobs` 1 枚のみ。配列・PNG・巨大 CSV は入れない。

| カラム | 型 | 備考 |
|---|---|---|
| `id` | TEXT PK | uuid4 hex |
| `mode` | TEXT | `estimate_params` / `forward_by_cartesian_grid` / `forward_by_operating_points` |
| `status` | TEXT | `queued` / `running` / `succeeded` / `failed` / `cancelled` |
| `created_at` / `started_at` / `finished_at` | TIMESTAMP | UTC で入れる。SQLite は tzinfo を保持しないため、`JobRecord` へ写す際に naive 値を UTC とみなして付け直す（tz-aware なのは DTO 側） |
| `job_dir` / `output_dir` | TEXT | 絶対パス |
| `exit_code` | INTEGER NULL | runner の終了コード |
| `error_kind` | TEXT NULL | `validation`(exit 2) / `unexpected`(exit 1) / `timeout` / `cancelled` / `interrupted` |
| `error_message` | TEXT NULL | `run.log` 末尾数行の要約 |
| `pid` | INTEGER NULL | 孤児検出用 |

層外は `IJobRepository` と `JobRecord`（DTO）越しにのみ台帳へ触る。ORM
モデル（`Job` / `Base`）は層外非公開。

スキーマ作成は起動時の `Base.metadata.create_all` だけで行い、マイグレーション
の仕組みは持たない。ローカル実行前提で `jobs_root` ごと捨てて作り直せるため。
スキーマを変えたら `local_jobs/` を消す（既存ジョブの履歴は失われる）。

## `engine_contract` — engine の入出力ファイル契約の写し

```text
apps/web/engine_contract/
├── __init__.py
├── model_kinds.py
├── estimate_params_input.py
├── im_yaml_contract.py
└── fit_report.py
```

`apps/` は engine を import しない。検証・結果表示に要る知識
（種別語彙・必須軸ラベル・YAML の形）はここに写す。写しが engine から離れたら
`tests/test_apps/test_web/engine_contract/test_engine_contract_drift.py` が落ちる
（`tests/` は engine を import してよい）。`api` だけがこれを使う。

## 投入時プリフライト

アップロード・プリセットいずれの入力も、内容の不整合は **422** で弾き、
ジョブを作らない（プリセットも `save_input_file` でアップロードと同じ経路に
載るため、契約検証も同じく通る）。必須入力の欠落・JSON 不正は従来どおり
**400**。同梱の既定パス（`RunnerGatewaySettings` の `*_default`）を直接使う
のは、アップロードもプリセット指定も無い場合だけであり、そのときだけ検証を
省略する（リポジトリ自身のファイルで、engine 側テストが担保している）。

検証する対象:

- `estimate_params` の統合入力: `model_candidate_axis` に
  `im_friction_windage` / `im_stray_load` があり、候補セルが空でないこと。
- `estimate_params` の統合入力: 各候補セルが、その軸で既知のモデル種別名で
  あること（語彙の写しは `engine_contract/model_kinds.py` の
  `CANDIDATE_AXIS_KINDS`）。engine は種別名の合法性を検証せず bounds YAML
  引きの `KeyError` にするため、ここで拾わないと利用者のタイポが
  `unexpected` として表示される（下の「エラーの伝え方」）。未知の**軸
  ラベル**は engine が `ValueError`（exit 2）にするので対象外。
- `im_bounds`: トップレベルに `friction_windage` / `stray_load` の
  `model_parameters` があること。
- `im_catalog`: 各 series に `friction_windage.model.name` /
  `stray_load.model.name` があり、既知の種別であること。

欠けている軸へ `NONE` を自動補完しない。「考慮しない」という判断をシステムが
黙って行わないため。ゼロ損失なら呼び出し側が `NONE` を明示する。

### ブロックしない警告

弾くほどではないが黙って進めたくない事象は、ジョブを作ったうえで投入レスポンスの
`warnings`（文字列の配列）に載せる。UI はこれを投入直後に表示する。422/400 と違い
**投入は成立する**ので、判断は利用者に残る。

現在の対象は、軸出力控除を推定する候補があるのに教師曲線が滑り $s \approx 0$ の
点を含む場合。この領域では軸出力が 0 に近づいて控除項の寄与が分離できず、
推定が不定になりやすい（`docs/model/curve_fitting_consistency.md`）。
判定に使う滑りの閾値は `apps` 側の表示ヒューリスティックであって、engine が
公開している数値ガードではない（正本は `engine_contract/estimate_params_input.py`
の定数とその docstring）。

## 軸出力控除の 2 軸

候補（`model_candidate_axis`）は統合入力 CSV、境界・初期値は `im_bounds`
YAML が正本であり、画面はどちらもプリセット選択で渡す（`apps/web/presets/input.yaml`）。
API 側は CSV 書き換えも境界上書きも行わない — 軸出力控除を変えたいときは
別の入力プリセットまたはアップロードファイルを選び直す。

結果表示は `GET /api/jobs/{job_id}/fit-summaries` が
`<output_dir>/reports/report_model_*.yaml` を全件読み、`FittedCatalogView`
へ写して name 昇順で返す（0 件は空リスト。DB にもマニフェストにも持たない）。

この経路だけは成果物一覧（走査のみ）と違い、**config の出力先とファイル名
パターンに張り付いている**。`reports` サブディレクトリ名と `report_model_*`
というパターンをアップロード config が変えると 0 件になり、画面には
「まだありません」としか出ない（設定違いと未生成を区別しない）。
プリセット config はこの前提を満たす。前提を外す config を許すなら、
成果物一覧と同じく走査へ寄せるのが筋で、パターンを増やして追随しない。
UI は組み合わせの比較表と selectbox で 1 件を選び、成果物一覧は選択中の
組み合わせ名で表示を絞る（表示層のヒューリスティック。API は走査結果を
絞らない）。出せるのはモデル名・推定係数・境界張り付き状態まで。この面は
engine が書き出した成果物を読むだけで、値を自前で再計算しない。動作点ごとの
$P_{FW}$ / $P_{\mathrm{stray}}$ 曲線のような engine が出力していない量を
出したくなった場合も、apps 側で計算せず engine の出力面を足す。

## api — FastAPI 窓口

| メソッド | パス | 役割 |
|---|---|---|
| POST | `/api/jobs/{mode}` | multipart 投入 → 202 `{job_id, status: "queued", warnings}`（`warnings` は「ブロックしない警告」節を見る） |
| GET | `/api/jobs` | 一覧（`mode` / `status` フィルタ、ページング） |
| GET | `/api/jobs/{job_id}` | 状態・時刻・終了コード・エラー・表示用 `timezone`（`config.yaml` の `project_info.timezone`。不正なら `UTC`） |
| GET | `/api/jobs/{job_id}/log` | `run.log` の末尾（`?tail_lines=N`） |
| GET | `/api/jobs/{job_id}/artifacts` | 走査結果 |
| GET | `/api/jobs/{job_id}/artifacts/{rel_path}` | ファイル本体（`?disposition=inline\|attachment`、省略時 `inline`） |
| GET | `/api/jobs/{job_id}/fit-summaries` | 全 `report_model_*.yaml` を name 昇順（0 件は空リスト）。`FitSummaryListResponse` |
| POST | `/api/jobs/{job_id}/cancel` | terminate → 猶予後 kill |
| DELETE | `/api/jobs/{job_id}` | 終端ジョブのみ削除（非終端は 409）。ディレクトリ → 台帳の順 |
| GET | `/api/config-presets` | `mode` 必須。その mode のプリセット名と YAML |
| GET | `/api/input-presets` | `mode` の入力ファイルプリセット（field ごと） |
| GET | `/healthz` | 死活 |

投入は必ず 202 で即返し、計算完了を待たない。UI は詳細エンドポイントを
ポーリングする。

`create_app`（`main.py`）はモジュール import 時点で DB へ触らないファクトリー
である。起動には `uvicorn apps.web.api.main:create_app --factory` を使う
（module-level に `app = create_app()` を置くと import するだけで既定の
`jobs_root` にディレクトリが作られてしまうため、あえて置いていない）。

### 実行と並行制御 — JobSupervisor

`api/supervisor.py` の `JobSupervisor` が、`asyncio.create_subprocess_exec` +
`asyncio.Semaphore(N)` + タスク登録簿で並行数を制限し、FastAPI と同じ
イベントループに乗せる。壁時計タイムアウトは apps 側
（`RunnerGatewaySettings.job_timeout_seconds`）が持つ。config の
`calculation.execute.data_processing.timeout_seconds` は `as_completed`
の待ち上限でありジョブ全体の上限ではなく、既定の `method: "sequential"`
ではそもそも効かないため、両者は無関係である。

`env` には `MPLBACKEND=Agg` を必ず設定する（未設定だと matplotlib の
ヘッドレス実行に失敗し figure 出力が落ちる）。

### 起動時の孤児ジョブ回収

サーバ再起動時、非終端（`queued` / `running`）のまま残っているジョブは実体の
subprocess もキュー待ちタスクも存在しないため、lifespan で `failed`
（`error_kind = "interrupted"`）へ倒す。再実行はユーザーが判断する
（嘘をつかない設計）。

`running` だけでは足りない。非終端の行は DELETE が 409 で拒むため、
`queued` のまま取り残すと UI からも API からも消せない行になる。同じ理由で、
**subprocess の起動自体に失敗した場合も `failed`（`unexpected`）へ倒す**
（`JobSupervisor._run` が `_execute` の例外を受ける）。倒し先の無い非終端を
作らない、が状態遷移の不変条件である。

### エラーの伝え方

engine には専用例外型が無い。ジョブの成否は例外型ではなく runner の終了コード
（0 / 1 / 2）だけで判断する: `exit_code == 2` は `error_kind = "validation"`、
それ以外の非 0 は `error_kind = "unexpected"`。ただし argparse の引数エラーも
exit 2 を返すため区別できず、`run.log` 末尾数行を `error_message` へ残して補う。

終了コードへの写像は runner 側が行う（正本は
`docs/architecture/shared/config_and_logger.md`）。`ValueError` が exit 2、
それ以外の例外が exit 1 なので、**engine が投げる `ValueError` 以外**
（bounds YAML のキー欠落に対する `KeyError`、設定ファイル不在の
`FileNotFoundError` など）は、原因が利用者の入力にあっても
`error_kind = "unexpected"` として表示される。この粒度で足りない入力不備は、
apps 側の投入時プリフライトで 422 として先に弾く方針を取る
（プリフライトを足す判断は上の「投入時プリフライト」節を見る）。

`model_candidate_axis` のモデル種別名はこの方針を適用済みで、タイポは投入時に
422 になる。engine 側に残る `KeyError` 経路は、apps が検証しない入力
（`im_bounds` の種別キー欠落など）に対する後段の網である。

## ui — Streamlit

`api_client.py` に `httpx` 呼び出しを閉じ込める（`ApiClient`）。
`st.cache_resource` で共有するのは `httpx.Client`（接続プール）であり、
`ApiClient` はリラン毎に作り直す。関数本体が変わらない限り
`cache_resource` は古いインスタンスを返すため、メソッド追加が反映されなくなる
のを避ける。`ApiClient` はプールを閉じるメソッドを持たない
（通常運用ではプロセス終了まで閉じない設計で、`st.fragment(run_every=...)`
はスクリプト全体を再実行しないため、リラン毎に閉じるとフラグメントが
閉じたクライアントを掴むことになる）。ページは
`pages/1_Submit_Job.py`（モード別投入フォーム: config と必須の入力ファイルは
「プリセット選択 / アップロード」の 2 択 radio、省略可の入力ファイルは
「使わない / プリセット選択 / アップロード」の 3 択で既定は「使わない」。
既定の mode は `forward_by_cartesian_grid`。config プリセットは選択中 mode に
連動し、必須の入力ファイルは既定でプリセット選択かつ先頭プリセットが
選ばれているため、画面を開いてアップロード 0 件のまま「投入する」で
投げられる）と
`pages/2_Jobs.py`（一覧は `st.dataframe` の単一行選択（左端の丸ボタン）。
一覧は非終端ジョブがある間だけ監視して自動更新する。投入直後のジョブは
Jobs 側で 1 回だけ引き継いで選択する。削除は一覧下のボタン → 確認帯 →
ジョブ削除 API。時刻はジョブの Config TZ 表示。終端まで
`st.fragment(run_every=...)` でポーリングし、ログ末尾・成果物一覧・
キャンセルを提供する。`estimate_params` 成功時は組み合わせの比較表と
selectbox、成果物の絞り込みを提供する。PNG は別タブ閲覧、DL は保存）。

## presets — サーバ同梱プリセット（実体コピーは持たない）

どちらのマニフェストも先頭に `version: 1` を持ち、残りが
`apps/web/presets/config.yaml` は `mode → [{name, path, description}]`、
`apps/web/presets/input.yaml` は `mode → field → [{name, path, description}]`
である（読み込み時に `version` を除いてから mode の辞書として扱う）。
`path` は `RunnerGatewaySettings.repo_root` からの相対パスで、
**実体コピーを持たず既存ファイルを指すだけ**である。各 mode（入力は各 field）
の先頭要素が UI の既定選択になる。

参照してよい先は次に限る。`tests/` は指さない。

- 入力: `examples/`・`src/im_cable_system/catalog/`・
  `src/im_cable_system/bounds_and_init/`
- config: `examples/config/`（README Quick Start と同一ソース）

config の YAML に残る catalog / bounds の相対参照と `dump.base_dir` は、
CLI 引数上書きと materialize 時のキー削除により**一度も解決されない**
（`_resolve_required_path` は override があれば YAML 側を見ない。上の
「catalog / bounds を必ず明示的に渡す」を参照）。

`config_preset_loader.py` / `input_preset_loader.py` が一覧・読み込みを行い、
読み込み時に解決後のパスが `repo_root` 配下であることを検証する
（`runner_gateway/artifacts.py` の `resolve_artifact_path` と同じ姿勢）。

投入時、`api/submission_form.py` の `SubmissionForm` がアップロードと
プリセット名（`{field}_preset`）の両方を同じ `FieldBytes` 経路で扱う。
`routes_jobs.py` は `SubmissionForm` を組み立てて呼ぶだけで、フォームの
読み取り自体は持たない。プリセットを選ぶと、その実ファイルはアップロードと
同じく `save_input_file` で `<job_dir>/inputs/` へコピーされる
（`examples/` が後で変わってもそのジョブの `cmd.json` が指すファイルは動か
ない）。アップロードとプリセットの同時指定は 400、未知のプリセット名も 400。

## 外部フレームワークの基底クラス継承（境界での例外）

`docs/conventions/2_design_principles.md` は実装継承を禁止するが、外部
フレームワークの基底クラスは境界での例外として許容する: `BaseModel`
（pydantic。`api/schemas.py` の DTO が継承）と `DeclarativeBase`
（SQLAlchemy。`store/models.py` の `Job` が継承）。engine 内には持ち込まない。

## やらないこと

- engine 層への Web 混入。`src/im_cable_system/` は変更しない。
- 同期計算。投入エンドポイントは常に 202 を返し、計算完了を待たない。
- 成果物の BLOB 化・成果物メタの二重管理（artifacts テーブルも
  manifest.json も作らない。走査のみ）。成果物 YAML を**表示目的で読む**ことは
  行う（DB には持たない）。
- Streamlit からの engine 直 import。
- `apps/` から engine 内部への直 import（契約の写しは `engine_contract` に閉じ、
  drift は `tests/` が検出する）。
- 認証・マルチテナント（ローカル単一ユーザー前提）。
