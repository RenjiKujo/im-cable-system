"""ItmDto → OutputDto 変換ステップの実装。

本モジュールは出力アルゴリズムで「唯一 itm ステージ DTO に依存する境界」である。
``ItmDto`` から、入力原値の ``ImDto`` / ``CableDto``・出力用結果生量
``OutputSimulationResultDto`` を組み立て、``OutputDto`` を返す。

設計判断（入力原値の解決経路）:
    ``ItmDto`` は入力原値の ``ImDto`` / ``CableDto`` を保持せず、構築済みモデル
    ``model.im`` (``ItmImModelDto``) / ``model.cable`` (``ItmCableModelDto``) のみ
    を持つ。``ItmImModelDto`` は ``ImSeriesDto`` 相当（銘板・結線/回路種別・
    一次/励磁/二次の回路モデルと R/L）を全て保持するため、ここから ``ImDto`` を
    復元する。ケーブルも ``ItmCableModelDto`` から復元するが、入力 ``cable=None``
    に対し build_model が生成する擬似ケーブル（完全導体・完全絶縁）は個体名・
    セクション情報を持たないため、入力原値ケーブルは存在しないとみなし ``None``
    を返す（``ItmCableModelDto.name is None`` で判定）。
"""

from __future__ import annotations

from im_cable_system.engine.algorithm.output_algorithm.convert.i_output_dto_converter import (  # noqa: E501
    IOutputDtoConverter,
)
from im_cable_system.engine.shared.config import IConfig, ILogger
from im_cable_system.engine.shared.dto.generic.im_cable_system import (
    CableDto,
    CableSectionDto,
    CableSectionDtos,
    CableSeriesDto,
    ImDto,
    ImSeriesDto,
)
from im_cable_system.engine.shared.dto.itm import ItmDto
from im_cable_system.engine.shared.dto.output import (
    OutputDto,
    OutputSimulationResultDto,
)


