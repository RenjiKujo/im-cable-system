---
name: pj-run-tests
description: >-
  Runs pytest with the project venv from .venv_path. Reports results only; does not fix failures.
  Use when the user asks to run tests, smoke tests, or pre-PR checks.
disable-model-invocation: true
---

# pj-run-tests

## Python

ルートの `.venv_path`（先頭の非空行。相対パスはルート基準）が指す venv の
`bin/python`（Windows は `Scripts\python.exe`）だけ使う。
無い／壊れているなら実行せず、報告して確認を待つ。
素の `python` / `pytest` は使わない。

## 引数

ユーザー指定の解釈:

| 指定 | 実行 |
|---|---|
| `smoke` / `スモーク` / `通常` | `pytest -m "not slow" -q`（CI と同じ） |
| `all` / `全部` | `pytest -q`（slow 含む） |
| パス指定 | そのパスだけ |
| 空 | `pytest -m "not slow" -q` |
| 判断不能 | `pytest -m "not slow" -q` とし、解釈を報告する |

タイムアウト目安は 120 秒。重い推定テストは `all` のときだけ。

## 報告

- PASSED / FAILED
- 実行時間
- 件数の内訳
- 失敗時は原因の要約のみ。スタックトレース全文は出さない
- 失敗してもコードは直さない。報告だけ
