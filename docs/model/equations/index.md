# 等価回路モデルの数式 ↔ YAML キー ↔ 実装の対応

本プロジェクトの中核ドキュメント。誘導電動機（IM）＋ケーブル系の等価回路を、
**数式（理論）・モデル種別／係数名（DTO・Enum）・係数の境界／初期値（YAML）・実装（コード）が
1 対 1 で対応する**形で明文化する。新しい依存モデルを追加・推定するときの索引として使う。
各情報の「正（source of truth）」は次節を参照。

## 正（source of truth）

関心事ごとに正を分ける。三者は 1 対 1 で対応するが、改変時の起点は次のとおり。

- **モデル種別（Enum）と、各種別が要求する係数名**は、**shared の DTO / Enum を正**とする。
  YAML のキー・本ドキュメントの記号は、この DTO / Enum に後追いで合わせる（乖離させない）。
  - IM（primary / excitation / secondary）:
    `engine.shared.dto.generic.im_cable_system.im` の
    `Im{Primary,Excitation,Secondary}ModelType` と各 DTO の
    `get_required_parameter_names()`
  - ケーブル（conductor）:
    `engine.shared.dto.generic.im_cable_system.cable` の `ConductorModelType` と
    `CableConductorModelDto.get_required_parameter_names()`
- **係数の探索境界（bounds）・初期化（init）**は、次の 2 つの YAML を**正**とする。
  - IM: `src/im_cable_system/bounds_and_init/im_descriptor_bounds_and_init.yaml` の `<subsystem>.model_parameters`
  - ケーブル: `src/im_cable_system/bounds_and_init/cable_descriptor_bounds_and_init.yaml` の `conductor.model_parameters`
- 各モデル種別ごとの**数式と記号の定義**は、本ディレクトリの各 md（下表のリンク先）を正とする。

## 記号の共通前提

- $s$: スリップ（無次元）
- $f$: 周波数（Hz）
- $\omega = 2\pi f$
- $r_I = |I| / I_{\mathrm{ref}}$: 電流比（無次元。基準電流 $I_{\mathrm{ref}}$ は対象により異なる）
  - **IM（一次・励磁・二次）**: $I_{\mathrm{ref}}$ は当該シリーズの**銘牌電流（定格電流, A）**。実装は `ImSeriesDto.nameplate_current` を用いる。銘牌電流が $0$ 以下のときは正規化せず $r_I = |I|$ にフォールバックする。
  - **ケーブル導体**: $I_{\mathrm{ref}}$ は系の定格ではなく**固定正規化定数 100 A**（コード内固定値）。
- 抵抗・インダクタンスの基準値（$R_{\bullet,0}$, $L_{\bullet,0}$, $X_{\bullet,0}=\omega L_{\bullet,0}$）は、同定対象の `rl_parameters` および各区間・各巻線の定義に従う

## 三者対応表（数式 ↔ YAML キー ↔ 実装）

「モデル種別」列が YAML の `model_parameters` 直下の Enum キーそのもの。
「数式」列から各モデルの式・係数記号へ、「実装」列の `build_model/.../*_immittance_converter.py` へ辿る。

