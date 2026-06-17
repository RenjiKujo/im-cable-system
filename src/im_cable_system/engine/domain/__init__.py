"""Domain 層（物理法則・汎用数値計算・状態判定・契約検証）。

サブパッケージごとに責務を分けている:

- ``physics``: IM＋ケーブル系のドメイン物理計算（DTO→DTO）。
- ``numerics``: ドメイン知識を持たない数値計算ユーティリティ。
- ``predicate``: DTO の状態分類用の述語（DTO→bool）。
- ``validation``: ドメイン契約の検証（DTO→ValidationResultDto）。

層外から利用する公開窓口:

- 物理量計算（電気）: ``im_cable_system.engine.domain.physics.electrical``
- 物理量計算（機器特性）: ``im_cable_system.engine.domain.physics``
- 数値計算ユーティリティ: ``im_cable_system.engine.domain.numerics``
- 状態判定: ``im_cable_system.engine.domain.predicate``
- 契約検証: ``im_cable_system.engine.domain.validation``

Note:
    本パッケージルートは束ね用であり、層外からここを import 窓口にしない。

設計方針:
    Domain 層の関数は **関数ごとの独立性** を優先し、横断的な共通 helper を
    あえて作らない方針とする。

    理由:
        Domain 層は「物理式 + DTO 変換 + 数値安定化」を担う層であり、
        一見似た処理（shape 検証・極小極大マスク・クランプ・イベント記録）
        も、関数ごとに物理的意味やクランプ後の値が異なることが多い。
        共通 helper に逃がすと、誤用や仕様変更時の事故が広範囲に波及するため、
        各関数内で完結させて読みやすさ・変更影響範囲の局所性を取る。

    許容するトレードオフと対応方針:

    - 似た処理が各関数に重複する → 許容する。
      （関数単体で読めばロジックが完結することを優先する。）

    - 方針変更に弱い（例: ``eps`` の値を全体で変えたい等）
      → Domain 関数は ``eps`` / ``max_mag`` を **キーワード必須引数**として
      受け取り、**アルゴリズム層が Config から取得して注入する**。
      Domain 側で既定値・共通定数を持たない（``_DEFAULT_EPS`` /
      ``_DEFAULT_MAX_MAG`` は撤廃済み）。

      NOTE:
          既定値を撤廃したことで「Config 由来の設定値か Domain の
          暗黙既定値か」の曖昧さがなくなり、アルゴリズム層での注入忘れは
          呼び出し時の ``TypeError`` で検出できる。テストからは
          ``tests/test_domain/conftest.py`` の ``TEST_EPS`` /
          ``TEST_MAX_MAG`` を明示注入する。

    - 微妙な不一致が入りやすい（``<= eps`` vs ``< eps`` 等）
      → コードレビューおよびテストでの精査で対応する。

    新しい関数を追加するときは、同パッケージ内の既存関数と同じ処理手順
    （shape 検証 → 極小極大検出 → イベント記録 → 計算 → クランプ → DTO 化）
    を踏襲し、共通 helper には抽出しないこと。
"""
