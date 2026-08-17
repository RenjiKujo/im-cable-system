# IM 漂遊負荷損（stray_load）モデル係数と数式

漂遊負荷損 $P_{stray}$ は、二次負荷支路電力（内部機械出力）から引いて軸出力を得る
**軸出力控除**の一つである。規格（IEC 60034-2-1 / IEEE 112）の損失分類では
機械損ではなく追加負荷損（stray load loss）であり、**機械損とは呼ばない**。
摩擦・風損と同じくイミタンス（インピーダンス・アドミタンス）を持たない
サブシステムであり、実装は
`engine/algorithm/execute_algorithm/simulate/power/calculate_im_shaft_output_deduction/stray_load/`
（`build_model/` 配下ではない）。

基準電流には**二次側合計電流 $|I_2|$**（`get_secondary_total_current()`）を選ぶ。
無負荷（$s=0$）で二次電流が 0 になるため、$P_{stray}$ も無負荷で 0 になる
「負荷」損として振る舞う（一次電流を基準にすると無負荷損に励磁電流分が混入する）。

$P_N$ は `ImSeriesDto.nameplate_power`（**3相合計**）。$I_N$ は
`ImSeriesDto.nameplate_current`（銘牌電流）。$|I_N| \le \mathrm{eps}$（近接ゼロ、数値ガードの
共通閾値）のときは正規化せず $r_{I_2} = |I_2|$ にフォールバックする。他サブシステムの
`r_I` 正規化（`model_equations/index.md` の記号の共通前提）が単純な「$0$ 以下」判定なのに対し、
本サブシステムは `docs/conventions/4_numerical_robustness.md` の極小ガード規約
（`abs(x) <= eps` をクランプ対象にする）に合わせて eps 判定にする。
$P_{stray}$ は $P_N$ に比例するため**3相合計**であり、「1相で計算して3相へ変換」の
経路を通らない。$P_{stray}$ は**有効電力のみ**（虚部は常に 0）。

適用範囲は電動域に限る（[im_friction_windage.md](im_friction_windage.md) と同じ理由）。

## NONE

モデル固有係数はない。$P_{stray} = 0$。

## CURRENT_DEPENDENT_QUADRATIC_V1

二次側合計電流の比の2乗に比例する漂遊負荷損。

| 記号 | YAML キー |
|------|------------|
| $k_{str}$ | `k_stray_load` |

$$P_{stray} = k_{str}\, P_N\, r_{I_2}^{\,2}, \qquad r_{I_2} = \frac{|I_2|}{I_N}$$
