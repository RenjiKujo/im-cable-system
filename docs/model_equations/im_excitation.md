# IM 励磁（excitation）モデル係数と数式

$R_{m,0}$、$L_{m,0}$ は励磁支路の基準抵抗・基準インダクタンスから導く。$X_{m,0}=\omega L_{m,0}$。励磁支路は **並列**（アドミタンス加算）で合成する前提で、ここでは各支路の $R_m$、$X_m$（実部・虚部の対応する成分）を記す。

## BASIC

モデル固有係数はない。

**並列合成:**

$$\frac{1}{Z_m} = \frac{1}{R_{m,0}} + \frac{1}{\mathrm{j}X_{m,0}}$$

（等価的に $Z_m = \dfrac{R_{m,0}\cdot \mathrm{j}X_{m,0}}{R_{m,0} + \mathrm{j}X_{m,0}}$。）

## SLIP_DEPENDENT_SATURATION_V1

スリップ $s$ に対し、一次の SLIP 依存漏れと同型に、抵抗は線形、リアクタンスは $\tanh$ 飽和とする。

| 記号 | YAML キー |
|------|------------|
| $\alpha_r$ | `alpha_excitation_r` |
| $\alpha_x$ | `alpha_excitation_x` |
| $\beta_x$ | `beta_excitation_x` |

**抵抗:**

$$R_m(s) = R_{m,0}\,\bigl(1 + \alpha_r\, s\bigr)$$

**リアクタンス:**

$$X_m(s) = X_{m,0}\,\Bigl(1 - \alpha_x\,\tanh(\beta_x\, s)\Bigr)$$

**並列合成:**

$$\frac{1}{Z_m(s)} = \frac{1}{R_m(s)} + \frac{1}{\mathrm{j}X_m(s)}$$

（等価的に $Z_m(s) = \dfrac{R_m(s)\cdot \mathrm{j}X_m(s)}{R_m(s) + \mathrm{j}X_m(s)}$。）

## CURRENT_DEPENDENT_SATURATION_V1

励磁電流の大きさに依存する飽和。基準電流 $I_{m,0}$ は**銘牌電流（定格電流, A, `ImSeriesDto.nameplate_current`）** とし、$r_I = |I_m| / I_{m,0}$ とする。$I_{m,0} \le 0$ のときは正規化せず $r_I = |I_m|$ にフォールバックする。電流配列が未設定の初回ビルドでは $I_m = 0$（$r_I = 0$）として計算する。

| 記号 | YAML キー |
|------|------------|
| $\alpha_r$ | `alpha_excitation_r` |
| $\alpha_x$ | `alpha_excitation_x` |
| $\beta_x$ | `beta_excitation_x` |

（`SLIP_DEPENDENT_SATURATION_V1` と同一のキー。）

**抵抗:**

$$R_m(r_I) = R_{m,0}\,\bigl(1 + \alpha_r\, r_I\bigr)$$

**リアクタンス:**

$$X_m(r_I) = X_{m,0}\,\Bigl(1 - \alpha_x\,\tanh(\beta_x\, r_I)\Bigr)$$

**並列合成:**

$$\frac{1}{Z_m(r_I)} = \frac{1}{R_m(r_I)} + \frac{1}{\mathrm{j}X_m(r_I)}$$

（等価的に $Z_m(r_I) = \dfrac{R_m(r_I)\cdot \mathrm{j}X_m(r_I)}{R_m(r_I) + \mathrm{j}X_m(r_I)}$。）
