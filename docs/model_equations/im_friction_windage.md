# IM 摩擦・風損（friction_windage）モデル係数と数式

摩擦・風損 $P_{FW}$ は、二次負荷支路電力（内部機械出力）から引いて軸出力を得る
**軸出力控除**の一つである。規格（IEC 60034-2-1 / IEEE 112）の損失分類でも
機械損（friction / windage）であり、この呼び名は変えない。
イミタンス（インピーダンス・アドミタンス）を持たないサブシステムであり、
`ImPrimaryModelDto` 等と異なり並列合成・直列合成の対象にならない。実装は
`engine/algorithm/execute_algorithm/simulate/power/calculate_im_shaft_output_deduction/friction_windage/`
（`build_model/` 配下ではない）。

$P_N$ は `ImSeriesDto.nameplate_power`（**3相合計**）。$P_{FW}$ もこれに比例するため
**3相合計**であり、「1相で計算して3相へ変換」の経路を通らない唯一の量である。
$P_{FW}$ は**有効電力のみ**（虚部は常に 0）。無効電力は一切動かさない。

適用範囲は電動域（$s$ が 0 に近すぎない負荷範囲）に限る。$s \to 0$ 近傍では
軸出力（二次負荷電力 − 軸出力控除）が負になり得るため、この係数を有効にする教師曲線・
評価格子は $s \approx 0$ を含めない運用とする。

## NONE

モデル固有係数はない。$P_{FW} = 0$。

## CONSTANT_V1

負荷・スリップによらず一定の摩擦・風損。定格入力に対する比率 $k_{fw}$ で表す。

| 記号 | YAML キー |
|------|------------|
| $k_{fw}$ | `k_friction_windage` |

$$P_{FW} = k_{fw}\, P_N$$
