"""IMモデルビルダーのファクトリークラス。

このモジュールは、かご重数（単一かご／二重かご）に応じて適切な
IMモデルビルダーのインスタンスを生成します。
"""

from __future__ import annotations

from im_cable_system.engine.algorithm.execute_algorithm.build_model.build_im_model.double_cage_im_model_builder import (  # noqa: E501
    DoubleCageImModelBuilder,
)
from im_cable_system.engine.algorithm.execute_algorithm.build_model.build_im_model.i_im_model_builder import (  # noqa: E501
    IImModelBuilder,
)
from im_cable_system.engine.algorithm.execute_algorithm.build_model.build_im_model.single_cage_im_model_builder import (  # noqa: E501
    SingleCageImModelBuilder,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    ImCageMultiplicityType,
)


class ImModelBuilderFactory:
    """IMモデルビルダーのファクトリークラス。

    かご重数（単一かご／二重かご）に応じて適切なIMモデルビルダーの
    インスタンスを生成します。
    """

    @classmethod
    def create(
        cls,
        cage_multiplicity: ImCageMultiplicityType,
        config: IConfig,
        logger: ILogger,
    ) -> IImModelBuilder:
        """IMモデルビルダーのインスタンスを生成する。

        Args:
            cage_multiplicity: かごの重数（単一かご／二重かご）。
            config: 設定オブジェクト。
            logger: ロガーオブジェクト。

        Returns:
            IImModelBuilder: 生成されたビルダーインスタンス。

        Raises:
            ValueError: 未対応のかご重数が指定された場合。

        Note:
            モデルについては、一次、励磁、二次回路それぞれに対して存在するが、ArrayLayoutDtoが求める条件（電流に対してイミタンスが変化するなど）合わせて構築されている限り、ビルダーは一つ「SingleCageImModelBuilder」で良い。
            一方で、二重かご型（深溝の等価表現を含む）を処理する場合は、ビルダーは「DoubleCageImModelBuilder」が必要になる。
        """
        if cage_multiplicity == ImCageMultiplicityType.SINGLE_CAGE:
            return SingleCageImModelBuilder.create(config=config, logger=logger)
        if cage_multiplicity == ImCageMultiplicityType.DOUBLE_CAGE:
            return DoubleCageImModelBuilder.create(config=config, logger=logger)
        raise ValueError(f"未対応のかご重数です: {cage_multiplicity}")
