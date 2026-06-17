"""中間DTO検証オーケストレーターのインターフェース（im_cable_system）。

このモジュールは、IMケーブルシステムの中間DTO検証を統括する
オーケストレーターの契約を定義します。オーケストレーターの IF は、
実装（および公開窓口）が置かれる ``orchestrate`` サブパッケージの
**親 Dir（validate_itm_dto 直下）** に配置する。

設計方針（execute_algorithm の最上位 IF と形態を揃える）:
    - ``create(config, logger)`` と公開実行メソッド ``validate(itm_dto)`` の
      2 メソッド構成とする。``create`` は自身の生成のみを担当し、下位検証器の
      生成と実行は対応する private メソッド内に閉じる。
    - 各検証の有効・無効は **Config（``validation_config``）の ``enabled`` のみ**
      で制御する。forward-by-cartesian-grid のように電流・電圧レンジ検証を
      外したい場合は、Config 側で ``current_voltage_range.enabled: false`` とする。
    - ``_validate_energy_conservation`` / ``_validate_current_voltage_range``
      を ``@abstractmethod`` として明示し、「validate が何を順に呼ぶか」を
      IF の契約として固定する（:class:`IExecuteAlgorithmsOrchestrator` と同じ
      「実行手順そのものを IF で握る」ポリシー）。各 private は対応する検証が
      Config で無効な場合は何もしない。

検証を追加するときの門番（トートロジー回避）:
    新しい検証をここに足す前に、必ず「その条件は DTO 構築
    （``__post_init__``）または domain 計算で既に raise されるか？」を確認する。

    - **既に保証済みなら追加しない**。例えば効率が ``[0, 1]`` か、回転速度が
      非負か、配列が finite か等は ``physical_quantity`` DTO 構築時や
      ``domain.physics`` の計算時点で raise されるため、ここで再検証しても
      発火しないデッドコード（実質トートロジー）になる。
    - **追加してよいのは「単一 DTO では見えないもの」だけ**。すなわち
      (1) 外部基準との比較（例: 定格値 → ``current_voltage_range``）、
      (2) 別経路で算出した量どうしの突き合わせ（例: 入力＝出力＋損失 →
      ``energy_conservation``）、(3) 複数 DTO 間の関係。
    - 残っている 2 検証（energy_conservation / current_voltage_range）は
      いずれもこの基準を満たす独立検証である。
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.itm import (
    ItmDto,
)


class IItmValidationOrchestrator(ABC):
    """中間DTO検証オーケストレーターのインターフェース。

    ExecuteStage の最後に、中間 DTO（``ItmDto``）に対して複数の検証を
    既定順序でまとめて実行するオーケストレーター。

    メソッドの並び（呼び出し順）: ``create(config, logger)`` → ``validate``。
    """

    @classmethod
    @abstractmethod
    def create(
        cls, config: IConfig, logger: ILogger
    ) -> IItmValidationOrchestrator:
        """config と logger を受け取り、自身のインスタンスを生成する。

        自身のインスタンスのみ生成して返す。

        Args:
            config: 設定オブジェクト。
            logger: ロガーオブジェクト。

        Returns:
            IItmValidationOrchestrator: 生成されたインスタンス。
        """

    @abstractmethod
    def validate(self, itm_dto: ItmDto) -> None:
        """中間 DTO の妥当性を検証する。

        各 private メソッド内で検証器を生成し、既定の順序で順次実行する。実行順序:
        1. エネルギー保存則の検証（``_validate_energy_conservation``）
        2. 電流・電圧レンジの検証（``_validate_current_voltage_range``）

        各検証が Config で無効な場合、その検証はスキップされる。

        Args:
            itm_dto: 検証する中間 DTO。

        Raises:
            ValueError: 検証に失敗した場合（重大度レベルが ERROR の場合）。
        """

    @abstractmethod
    def _validate_energy_conservation(self, itm_dto: ItmDto) -> None:
        """エネルギー保存則を検証する。

        validate が内部で呼ぶ。外部からは直接呼ばない想定。
        対応する検証が Config で無効な場合は何もしない。

        Args:
            itm_dto: 検証する中間 DTO。

        Raises:
            ValueError: 検証に失敗した場合（重大度レベルが ERROR の場合）。
        """

    @abstractmethod
    def _validate_current_voltage_range(self, itm_dto: ItmDto) -> None:
        """電流・電圧レンジを検証する。

        validate が内部で呼ぶ。外部からは直接呼ばない想定。
        対応する検証が Config で無効な場合は何もしない。

        Args:
            itm_dto: 検証する中間 DTO。

        Raises:
            ValueError: 検証に失敗した場合（重大度レベルが ERROR の場合）。
        """
