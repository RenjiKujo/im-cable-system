# ケーブル導体（conductor）モデル係数と数式

$R_{c,0}$、$L_{c,0}$ は導体区間全体の合成基準抵抗・基準インダクタンスから導く。$X_{c,0}=\omega L_{c,0}$。

$f$ は周波数（Hz）、$\omega = 2\pi f$。ここでは導体支路の抵抗・リアクタンスを $R_c$、$X_c$（いずれも Ω）と書く。直列合成 $Z = R_c + \mathrm{j}X_c$ のもとで表皮スケールを適用する。

> **スコープ**: 本ファイルは π 型ケーブルの**導体支路**の式のみを扱う。ケーブルが複数区間からなる場合、各区間の導体インピーダンスは**直列合成**される（`pie_cable_model_builder.py`）。アース（シャント）支路 $R \parallel 1/(\mathrm{j}\omega C)$ と区間間の**並列合成**は本ファイルの対象外（実装は `line_density_impedance_converter.py` を参照）。

## BASIC

モデル固有係数はない。直列インピーダンスは次式とする。

**抵抗:**

$$R_c = R_{c,0}$$

**リアクタンス:**

$$X_c = X_{c,0}$$

**直列合成:**

$$Z = R_c + \mathrm{j}X_c$$

## FREQUENCY_DEPENDENT_SKIN_EFFECT_V1

周波数正規化定数を $f_\mathrm{ref}=50\,\mathrm{Hz}$ とし、比 $r_f = f / f_\mathrm{ref}$ を用いる。$r_f$ に対し、抵抗・リアクタンスに指数型の表皮スケールを付与する。

$f_\mathrm{ref}$ は系統固有の定格周波数ではなく、無次元化のための固定正規化定数（コード内固定値）である。$\beta_r$、$\beta_x$ が推定対象として周波数スケールを吸収する。

| 記号 | YAML キー |
|------|------------|
| $f_\mathrm{ref}$ | 正規化定数（固定値 50 Hz、推定対象外） |
| $\alpha_r$ | `alpha_conductor_r` |
| $\beta_r$ | `beta_conductor_r` |
| $\alpha_x$ | `alpha_conductor_x` |
| $\beta_x$ | `beta_conductor_x` |

**抵抗:**

$$R_c(r_f) = R_{c,0}\,\Bigl(1 + \alpha_r\,\bigl(1 - e^{-\beta_r\, r_f}\bigr)\Bigr)$$

**リアクタンス:**

$$X_c(r_f) = X_{c,0}\,\Bigl(1 - \alpha_x\,\bigl(1 - e^{-\beta_x\, r_f}\bigr)\Bigr)$$

**直列合成:**

$$Z(r_f) = R_c(r_f) + \mathrm{j}X_c(r_f)$$

## CURRENT_DEPENDENT_SKIN_EFFECT_V1

電流正規化定数を $I_\mathrm{ref}=100\,\mathrm{A}$ とし、$r_I = |I_c| / I_\mathrm{ref}$ とする。$r_I$ に対し、抵抗・リアクタンスに指数型の表皮スケールを付与する。$R_{c,0}$、$X_{c,0}$ の定義は冒頭と同じとする。

$I_\mathrm{ref}$ はケーブル固有の定格電流ではなく、無次元化のための固定正規化定数である。$\beta_r$、$\beta_x$ が推定対象として電流スケールを吸収するため、ケーブルカタログに定格電流が無い場合でも本モデルを使用できる。導体電流が未設定の初回ビルドでは $I_c = 0$（$r_I = 0$）として計算する。

| 記号 | YAML キー |
|------|------------|
| $I_\mathrm{ref}$ | 正規化定数（固定値 100 A、推定対象外） |
| $\alpha_r$ | `alpha_conductor_r` |
| $\beta_r$ | `beta_conductor_r` |
| $\alpha_x$ | `alpha_conductor_x` |
| $\beta_x$ | `beta_conductor_x` |

（`FREQUENCY_DEPENDENT_SKIN_EFFECT_V1` と同一のキー。）

**抵抗:**

$$R_c(r_I) = R_{c,0}\,\Bigl(1 + \alpha_r\,\bigl(1 - e^{-\beta_r\, r_I}\bigr)\Bigr)$$

**リアクタンス:**

$$X_c(r_I) = X_{c,0}\,\Bigl(1 - \alpha_x\,\bigl(1 - e^{-\beta_x\, r_I}\bigr)\Bigr)$$

**直列合成:**

$$Z(r_I) = R_c(r_I) + \mathrm{j}X_c(r_I)$$
