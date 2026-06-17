# IM 一次（primary）モデル係数と数式

$R_{1,0}$、$L_{1,0}$ は一次の基準抵抗・基準インダクタンスから導く。$X_{1,0}=\omega L_{1,0}$。

## BASIC

モデル固有係数はない。直列インピーダンスは次式とする。

**直列合成:**

$$Z = R_{1,0} + \mathrm{j}\,X_{1,0}$$

## SLIP_DEPENDENT_LEAKAGE_SATURATION_V1

スリップ $s$ に対し、抵抗は線形補正、リアクタンスは $\tanh$ 型の飽和を付与する。

| 記号 | YAML キー |
|------|------------|
| $\alpha_r$ | `alpha_primary_r` |
| $\alpha_x$ | `alpha_primary_x` |
| $\beta_x$ | `beta_primary_x` |

**抵抗:**

$$R_1(s) = R_{1,0}\,\bigl(1 + \alpha_r\, s\bigr)$$

**リアクタンス:**

$$X_1(s) = X_{1,0}\,\Bigl(1 - \alpha_x\,\tanh(\beta_x\, s)\Bigr)$$

**直列合成:**

$$Z(s) = R_1(s) + \mathrm{j}\,X_1(s)$$

## CURRENT_DEPENDENT_LEAKAGE_SATURATION_V1

一次電流の大きさに応じた漏れ飽和。基準電流 $I_{1,0}$ は**銘牌電流（定格電流, A, `ImSeriesDto.nameplate_current`）** とし、$r_I = |I_1| / I_{1,0}$ とする。$I_{1,0} \le 0$ のときは正規化せず $r_I = |I_1|$ にフォールバックする。電流配列が未設定の初回ビルドでは $I_1 = 0$（$r_I = 0$）として計算する。

| 記号 | YAML キー |
|------|------------|
| $\alpha_{\ell}$ | `alpha_primary_leakage_x` |
| $\beta_{\ell}$ | `beta_primary_leakage_x` |

**抵抗:**

$$R_1 = R_{1,0}$$

**リアクタンス:**

$$X_1(r_I) = X_{1,0}\,\Bigl(1 - \alpha_{\ell}\,\tanh(\beta_{\ell}\, r_I)\Bigr)$$

**直列合成:**

$$Z(r_I) = R_{1,0} + \mathrm{j}\,X_1(r_I)$$
