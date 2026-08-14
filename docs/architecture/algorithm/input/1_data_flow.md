# Inputアルゴリズムデータフロー

## 概要

Input アルゴリズムは、ジョブ仕様を受け取り、`build_input_dto` を入口として `InputDto` / `InputDtos` を返す。実行モードごとのオーケストレーターが同じ 4 段フローを共有する。

詳細な責務境界は [`2_component.md`](./2_component.md)、各段がいつ raise するかは [`3_design_principles.md`](./3_design_principles.md) を参照。

## 4 段フロー

```mermaid
flowchart LR
  spec[JobSpec]
  validateSpec[_validate_job_spec]
  load[_load_data]
  assemble[_assemble_input_dto]
  validateDto[_validate_input_dto]
  output[InputDto / InputDtos]

  spec --> validateSpec
  validateSpec --> load
  load --> assemble
  assemble --> validateDto
  validateDto --> output
```

1. `_validate_job_spec`: ファイルを開く前に、パスの存在や必須フィールドの非空など、軽量に確認できる項目だけを検証する。
2. `_load_data`: ファイルを読み、`LoadedData` を構築する。ファイル構造の破綻（ヘッダ欠落、変換失敗、カタログキー未登録など）でのみ raise する。
3. `_assemble_input_dto`: `LoadedData` から `InputDto` を組み立てる。フィールド単体の値域・単位などの契約は各 DTO の `__post_init__` が担う。
4. `_validate_input_dto`: 組み立て済み DTO に対して、構造整合・単位整合・DTO 横断整合・物理関係式などを意図的に重く検証する。

## モード別の流れ

- **forward**: `ForwardJobSpec`（パス束）→ 単一 `InputDto`。CartesianGrid / OperatingPoints の差は `reference_axes` の選び方だけで、フロー自体は共通である。
- **estimate_params**: 統合 TSV を 1 回パースし、候補軸（一次・励磁・二次・導体など）の直積に展開して複数 `InputDto` を構築し、`InputDtos` にまとめる。

直積を展開するループは Loader に閉じ、組み立て・検証の複数件ループはオーケストレーターが持つ。これにより Assembler / Validator は「1 件 → 1 件」の単純な契約を保てる。
