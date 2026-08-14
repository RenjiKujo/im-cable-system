---
name: pj-update-design-doc
description: >-
  Syncs docs/ with src/im_cable_system without changing design philosophy.
  Use when the user asks to update design docs to match code.
disable-model-invocation: true
argument-hint: "docs/<file>"
allowed-tools: Read Glob Grep Edit Write
context: fork
agent: design-doc-writer
---

# pj-update-design-doc

コードと `docs/` の差分を洗い、必要なら設計文書を更新する。
方針の正本は `.cursor/agents/design-doc-writer.md`。先に Read して従う。

対象（ユーザーがパスを指定すればそれを優先。空なら直近のコード変更に近い範囲）:

- `docs/README.md`（俯瞰・目次）
- `docs/architecture/`（層別。algorithm / shared のサブツリー含む）
- `docs/model_equations/`
- `docs/conventions/`（規約が変わったときだけ）
- `docs/estimate_params_curve_fitting_consistency.md`（該当するとき）

## 手順

1. 既存 docs を読む
2. 対応する `src/im_cable_system/` を読む
3. 差分リストを作る
4. 更新する（クラス処理の詳細は書かない）
5. `.venv/bin/python -m pytest tests/test_docs/ -q` を回す
   （`design-doc-writer` は Bash を持たないため、検証は呼び出し側の責務）
6. 変更ファイルとテスト結果を報告する

## 方針

- 設計思想は変えない
- コードが思想から外れていたら警告し、docs をコードに合わせて思想を曲げない
- 根拠なくファイルを増やさない
- 大きな変更はリストにしてユーザー確認を求める
