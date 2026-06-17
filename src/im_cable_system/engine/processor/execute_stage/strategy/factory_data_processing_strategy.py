"""データ処理戦略ファクトリー。

このモジュールは、ExecuteStage における IM ケーブルシステムの
データ処理方法（逐次 or 並列）を設定ファイルに基づいて選択し、
対応するストラテジー実装を生成するためのファクトリーを提供する。

呼び出し側は `IDataProcessingStrategy` インターフェースのみを意識すればよく、
逐次処理・スレッド並列・プロセス並列といった実装差分は本モジュールに
カプセル化される。
"""

from im_cable_system.engine.processor.execute_stage.strategy.i_data_processing_strategy import (  # noqa: E501
    IDataProcessingStrategy,
)
from im_cable_system.engine.processor.execute_stage.strategy.parallel_processing_strategy import (  # noqa: E501
    ParallelProcessingStrategy,
)
from im_cable_system.engine.processor.execute_stage.strategy.sequential_processing_strategy import (  # noqa: E501
    SequentialProcessingStrategy,
)
from im_cable_system.engine.shared.config import (
    DataProcessingMethod,
    IConfig,
    ILogger,
)


class DataProcessingStrategyFactory:
    """データ処理戦略ファクトリー。

    設定（`config.yaml`）の内容に応じて、以下のいずれかを生成する。

    - `SequentialProcessingStrategy`（逐次処理）
    - `ParallelProcessingStrategy`（スレッド／プロセス並列）

    これにより、ExecuteStage 側は「戦略の選択」を意識せず、
    単に `IDataProcessingStrategy` の `process` を呼び出すだけでよい設計とする。

    """

    @staticmethod
    def create(config: IConfig, logger: ILogger) -> IDataProcessingStrategy:
        """データ処理戦略のインスタンスを生成する。

        設定ファイル（`config.yaml`）の `data_processing.method` に基づいて
        戦略クラスを選択し、そのインスタンスを生成する。

        現在サポートしている値は以下の通り。

        - `"sequential"`: 逐次処理戦略
        - `"thread"`: スレッドベースの並列処理戦略
        - `"process"`: プロセスベースの並列処理戦略

        Note:
            ExecuteStage ではバッチ内の各 Input に対し Algorithm 層の計算（多くは
            NumPy 等を用いた数値シミュレーション）を行う。method の選び方の目安:

            `"sequential"`:
                メリットは処理が単純で再現性が高くデバッグしやすいこと、および GIL や
                pickle の制約を気にしなくてよいこと。デメリットは CPU コアを横断して
                速くしにくく、Input 件数が多いと総所要時間が伸びやすいこと。

            `"thread"`:
                メリットは同一プロセス内で完結し、`"process"` より起動・通信負荷が
                小さいことが多いこと。NumPy/BLAS 等が GIL を解放する区間では
                スループットが伸びうる。デメリットは CPython の GIL により、純粋な
                Python の CPU 処理が主体だと並列効果が限定的になりやすいこと。

            `"process"`:
                メリットはプロセス単位で走らせられるため CPU バウンドな計算の並列度を
                上げやすいこと。デメリットは各タスクの引数・戻り値の pickle と
                プロセス起動のオーバーヘッドがあり、件数が少ないと割に合わないこと、
                およびワーカーに渡す関数・DTO が pickle 可能である必要があること
                （制約に引っかかる場合は `"sequential"` / `"thread"` を検討）。

        戦略の詳細な挙動（例: ワーカー数、キューの実装など）は各クラス側に委譲し、
        本ファクトリーでは「どの戦略を使うか」の判定のみに責務を限定する。

        Args:
            config: 設定オブジェクト。
                `data_processing` セクションから `method` を参照する。
            logger: ロガーオブジェクト。
                並列戦略ではワーカー側のログ出力にも利用される。

        Returns:
            IDataProcessingStrategy: 生成された戦略インスタンス。

        Raises:
            ValueError: 想定外の :class:`DataProcessingMethod` 値だった場合。
        """
        method = config.data_processing.method

        if method is DataProcessingMethod.SEQUENTIAL:
            return SequentialProcessingStrategy.create(
                config=config, logger=logger
            )
        if method in (
            DataProcessingMethod.THREAD,
            DataProcessingMethod.PROCESS,
        ):
            return ParallelProcessingStrategy.create(
                config=config, logger=logger, method=method
            )

        # 通常 Config 側で値域は検証済みのため到達しない。
        raise ValueError(
            f"無効なデータ処理方法です: {method.value}. "
            '"sequential", "thread", "process" のいずれかを指定してください。'
        )
