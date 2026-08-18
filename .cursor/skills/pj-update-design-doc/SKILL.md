---
name: pj-update-design-doc
description: >-
  Syncs docs/ with src/im_cable_system without changing design philosophy.
  Use when the user asks to update design docs to match code.
argument-hint: "docs/<file>"
context: fork
---

# pj-update-design-doc

コードと `docs/` の差分を洗い、必要なら設計文書を更新する。

これは **docs を書く**唯一の経路で、レビュー 2 体（`pj-review-code` /
`pj-review-docs`）とは軸が違う。あちらは報告だけで直さない。専用エージェントは
持たず、本文がそのまま手順の正本になる。

`context: fork` は Cursor 固有で、Claude Code は解釈しない
（Claude Code ではメインコンテキストで手順が走る）。

**`disable-model-invocation` は意図的に付けない。** 6 スキルのうち本スキルだけは
ユーザーの明示なしに起動してよい（`.cursor/rules/git.mdc`）。付けるとモデルからは
起動できなくなり、方針と食い違う。

対象（ユーザーがパスを指定すればそれを優先。空なら直近のコード変更に近い範囲）:

- `docs/README.md`（俯瞰・目次）
- `docs/architecture/`（層別。algorithm / shared のサブツリー含む）
- `docs/model/`（equations / curve_fitting_consistency を含む）
- `docs/conventions/`（規約が変わったときだけ）

## 手順

1. 着手前に読む文書は `.cursor/rules/consistency_check.mdc` の節 0 に従う
   （必読リストをここに再掲しない。二重管理は drift 源になる）
2. 既存 docs を読む
3. 対応する `src/im_cable_system/` を読む
4. 差分リストを作る。大きな変更はリストにしてユーザー確認を求める
5. 更新する（クラス単位の処理詳細は書かない。コードに委ねる）
6. `.venv/bin/python -m pytest tests/test_docs/ -q` を回す
   （リンク切れ・パス実在・ツリー整合・識別子実在・`docs/model/equations/` の
   3 者契約を機械検出する）
7. 変更ファイルとテスト結果を報告する

`docs/model/equations/` のモデル種別・係数を追加改名したときは `tests/test_docs/` 側の
更新も要る。**その旨を報告に明記する。**

## 書き方

- 既存見出しの粒度・構成に従う
- ディレクトリツリーは実構成に合わせ、役割コメントを付ける
- シグネチャはコードから正確に写す（メソッド名・引数名・戻り値型を grep で確認する）
- 数式は `$...$` / `$$...$$`。識別子・シンボルはソースどおり
- 日本語。事実だけ書く。推測しない
- **読んだ範囲だけを書く。** 部分的にしか読んでいない実装について断定しない。
  未確認のまま「〜である」と書かず、確認するか、書かない

## 禁止

- 設計思想・方針の変更。コードが思想から外れていたら、docs をコードに合わせて
  思想を曲げず**警告する**
- 根拠なくドキュメントを増やすこと。`reference/` 相当の外部資料の丸写しで
  独立ドキュメントを作らない
- **実装状況（未実装・未定・「現時点では対象外」等）を書くこと。**
  設計判断だけを書く。理由と実例は
  [`docs/README.md`](../../../docs/README.md) の「ドキュメント更新時の注意」を参照
