"""estimate_params のステップ間共有部品（軸2: shared）。

``estimate_params`` のコンポーネントは2軸で整理する。

- **軸1（ステップ）**: ``collect_descriptors`` / ``fit_parameters`` /
  ``apply_fitted_input`` / ``build_summary`` … ``execute`` の実行フローに対応。
- **軸2（共有）= 本パッケージ**: 複数ステップから使われる横断部品のみを集約する。
  特定の1ステップ専用の処理はここに置かず、該当ステップ配下に置く。

サブパッケージ:
    - :mod:`descriptor`: フィット記述子 DTO（``FittableParamDescriptor``）。
      collect / fit / apply / summary の全ステップで生成・消費される共通契約。
    - :mod:`curve_eval`: カタログ対シミュレーションの「残差・指標・補間・正規化」。
      fit_parameters（残差評価）と build_summary（誤差指標）の両方から共有される。

本パッケージ自体は import 窓口ではない（各サブパッケージの ``__init__`` を窓口とする）。
"""