class OutputDtoConverter(IOutputDtoConverter):
    """ItmDto から OutputDto を組み立てる変換器。"""

    def __init__(self, config: IConfig, logger: ILogger) -> None:
        """インスタンスを初期化する。

        Args:
            config: 設定オブジェクト。
            logger: ロガーオブジェクト。
        """
        self._config: IConfig = config
        self._logger: ILogger = logger

    @classmethod
    def create(
        cls,
        config: IConfig,
        logger: ILogger,
    ) -> IOutputDtoConverter:
        """変換器のインスタンスを生成する。"""
        return cls(config=config, logger=logger)

    def convert(self, itm_dto: ItmDto) -> OutputDto:
        """ItmDto から OutputDto を構築して返す。

        Args:
            itm_dto: 変換元の中間 DTO。``simulation_result`` は power /
                characteristic を含む完全計算済みであること。

        Returns:
            入力原値とシミュレーション結果生量を併せ持つ出力トップ DTO。

        Raises:
            ValueError: ``simulation_result`` が None、または電流電圧のみ計算で
                power / characteristic を欠く場合（``_build_result`` 参照）。
        """
        model = itm_dto.model
        return OutputDto(
            name=itm_dto.name,
            array_layout=model.array_layout,
            im=self._resolve_input_im(itm_dto),
            cable=self._resolve_input_cable(itm_dto),
            result=self._build_result(itm_dto),
            im_pc_catalogs=model.im_pc_catalogs,
            numerical_stability_report=itm_dto.numerical_stability_report,
            estimate_params_fit_summary=itm_dto.estimate_params_fit_summary,
        )

    def _resolve_input_im(self, itm_dto: ItmDto) -> ImDto:
        """構築済み IM モデルから入力原値 ``ImDto`` を復元する。

        ``ItmImModelDto`` が保持する銘板・結線/回路種別・一次/励磁/二次の回路
        モデルと R/L をそのまま ``ImSeriesDto`` に詰め替える。

        Args:
            itm_dto: 変換元の中間 DTO。

        Returns:
            復元した入力原値の IM DTO。
        """
        im_model = itm_dto.model.im
        basic = im_model.basic_info
        circuit = im_model.circuit_info
        primary = im_model.primary_model
        excitation = im_model.excitation_model
        secondary = im_model.secondary_model
        im_series = ImSeriesDto(
            name=basic.series_name,
            poles=basic.poles,
            nameplate_voltage=basic.nameplate_voltage,
            nameplate_current=basic.nameplate_current,
            nameplate_power=basic.nameplate_power,
            nameplate_frequency=basic.nameplate_frequency,
            connection_type=circuit.connection_type,
            circuit_type=circuit.circuit_type,
            primary_model=primary.model,
            primary_resistance=primary.resistance,
            primary_inductance=primary.inductance,
            excitation_model=excitation.model,
            excitation_resistance=excitation.resistance,
            excitation_inductance=excitation.inductance,
            cage_multiplicity=secondary.cage_multiplicity,
            secondary_models=secondary.models,
            secondary_resistances=secondary.resistances,
            secondary_inductances=secondary.inductances,
            friction_windage_model=im_model.friction_windage_model,
            stray_load_model=im_model.stray_load_model,
        )
        return ImDto(im_series=im_series, name=im_model.name)

    def _resolve_input_cable(self, itm_dto: ItmDto) -> CableDto | None:
        """構築済みケーブルモデルから入力原値 ``CableDto`` を復元する。

        擬似ケーブル（入力 ``cable=None`` に対し build_model が生成する完全導体・
        完全絶縁モデル）は個体名・セクション情報を持たないため ``None`` を返す。

        Args:
            itm_dto: 変換元の中間 DTO。

        Returns:
            復元した入力原値のケーブル DTO。擬似ケーブルの場合は ``None``。
        """
        cable_model = itm_dto.model.cable
        # 擬似ケーブルは name / cable_info が None（cable_model docstring 参照）。
        if cable_model.name is None or cable_model.cable_info is None:
            return None
        sections: list[CableSectionDto] = []
        for section in cable_model.cable_info.get_all():
            basic = section.basic_info
            density = section.line_density_info
            series = CableSeriesDto(
                name=basic.series_name,
                shape_type=basic.shape_type,
                conductor_resistance_per_length=(
                    density.conductor_resistance_per_length
                ),
                conductor_inductance_per_length=(
                    density.conductor_inductance_per_length
                ),
                ground_resistance_length=density.ground_resistance_length,
                ground_capacitance_per_length=(
                    density.ground_capacitance_per_length
                ),
            )
            sections.append(
                CableSectionDto(
                    name=basic.name,
                    length=basic.length,
                    series=series,
                )
            )
        return CableDto(
            name=cable_model.name,
            sections=CableSectionDtos(objects=sections),
            conductor_model=cable_model.cable_immittance.conductor_model,
        )

    def _build_result(self, itm_dto: ItmDto) -> OutputSimulationResultDto:
        """シミュレーション結果生量を ``OutputSimulationResultDto`` へ抽出する。

        出力（図表・表）に必要な物理量だけを generic の物理量 DTO で取り出す。
        派生量（PF / |I| / 出力比 等）は持たせず、図表/表ビルダーが算出する。

        Args:
            itm_dto: 変換元の中間 DTO。

        Returns:
            出力用に抽出したシミュレーション結果生量。

        Raises:
            ValueError: ``simulation_result`` が None（simulate 未実行）の場合、
                または power / characteristic を欠く（電流電圧のみ計算）場合。
        """
        simulation = itm_dto.simulation_result
        if simulation is None:
            raise ValueError(
                "simulation_result が None です。"
                "出力には simulate 済みの ItmDto が必要です。"
            )
        power = simulation.power
        characteristic = simulation.characteristic
        if power is None or characteristic is None:
            raise ValueError(
                "電流電圧のみ計算した結果は出力に未対応です。"
                "power / characteristic を含む完全計算済み結果が必要です。"
            )
        voltage_current = simulation.voltage_current
        # 回転数のみ rpm で出力する（他量は ItmDto の SI 値を素通し）。
        rotational_speed = (
            characteristic.rotational_speed.rotational_speed.convert_to_unit(
                "rpm"
            )
        )
        return OutputSimulationResultDto(
            output_power=power.im_power.output_power,
            cable_input_phase_power=power.cable_power.input_phase_power,
            input_line_current=(
                voltage_current.cable_voltage_current.input_line_current
            ),
            system_efficiency=characteristic.efficiency.system_efficiency,
            torque=characteristic.torque.torque,
            rotational_speed=rotational_speed,
        )
