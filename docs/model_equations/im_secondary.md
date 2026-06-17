# IM 二次（secondary）モデル係数と数式

$s$ はスリップ、$\omega = 2\pi f$。$R_{2,0}$ は二次の基準抵抗（実部、Ω）。$X_{2,0} = \omega L_{2,0}$ は二次の基準リアクタンス（Ω）。電流比は $r_I = |I_2| / I_\mathrm{rated}$ とする（$I_\mathrm{rated}$ は銘牌電流（A, `ImSeriesDto.nameplate_current`）。$I_\mathrm{rated} \le 0$ のときは正規化せず $r_I = |I_2|$）。

> **実装上の注意**:
> - **slip 近接ゼロ**: $s \le \mathrm{eps}$ の要素は負荷支路 $R_2(1-s)/s$・総合 $R_2/s$ の実部を `max_mag`（$=1/\mathrm{eps}$）にクランプし、数値安定化イベントを記録する。
> - **電流依存モデルの初回ビルド**: 二次電流が未解決のときは $I_2 = 0$（$r_I = 0$）として計算し、反復で電流確定後に再計算する。

## BASIC

一次簡化かごに相当する。表皮・飽和の追加係数はない。

**抵抗:**

$$R_2 = R_{2,0}$$

**リアクタンス:**

$$X_2 = X_{2,0}$$

**基本支路:**

$$Z_\mathrm{base} = R_{2,0} + \mathrm{j}\,X_{2,0}$$

**負荷支路（純実部）:**

$$Z_\mathrm{load} = R_{2,0}\,\frac{1-s}{s}$$

**合成:**

$$Z_\mathrm{tot} = \frac{R_{2,0}}{s} + \mathrm{j}\,X_{2,0}$$

## 二重かご（DOUBLE_CAGE）の等価二次