| 対象 | モデル種別（YAML Enum キー） | 数式 | 実装（`...build_model/` 以下） |
|------|------------------------------|------|--------------------------------|
| IM 一次 | `BASIC` | [im_primary.md#basic](im_primary.md#basic) | `build_im_model/im_component_immittance/primary/basic/` |
| IM 一次 | `SLIP_DEPENDENT_LEAKAGE_SATURATION_V1` | [im_primary.md](im_primary.md#slip_dependent_leakage_saturation_v1) | `.../primary/slip_dependent/` |
| IM 一次 | `CURRENT_DEPENDENT_LEAKAGE_SATURATION_V1` | [im_primary.md](im_primary.md#current_dependent_leakage_saturation_v1) | `.../primary/current_dependent/` |
| IM 励磁 | `BASIC` | [im_excitation.md#basic](im_excitation.md#basic) | `.../excitation/basic/` |
| IM 励磁 | `SLIP_DEPENDENT_SATURATION_V1` | [im_excitation.md](im_excitation.md#slip_dependent_saturation_v1) | `.../excitation/slip_dependent/` |
| IM 励磁 | `CURRENT_DEPENDENT_SATURATION_V1` | [im_excitation.md](im_excitation.md#current_dependent_saturation_v1) | `.../excitation/current_dependent/` |
| IM 二次 | `BASIC` | [im_secondary.md#basic](im_secondary.md#basic) | `.../secondary/basic/` |
| IM 二次 | `SLIP_DEPENDENT_SKIN_EFFECT_V1` | [im_secondary.md](im_secondary.md#slip_dependent_skin_effect_v1) | `.../secondary/slip_dependent/` |
| IM 二次 | `CURRENT_DEPENDENT_SKIN_EFFECT_V1` | [im_secondary.md](im_secondary.md#current_dependent_skin_effect_v1) | `.../secondary/current_dependent/` |
| IM 二次 | `CURRENT_DEPENDENT_LEAKAGE_SATURATION_V1` | [im_secondary.md](im_secondary.md#current_dependent_leakage_saturation_v1) | `.../secondary/current_dependent/` |
| IM 二次 | `CURRENT_DEPENDENT_SKIN_EFFECT_AND_LEAKAGE_SATURATION_V1` | [im_secondary.md](im_secondary.md#current_dependent_skin_effect_and_leakage_saturation_v1) | `.../secondary/current_dependent/` |
| ケーブル導体 | `BASIC` | [cable_conductor.md#basic](cable_conductor.md#basic) | `build_cable_model/conductor_immittance/basic/` |
| ケーブル導体 | `FREQUENCY_DEPENDENT_SKIN_EFFECT_V1` | [cable_conductor.md](cable_conductor.md#frequency_dependent_skin_effect_v1) | `.../conductor_immittance/frequency_dependent/` |
| ケーブル導体 | `CURRENT_DEPENDENT_SKIN_EFFECT_V1` | [cable_conductor.md](cable_conductor.md#current_dependent_skin_effect_v1) | `.../conductor_immittance/current_dependent/` |
| IM 摩擦・風損 | `NONE` | [im_friction_windage.md](im_friction_windage.md#none) | `simulate/power/calculate_im_shaft_output_deduction/friction_windage/` |
| IM 摩擦・風損 | `CONSTANT_V1` | [im_friction_windage.md](im_friction_windage.md#constant_v1) | `.../friction_windage/` |
| IM 漂遊負荷損 | `NONE` | [im_stray_load.md](im_stray_load.md#none) | `simulate/power/calculate_im_shaft_output_deduction/stray_load/` |
| IM 漂遊負荷損 | `CURRENT_DEPENDENT_QUADRATIC_V1` | [im_stray_load.md](im_stray_load.md#current_dependent_quadratic_v1) | `.../stray_load/` |

> 実装ディレクトリの基点は
> `src/im_cable_system/engine/algorithm/execute_algorithm/build_model/`。
> どの種別を生成するかは各 `factory_*_immittance_converter.py` が Enum キーで分岐する。
> **例外**: IM 摩擦・風損／漂遊負荷損の 2 サブシステムは
> **イミタンス（インピーダンス・アドミタンス）を持たない**。並列・直列合成の対象にならず、
> 実装は `build_model/` ではなく
> `engine/algorithm/execute_algorithm/simulate/power/calculate_im_shaft_output_deduction/` に置く
> （電力計算段で二次負荷電力から直接減算するため）。

## 二重かご（DOUBLE_CAGE）の扱い

- **選択軸はモデル種別ではなく `cage_multiplicity`（`SINGLE_CAGE` / `DOUBLE_CAGE`）** である。
  ビルダー（`factory_im_model_builder.py`）・電圧電流計算器（`factory_im_voltage_current_calculator.py`）・電力計算器（`factory_im_power_calculator.py`）はいずれも `cage_multiplicity` で `Single*` / `Double*` を分岐する。
- 二重かごでは内かご（INNER）・外かご（OUTER）を**独立した二次枝**として扱い、各枝は**通常の二次モデル**（`BASIC` / `SLIP_DEPENDENT_*` / `CURRENT_DEPENDENT_*`）の式・コンバーターで計算する。枝二次アドミタンスを並列合成して等価二次 $Y_{2,\mathrm{eq}} = Y_{2,\mathrm{inner}} + Y_{2,\mathrm{outer}}$ を得る（`double_cage_im_total_immittance_synthesizer.py`）。
- 二重かご固有の二次モデル種別（推定（estimate_params）でも内かご・外かごの候補軸（`im_secondary(double_inner)` / `im_secondary(double_outer)`）に**通常の二次モデル種別**を指定する。

## 実装上の共通注意（数式に明示されない挙動）

- **数値安定化クランプ**: 各イミタンス変換・合成は Config 由来の `eps` / `max_mag`（$=1/\mathrm{eps}$）で極小・極大をクランプする。特に二次モデルでは $s \le \mathrm{eps}$ を検出し、負荷支路 $R_2(1-s)/s$ と総合 $R_2/s$ の実部を `max_mag` にクランプして発散を防ぐ。
- **電流依存モデルの初回ビルド**: 電流配列が未設定（初回ビルド等）の場合は、参照形状の**ゼロ電流**として計算する（$r_I = 0$）。実際の電流は反復で確定後に再計算される。

## モデル別ドキュメント

| 対象 | ファイル | 内容 |
|------|----------|------|
| IM 一次（primary） | [im_primary.md](im_primary.md) | 直列インピーダンス。漏れ飽和（slip / 電流依存）。 |
| IM 励磁（excitation） | [im_excitation.md](im_excitation.md) | 並列アドミタンス合成。飽和（slip / 電流依存）。 |
| IM 二次（secondary） | [im_secondary.md](im_secondary.md) | 負荷支路 $(1-s)/s$、表皮効果、漏れ飽和、二重かご。 |
| ケーブル導体（conductor） | [cable_conductor.md](cable_conductor.md) | π型導体区間の表皮効果（周波数 / 電流依存）。 |
| IM 摩擦・風損（friction_windage） | [im_friction_windage.md](im_friction_windage.md) | 定格入力比例の一定損失。イミタンスを持たない。 |
| IM 漂遊負荷損（stray_load） | [im_stray_load.md](im_stray_load.md) | 二次電流比の2乗に比例。イミタンスを持たない。 |
