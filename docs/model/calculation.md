# 等価回路の計算の流れ

この文書は、等価回路の上で物理量がどの順で決まるかを書く。クラス構成や DTO の受け渡しは書かない。

書く内容:

- イミタンス → 電圧・電流 → 電力 → 特性値
- 電流依存モデルで、イミタンス構築をやり直す位置
- EstimateParams がこの順計算をどう使うか（概要）

残差とカタログ 4 量の扱いは [curve_fitting_consistency.md](./curve_fitting_consistency.md)。
実装の入口は [architecture/algorithm/execute/0_overview.md](../architecture/algorithm/execute/0_overview.md)。