二重かごは二次モデル種別ではなく `cage_multiplicity = DOUBLE_CAGE` で選択する（[index.md](index.md#二重かごdouble_cageの扱い) を参照）。内かご（INNER）・外かご（OUTER）を**独立した二次枝**として扱い、各枝は**通常の二次モデル**（`BASIC` / `SLIP_DEPENDENT_*` / `CURRENT_DEPENDENT_*`）のコンバーターで計算する。二重かご専用の二次モデル種別は存在しない。

以下では各枝が BASIC の場合を例に、枝ごとの二次インピーダンスと並列合成を示す（他種別の枝でも合成手順は同じ）。枝 $b \in \{\mathrm{inner}, \mathrm{outer}\}$ に対し、BASIC と同形の式で枝ごとの二次インピーダンスを定める。

**枝ごとの抵抗・リアクタンス:**

$$R_{2,b} = R_{2,b,0}$$

$$X_{2,b} = X_{2,b,0}$$

**枝ごとの基本支路:**

$$Z_{\mathrm{base},b} = R_{2,b,0} + \mathrm{j}\,X_{2,b,0}$$

**枝ごとの負荷支路（純実部）:**

$$Z_{\mathrm{load},b} = R_{2,b,0}\,\frac{1-s}{s}$$

**枝ごとの合成:**

$$Z_{\mathrm{tot},b} = \frac{R_{2,b,0}}{s} + \mathrm{j}\,X_{2,b,0}$$

**二重かごの等価二次:**

総合回路の合成では、内かご・外かごの二次枝を並列合成して等価二次イミタンスを得る。

$$Y_{2,\mathrm{eq}} = \frac{1}{Z_{\mathrm{tot},\mathrm{inner}}} + \frac{1}{Z_{\mathrm{tot},\mathrm{outer}}}$$

$$Z_{2,\mathrm{eq}} = \frac{1}{Y_{2,\mathrm{eq}}}$$

以降の総合合成では、単一かごの $Z_2$、$Y_2$ を $Z_{2,\mathrm{eq}}$、$Y_{2,\mathrm{eq}}$ に置き換える。

## SLIP_DEPENDENT_SKIN_EFFECT_V1

スリップに対する指数型表皮スケール。$R_2(s)$、$X_2(s)$ を定めたうえで、BASIC と同形の負荷項・合成を用いる。

| 記号 | YAML キー |
|------|------------|
| $\alpha_r$ | `alpha_secondary_r` |
| $\beta_r$ | `beta_secondary_r` |
| $\alpha_x$ | `alpha_secondary_x` |
| $\beta_x$ | `beta_secondary_x` |

**抵抗:**

$$R_2(s) = R_{2,0}\,\Bigl(1 + \alpha_r\,\bigl(1 - e^{-\beta_r\, s}\bigr)\Bigr)$$

**リアクタンス:**

$$X_2(s) = X_{2,0}\,\Bigl(1 - \alpha_x\,\bigl(1 - e^{-\beta_x\, s}\bigr)\Bigr)$$

**基本支路:**

$$Z_\mathrm{base}(s) = R_2(s) + \mathrm{j}\,X_2(s)$$

**負荷支路（純実部）:**

$$Z_\mathrm{load}(s) = R_2(s)\,\frac{1-s}{s}$$

**合成:**

$$Z_\mathrm{tot}(s) = \frac{R_2(s)}{s} + \mathrm{j}\,X_2(s)$$

## CURRENT_DEPENDENT_SKIN_EFFECT_V1

上式の $R_2(\cdot)$、$X_2(\cdot)$ において引数を $r_I$ とした $R_2(r_I)$、$X_2(r_I)$ を定める。負荷項・合成における $(1-s)/s$ および $1/s$ の $s$ は、引き続きスリップである。

| 記号 | YAML キー |
|------|------------|
| $\alpha_r$ | `alpha_secondary_r` |
| $\beta_r$ | `beta_secondary_r` |
| $\alpha_x$ | `alpha_secondary_x` |
| $\beta_x$ | `beta_secondary_x` |

**抵抗:**

$$R_2(r_I) = R_{2,0}\,\Bigl(1 + \alpha_r\,\bigl(1 - e^{-\beta_r\, r_I}\bigr)\Bigr)$$

**リアクタンス:**

$$X_2(r_I) = X_{2,0}\,\Bigl(1 - \alpha_x\,\bigl(1 - e^{-\beta_x\, r_I}\bigr)\Bigr)$$

**基本支路:**

$$Z_\mathrm{base}(s,r_I) = R_2(r_I) + \mathrm{j}\,X_2(r_I)$$

**負荷支路（純実部）:**

$$Z_\mathrm{load}(s,r_I) = R_2(r_I)\,\frac{1-s}{s}$$

**合成:**

$$Z_\mathrm{tot}(s,r_I) = \frac{R_2(r_I)}{s} + \mathrm{j}\,X_2(r_I)$$

## CURRENT_DEPENDENT_LEAKAGE_SATURATION_V1

抵抗は基準のまま。漏れリアクタンスのみ電流比で $\tanh$ 飽和する。

| 記号 | YAML キー |
|------|------------|
| $\alpha_{\ell}$ | `alpha_secondary_leakage_x` |
| $\beta_{\ell}$ | `beta_secondary_leakage_x` |

**抵抗:**

$$R_2 = R_{2,0}$$

**リアクタンス:**

$$X_2(r_I) = X_{2,0}\,\Bigl(1 - \alpha_{\ell}\,\tanh(\beta_{\ell}\, r_I)\Bigr)$$

**基本支路:**

$$Z_\mathrm{base}(r_I) = R_{2,0} + \mathrm{j}\,X_2(r_I)$$

**負荷支路（純実部）:**

$$Z_\mathrm{load}(s) = R_{2,0}\,\frac{1-s}{s}$$

**合成:**

$$Z_\mathrm{tot}(s,r_I) = \frac{R_{2,0}}{s} + \mathrm{j}\,X_2(r_I)$$

## CURRENT_DEPENDENT_SKIN_EFFECT_AND_LEAKAGE_SATURATION_V1

表皮（指数）と漏れ飽和（$\tanh$）を漏れリアクタンスに乗じる。抵抗は表皮の指数スケールのみを受ける。

| 記号 | YAML キー |
|------|------------|
| $\alpha_r$ | `alpha_secondary_r` |
| $\beta_r$ | `beta_secondary_r` |
| $\alpha_x$ | `alpha_secondary_x` |
| $\beta_x$ | `beta_secondary_x` |
| $\alpha_{\ell}$ | `alpha_secondary_leakage_x` |
| $\beta_{\ell}$ | `beta_secondary_leakage_x` |

**抵抗:**

$$R_2(r_I) = R_{2,0}\,\Bigl(1 + \alpha_r\,\bigl(1 - e^{-\beta_r\, r_I}\bigr)\Bigr)$$

**リアクタンス:**

$$S_{\mathrm{skin}}(r_I) = 1 - \alpha_x\,\Bigl(1 - e^{-\beta_x\, r_I}\Bigr)$$

$$S_{\mathrm{leak}}(r_I) = 1 - \alpha_{\ell}\,\tanh(\beta_{\ell}\, r_I)$$

$$X_2(r_I) = X_{2,0}\,S_{\mathrm{skin}}(r_I)\,S_{\mathrm{leak}}(r_I)$$

**基本支路:**

$$Z_\mathrm{base}(s,r_I) = R_2(r_I) + \mathrm{j}\,X_2(r_I)$$

**負荷支路（純実部）:**

$$Z_\mathrm{load}(s,r_I) = R_2(r_I)\,\frac{1-s}{s}$$

**合成:**

$$Z_\mathrm{tot}(s,r_I) = \frac{R_2(r_I)}{s} + \mathrm{j}\,X_2(r_I)$$
