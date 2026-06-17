# シミュレーションロジック設計 - Domain層設計方針

## 概要

本ドキュメントは、本シミュレーションエンジンにおけるDomain層（`src/im_cable_system/engine/domain/`）の構成と設計方針を定義する。
Domain層は、シミュレーションエンジンにおけるビジネスロジック（計算、チェック、バリデーション）を提供する。

シミュレーション層固有のDTO設計方針については、`1_shared.md`を参照してください。

## Domain層の設計原則

### 一貫性の原則
- 同じレベルのドメインクラスは同じ設計原則に従う
- ドメイン横断で共通利用される計算ロジックは一貫した命名規則と構造を持つ

### 責務分離の原則
- **`numerics/`**: 配列・数値演算のユーティリティ（ブロードキャストなど、計算ドメインに依らない汎用処理）
- **`physics/`**: 物理計算（電気回路の法則・インピーダンス/アドミタンス合成・電力計算・特性値計算など）
- **`predicate/`**: 状態・条件の判定処理（`bool`を返す。例: cable / im の種別・条件判定）
- **`validation/`**: 物理法則・制約に基づく検証（複数のDTOにまたがる検証、例外を発生させる）

**`predicate/`と`validation/`の役割分担**:
- **`predicate/`**: 計算処理中の分岐判定に使用。単一DTOまたは少数のDTOに対する状態・条件判定を行い、判定結果は`bool`型で返す。
- **`validation/`**: 計算処理後の結果検証に使用。複数のDTOにまたがる物理法則・制約の検証を行い、検証失敗時は例外を発生させる。

### 拡張性の原則
- 新規ドメインはオプショナル属性として追加し、既存コードへの影響を最小化
- ドメインの実装状況に応じて段階的に統合可能

## Domain層のパッケージ構成とフォルダ管理方針

Domain層は、責務ごとにパッケージ（フォルダ）を分割する。フォルダ構成は、**「何のドメインロジックか」が一目で分かる単位**で分割する。

### 依存関係の原則

- `numerics/`: 最基底。他のドメイン層から参照されるが、他のドメイン層を参照しない
- `physics/`: `numerics/`を参照することがあるが、その逆はない
- `predicate/`: 下位（`numerics/`等）を参照することがあるが、その逆はない
- `validation/`: 下位（`physics/`・`numerics/`等）を参照することがあるが、その逆はない

### パッケージ構成（Domain層）

```
src/im_cable_system/engine/domain/
├── numerics/      … 配列・数値ユーティリティ
├── physics/       … 物理計算（electrical 配下に circuit_laws / immittance / power / voltage_current、characteristic）
├── predicate/     … 状態・条件判定（cable / im）
└── validation/    … 物理・制約検証（energy_conservation / im_rated_value）
```

**インポート**: [`docs/rules/layering_and_imports.md`](../rules/layering_and_imports.md) を参照する。

## Domain層の実装原則

### 関数ベースの実装

Domain層は、呼び出しを簡単にし、シンプルに設計するため、**主に関数で実装**される。

- **関数**: 純粋関数として実装し、DTOを引数として受け取り、計算結果をDTOとして返す
- **クラス**: 状態を保持する必要がある場合や、複数の処理をまとめる必要がある場合のみ使用

**関数の例**:
```python
def solve_kirchhoff_current(
    voltage: ArrayComplexVoltageDto,
    admittance: ArrayComplexAdmittanceDto,
) -> ArrayComplexCurrentDto:
    """キルヒホッフの電流則に基づいて電流を計算する。"""
    # ...

def power_from_voltage_and_current(
    voltage: ArrayComplexVoltageDto,
    current: ArrayComplexCurrentDto,
) -> ArrayComplexPowerDto:
    """電圧と電流から電力DTOを生成する。"""
    # ...
```

**クラスの例**（状態を保持する必要がある場合）:
```python
class ITimeSeriesAggregator(ABC):
    """時系列データの集約処理を行うインターフェース。"""
    @abstractmethod
    def aggregate(self, data: TimeSeriesDto) -> AggregatedDto:
        pass
```

### 計算ロジックの責務

Domain層の計算ロジックは、以下の原則に従う。

- **単一責任の原則**: 1つの関数・クラスは1つの責務のみを持つ
- **純粋関数の推奨**: 可能な限り、副作用のない純粋関数として実装する
- **テスト容易性**: テストしやすいように、依存関係を最小限に抑える

### 設定値注入の原則（Domain層）

Domain層では、設定ファイルや設定管理オブジェクトへの依存を持たせない。
設定値の解決は上位層（Algorithm / Orchestrator / Builder）で行い、Domain層には
プリミティブ値・Enum・DTOとして注入する。

- **原則**: Domain層は `Config` / YAMLキー構造に依存してはならない
- **設定解決の責務**: Algorithm / Orchestrator / Builder層で設定を読み取り、Domainへ値を渡す
- **ドメイン既定値**: Domain層に `EPS` / `MAX_MAG` などの既定定数を置くことは許容する
- **運用上書き**: 設定による上書きは上位層で行い、Domain関数・Domainクラスへ引数として注入する
- **テスト方針**: Domainテストでは `Config` を使わず、必要な数値を直接与えて検証する

**例**:
- NG: Domain関数内で `config.get(...)` を呼び出す
- OK: 上位層で `slip_eps`, `slip_max_magnitude` を解決してDomainへ渡す

### バリデーションの責務分離

Domain層とAlgorithm層のバリデーション責務は以下のように分離する。

- **Domain層（`validation/`）の責務**:
  - 汎用DTOのバリデーション（単一DTOの妥当性チェック）
  - 物理法則に基づく汎用的な検証関数（エネルギー保存則、電流・電圧レンジなど）
  - 複数のDTOを受け取り、物理法則・制約に基づく検証を行う関数
  - 検証失敗時は例外（`ValueError`など）を発生させる

- **Algorithm層（Validatorインターフェイス）の責務**:
  - 各シミュレーション固有のバリデーション（複数のITmDtoを組み合わせた検証など）
  - Domain層の検証関数を呼び出して、シミュレーション結果全体の妥当性を検証
  - configに基づく検証の有効/無効制御や重大度レベル（ERROR/WARNING/IGNORE）の管理
  - 検証のオーケストレーション（検証順序の制御など）

**例**:
- Domain層: `validate_energy_conservation(input_power, output_power, loss_power)` - 汎用的なエネルギー保存則の検証関数
- Algorithm層: `IEnergyConservationValidator.validate(itm_dto)` - ITmDtoから必要なDTOを抽出し、Domain層の関数を呼び出す

## Domain層とDTO層の関係

Domain層は、DTO層（汎用DTO、シミュレーション層固有DTO）を参照する。

**依存関係**:
- Domain層 → 汎用 DTO（`common.dto`）、設定インターフェイス（`shared.config`）
- DTO層 → Domain層（依存しない）

**インポート**: [`docs/rules/layering_and_imports.md`](../rules/layering_and_imports.md) を参照する。
