"""π型ケーブルシステム回路モデル構築器。

このモジュールは、π型ケーブル回路と誘導電動機を統合したシステム回路の
イミタンスを計算し、ItmSystemModelDtoを構築する処理を提供します。
"""

from __future__ import annotations

from im_cable_system.engine.algorithm.execute_algorithm.build_model.build_system_model.i_system_model_builder import (  # noqa: E501
    ISystemModelBuilder,
)
from im_cable_system.engine.domain.physics.electrical import (
    admittance_from_impedance,
    combine_admittance_parallel,
    combine_impedance_series,
    impedance_from_admittance,
)
from im_cable_system.engine.shared.config import IConfig, ILogger, timer
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    PieCableConductorKey,
    PieCableGroundKey,
)
from im_cable_system.engine.shared.dto.generic.physical_quantity import (
    ArrayComplexAdmittanceDto,
    ArrayComplexImpedanceDto,
)
from im_cable_system.engine.shared.dto.itm import (
    ItmCableImmittanceDto,
    ItmCableModelDto,
    ItmImModelDto,
    ItmImTotalDto,
    ItmSystemModelDto,
)


class ImPieCableSystemModelBuilder(ISystemModelBuilder):
    """π型ケーブルシステム回路モデル構築器。

    π型ケーブル回路と誘導電動機を統合したシステム回路のイミタンスを計算し、
    ItmSystemModelDtoを構築します。
    """

    def __init__(self, config: IConfig, logger: ILogger) -> None:
        """回路モデル構築器のインスタンスを初期化する。

        Args:
            config: 回路モデル構築器生成に必要な設定。
            logger: ロガーオブジェクト。
        """
        self._config: IConfig = config
        self._logger: ILogger = logger

    @classmethod
    def create(cls, config: IConfig, logger: ILogger) -> ISystemModelBuilder:
        """回路モデル構築器のインスタンスを生成するファクトリーメソッド。

        Args:
            config: 回路モデル構築器生成に必要な設定。
            logger: ロガーオブジェクト。

        Returns:
            ISystemModelBuilder: 生成された回路モデル構築器インスタンス。
        """
        return cls(config=config, logger=logger)

    @timer(logger=None, line="=", min_duration=0.1)
    def build(
        self,
        itm_im_model_dto: ItmImModelDto,
        itm_cable_model_dto: ItmCableModelDto,
    ) -> ItmSystemModelDto:
        """システム回路モデルを構築する。

        Args:
            itm_im_model_dto: 誘導電動機モデルDTO（必須）。
            itm_cable_model_dto: ケーブルモデルDTO（必須）。

        Returns:
            ItmSystemModelDto: システムモデルDTO。

        Raises:
            ValueError: 必須引数がNoneの場合。
        """
        if itm_im_model_dto is None:
            raise ValueError("itm_im_model_dtoは必須です。")
        if itm_cable_model_dto is None:
            raise ValueError("itm_cable_model_dtoは必須です。")

        # システム全体のイミタンスを計算
        system_impedance: ArrayComplexImpedanceDto
        system_admittance: ArrayComplexAdmittanceDto
        system_impedance, system_admittance = self._calculate_system_immittance(
            im_model=itm_im_model_dto,
            cable_model=itm_cable_model_dto,
        )

        return ItmSystemModelDto(
            system_phase_impedance=system_impedance,
            system_phase_admittance=system_admittance,
        )

    def _calculate_system_immittance(
        self,
        im_model: ItmImModelDto,
        cable_model: ItmCableModelDto,
    ) -> tuple[ArrayComplexImpedanceDto, ArrayComplexAdmittanceDto]:
        """システム全体のイミタンスを計算する。

        π型ケーブル回路と誘導電動機を統合したシステム回路のイミタンスを計算する。
        ケーブルの状態（地絡、完全絶縁、理想導体、通常）に応じて計算ロジックを分ける。

        Args:
            im_model: 誘導電動機モデルDTO。
            cable_model: ケーブルモデルDTO。

        Returns:
            tuple[ArrayComplexImpedanceDto, ArrayComplexAdmittanceDto]:
                システム位相インピーダンスとアドミタンスのタプル。
        """
        cable_immittance = cable_model.cable_immittance
        im_total_model = im_model.total_model
        eps = self._config.numerical_guard_config.eps
        max_mag = 1.0 / eps

        # ケーブルの状態に応じて計算ロジックを分ける
        if (
            cable_immittance.is_ground_insulated
            and cable_immittance.is_conductor_ideal
        ):
            # ケーブルが完全絶縁かつ理想導体の場合
            system_impedance, system_admittance = (
                self._calculate_ground_insulated_ideal_conductor_system(
                    im_total_model=im_total_model,
                )
            )
        elif cable_immittance.is_ground_insulated:
            # ケーブルが完全絶縁で理想導体ではない場合
            system_impedance, system_admittance = (
                self._calculate_ground_insulated_system(
                    cable_immittance=cable_immittance,
                    im_total_model=im_total_model,
                    eps=eps,
                    max_mag=max_mag,
                )
            )
        elif cable_immittance.is_conductor_ideal:
            # ケーブルが理想導体で完全絶縁ではない場合
            system_impedance, system_admittance = (
                self._calculate_ideal_conductor_system(
                    cable_immittance=cable_immittance,
                    im_total_model=im_total_model,
                    eps=eps,
                    max_mag=max_mag,
                )
            )
        else:
            # 通常ケースもしくは地絡ケース
            system_impedance, system_admittance = self._calculate_normal_system(
                cable_immittance=cable_immittance,
                im_total_model=im_total_model,
                eps=eps,
                max_mag=max_mag,
            )

        # 型チェッカー用: 戻り値の型を明示  # noqa: ERA001
        return system_impedance, system_admittance

    def _calculate_normal_system(
        self,
        cable_immittance: ItmCableImmittanceDto,
        im_total_model: ItmImTotalDto,
        eps: float,
        max_mag: float,
    ) -> tuple[ArrayComplexImpedanceDto, ArrayComplexAdmittanceDto]:
        """通常ケースのシステムイミタンスを計算する。

        π型ケーブル回路と誘導電動機を統合したシステム回路のイミタンスを計算する。
        回路構成: [電源] --[Y_up]--[Z_c]--[Y_down]--[Z_im]--[GND]

        計算手順:
        1. 下流側: Y_downとY_imを並列合成 → Z_down_total
        2. 中間: Z_cとZ_down_totalを直列合成 → Z_mid
        3. 上流側: Y_upとZ_midを並列合成 → Z_system

        ケーブルが地絡しているショート回路の場合もこのケースに含まれる。

        Args:
            cable_immittance: ケーブルイミタンスDTO。
            im_total_model: 誘導電動機の全範囲モデル情報DTO。
            eps: 近接ゼロ判定のしきい値。
            max_mag: 最大の大きさ。

        Returns:
            tuple[ArrayComplexImpedanceDto, ArrayComplexAdmittanceDto]:
                システム位相インピーダンスとアドミタンスのタプル。
        """
        # ケーブルの各要素を取得
        y_up = cable_immittance.ground_admittance[PieCableGroundKey.UPSTREAM]
        z_c = cable_immittance.conductor_impedance[PieCableConductorKey.SINGLE]
        y_down = cable_immittance.ground_admittance[
            PieCableGroundKey.DOWNSTREAM
        ]

        # 誘導電動機のアドミタンスを取得
        y_im = im_total_model.admittance

        # 下流側: Y_downとY_imを並列合成  # noqa: ERA001
        y_down_total = combine_admittance_parallel(
            admittance1=y_down,
            admittance2=y_im,
            eps=eps,
            max_mag=max_mag,
        )
        # インピーダンスに変換
        z_down_total = impedance_from_admittance(
            admittance=y_down_total,
            eps=eps,
            max_mag=max_mag,
        )

        # 中間: Z_cとZ_down_totalを直列合成  # noqa: ERA001
        z_mid = combine_impedance_series(
            impedance1=z_c,
            impedance2=z_down_total,
            eps=eps,
            max_mag=max_mag,
        )

        # 上流側: Y_upとZ_midを並列合成  # noqa: ERA001
        # Z_midをアドミタンスに変換
        y_mid = admittance_from_impedance(
            impedance=z_mid,
            eps=eps,
            max_mag=max_mag,
        )
        # Y_upとY_midを並列合成
        y_system = combine_admittance_parallel(
            admittance1=y_up,
            admittance2=y_mid,
            eps=eps,
            max_mag=max_mag,
        )

        # システムインピーダンスに変換
        z_system = impedance_from_admittance(
            admittance=y_system,
            eps=eps,
            max_mag=max_mag,
        )

        return z_system, y_system

    def _calculate_ideal_conductor_system(
        self,
        cable_immittance: ItmCableImmittanceDto,
        im_total_model: ItmImTotalDto,
        eps: float,
        max_mag: float,
    ) -> tuple[ArrayComplexImpedanceDto, ArrayComplexAdmittanceDto]:
        """理想導体ケースのシステムイミタンスを計算する。

        理想導体の場合、Z_cは0（またはEPS）であるため、実質的に
        上流側アース、下流側アース、誘導電動機アドミタンスが並列接続される。

        回路構成: [電源] --[Y_up]--[Z_c≈0]--[Y_down]--[Z_im]--[GND]
        → Z_cが0のため、Y_up、Y_down、Y_imが並列接続される。

        Args:
            cable_immittance: ケーブルイミタンスDTO。
            im_total_model: 誘導電動機の全範囲モデル情報DTO。
            eps: 近接ゼロ判定のしきい値。
            max_mag: 最大の大きさ。

        Returns:
            tuple[ArrayComplexImpedanceDto, ArrayComplexAdmittanceDto]:
                システム位相インピーダンスとアドミタンスのタプル。
        """
        # ケーブルの各要素を取得
        y_up = cable_immittance.ground_admittance[PieCableGroundKey.UPSTREAM]
        y_down = cable_immittance.ground_admittance[
            PieCableGroundKey.DOWNSTREAM
        ]

        # 誘導電動機のアドミタンスを取得
        im_admittance = im_total_model.admittance

        # Y_up、Y_down、Y_imを並列合成
        y_temp = combine_admittance_parallel(
            admittance1=y_up,
            admittance2=y_down,
            eps=eps,
            max_mag=max_mag,
        )
        y_system = combine_admittance_parallel(
            admittance1=y_temp,
            admittance2=im_admittance,
            eps=eps,
            max_mag=max_mag,
        )

        # システムインピーダンスに変換
        z_system = impedance_from_admittance(
            admittance=y_system,
            eps=eps,
            max_mag=max_mag,
        )

        return z_system, y_system

    def _calculate_ground_insulated_system(
        self,
        cable_immittance: ItmCableImmittanceDto,
        im_total_model: ItmImTotalDto,
        eps: float,
        max_mag: float,
    ) -> tuple[ArrayComplexImpedanceDto, ArrayComplexAdmittanceDto]:
        """完全絶縁ケースのシステムイミタンスを計算する。

        完全絶縁の場合、上流側・下流側アースが開放しているため、
        Y_upとY_downは非常に小さい（EPS値）。
        上流側アースアドミタンス（Y_up ≈ 0）は並列接続では無視できるため、
        実質的にZ_cとZ_imが直列接続された結果がシステムインピーダンスになる。

        回路構成: [電源] --[Y_up≈0]--[Z_c]--[Y_down≈0]--[Z_im]--[GND]
        → Y_upとY_downが無視できるため、Z_cとZ_imの直列合成がシステムインピーダンス。

        Args:
            cable_immittance: ケーブルイミタンスDTO。
            im_total_model: 誘導電動機の全範囲モデル情報DTO。
            eps: 近接ゼロ判定のしきい値。
            max_mag: 最大の大きさ。

        Returns:
            tuple[ArrayComplexImpedanceDto, ArrayComplexAdmittanceDto]:
                システム位相インピーダンスとアドミタンスのタプル。
        """
        # ケーブルの導線インピーダンスを取得
        z_c = cable_immittance.conductor_impedance[PieCableConductorKey.SINGLE]

        # 誘導電動機のインピーダンスを取得
        im_impedance = im_total_model.impedance

        # 完全絶縁の場合、上流側・下流側アースは開放されているため、
        # アースアドミタンス（Y_up, Y_down ≈ 0）は無視でき、
        # Z_cとZ_imが直列接続される
        z_system = combine_impedance_series(
            impedance1=z_c,
            impedance2=im_impedance,
            eps=eps,
            max_mag=max_mag,
        )

        # システムアドミタンスに変換
        y_system = admittance_from_impedance(
            impedance=z_system,
            eps=eps,
            max_mag=max_mag,
        )

        return z_system, y_system

    def _calculate_ground_insulated_ideal_conductor_system(
        self,
        im_total_model: ItmImTotalDto,
    ) -> tuple[ArrayComplexImpedanceDto, ArrayComplexAdmittanceDto]:
        """完全絶縁かつ理想導体ケースのシステムイミタンスを計算する。

        完全絶縁かつ理想導体の場合、ケーブルの影響が無視できるため、
        システムイミタンスは誘導電動機のイミタンスそのものになる。

        完全絶縁: 上流側・下流側アースが開放（Y_up ≈ 0, Y_down ≈ 0）
        理想導体: 導線インピーダンスが0（Z_c ≈ 0）

        この場合、回路は実質的に誘導電動機のみが接続された状態になる。

        Args:
            im_total_model: 誘導電動機の全範囲モデル情報DTO。

        Returns:
            tuple[ArrayComplexImpedanceDto, ArrayComplexAdmittanceDto]:
                システム位相インピーダンスとアドミタンスのタプル。
                システムイミタンスは誘導電動機のイミタンスそのもの。
        """
        # システムインピーダンスは誘導電動機のインピーダンスそのもの
        z_system = im_total_model.impedance

        # システムアドミタンスは誘導電動機のアドミタンスそのもの
        y_system = im_total_model.admittance

        return z_system, y_system
