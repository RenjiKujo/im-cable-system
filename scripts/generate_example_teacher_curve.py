"""examples/input 用の教師性能曲線 CSV をフォワード計算で生成する。

SlipAndCurrentDependent03（ケーブルなし）を 50 Hz / 200 V、
回転数 1500→1440 rpm（slip 0–4 %、1.5 rpm 刻み）で ForwardByOperatingPoints し、
``performance_curve.csv`` 形式の行を標準出力する。
"""

from __future__ import annotations

import argparse
import csv
import io
from pathlib import Path

import numpy as np

from im_cable_system.engine.pipeline import ForwardByOperatingPointsPipeline
from im_cable_system.engine.shared.config import Config, Logger
from im_cable_system.engine.shared.dto.generic.im_cable_system import ArrayKey
from im_cable_system.engine.shared.job_spec.forward import (
    ForwardJobSpec,
    ForwardJobSpecs,
)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SYNC_RPM = 1500.0
_RPM_STEP = 1.5
_RPM_MIN = 1440.0


def _rpm_grid(
    *,
    rpm_max: float = _SYNC_RPM,
    rpm_min: float = _RPM_MIN,
    rpm_step: float = _RPM_STEP,
) -> np.ndarray:
    """教師曲線用の回転数格子 [rpm]。

    既定は同期速度 1500 rpm を含む（slip 0 を含む）。摩擦・風損／漂遊負荷損
    （戦略C）の教師曲線では、s≈0 で軸出力が負になり得るため、呼び出し側が
    ``rpm_max`` を同期速度未満に指定して s≈0 を除外する
    （docs/estimate_params_curve_fitting_consistency.md 戦略C 参照）。
    """
    count = int(round((rpm_max - rpm_min) / rpm_step)) + 1
    return rpm_max - rpm_step * np.arange(count, dtype=np.float64)


def _slip_from_rpm(rpm: np.ndarray) -> np.ndarray:
    """同期回転数 1500 rpm から slip を導出する。"""
    return (_SYNC_RPM - rpm) / _SYNC_RPM


def _flat_real(value: object) -> np.ndarray:
    return np.asarray(np.real(np.asarray(value)), dtype=np.float64).reshape(-1)


def _power_factor(complex_power: object) -> np.ndarray:
    power = np.asarray(complex_power, dtype=np.complex128).reshape(-1)
    magnitude = np.abs(power)
    valid = (
        np.isfinite(power.real) & np.isfinite(power.imag) & (magnitude > 0.0)
    )
    pf = np.zeros(power.shape, dtype=np.float64)
    pf[valid] = power.real[valid] / magnitude[valid]
    return pf


def _write_axes_csv(path: Path, slips: np.ndarray) -> None:
    lines = [
        "slip,frequency,input_line_voltage",
        "[-],[Hz],[V]",
    ]
    for slip in slips:
        lines.append(f"{slip:.17g},50,200")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_series_csv(path: Path, series_name: str) -> None:
    path.write_text(
        f"im_cable_system_name,{series_name}_NoCable\n\n"
        "im_series_name,cable_series_name,cable_length,cable_conductor_model\n"
        "[-],[-],[m],[-]\n"
        f"{series_name},,,\n",
        encoding="utf-8",
    )


def _run_forward(
    *,
    series_name: str,
    config_path: Path,
    im_catalog: Path,
    cable_catalog: Path,
    work_dir: Path,
    rpm_max: float = _SYNC_RPM,
    rpm_min: float = _RPM_MIN,
    rpm_step: float = _RPM_STEP,
) -> tuple[
    np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray
]:
    rpm = _rpm_grid(rpm_max=rpm_max, rpm_min=rpm_min, rpm_step=rpm_step)
    slips = _slip_from_rpm(rpm)
    series_path = work_dir / "series_selection.csv"
    axes_path = work_dir / "axes.csv"
    _write_series_csv(series_path, series_name)
    _write_axes_csv(axes_path, slips)

    config = Config.create(
        config_file_path=config_path,
        im_series_catalog_file_path=im_catalog,
        cable_series_catalog_file_path=cable_catalog,
    )
    logger = Logger.create(config)
    pipeline = ForwardByOperatingPointsPipeline.create(
        config=config,
        logger=logger,
    )
    outputs = pipeline.run(
        ForwardJobSpecs(
            specs=(
                ForwardJobSpec(
                    series_selection_path=series_path,
                    axes_path=axes_path,
                    performance_curve_path=None,
                ),
            ),
        ),
    )
    output = outputs.get_all()[0]
    result = output.result
    layout = output.array_layout
    slip_axis = _flat_real(
        layout.arrays[ArrayKey.SLIP].to_base_unit().get_value()
    )
    order = np.argsort(slip_axis)
    power = _flat_real(
        np.real(result.output_power.to_base_unit().get_value()),
    )[order]
    current = np.abs(
        np.asarray(
            result.input_line_current.to_base_unit().get_value(),
            dtype=np.complex128,
        ).reshape(-1),
    )[order]
    pf = _power_factor(
        result.cable_input_phase_power.to_base_unit().get_value(),
    )[order]
    efficiency = _flat_real(
        result.system_efficiency.to_base_unit().get_value(),
    )[order]
    torque = _flat_real(result.torque.to_base_unit().get_value())[order]
    rpm_out = _flat_real(
        result.rotational_speed.convert_to_unit("rpm").get_value(),
    )[order]
    return rpm_out, power, current, pf, efficiency, torque


def _format_performance_curve_csv(
    series_name: str,
    rpm: np.ndarray,
    power: np.ndarray,
    current: np.ndarray,
    pf: np.ndarray,
    efficiency: np.ndarray,
    torque: np.ndarray,
) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(["im_performance_curve_name", series_name])
    writer.writerow(["name", "value", "unit"])
    writer.writerow(["poles", "4", "-"])
    writer.writerow(["supply_frequency", "50", "Hz"])
    writer.writerow(["supply_voltage", "200.0", "V"])
    writer.writerow([])
    writer.writerow(
        [
            "rotational_speed",
            "power",
            "current",
            "power_factor",
            "efficiency",
            "torque",
        ],
    )
    writer.writerow(["[rpm]", "[W]", "[A]", "[-]", "[-]", "[N·m]"])
    for idx in range(rpm.shape[0]):
        rpm_value = round(float(rpm[idx]) * 2.0) / 2.0
        writer.writerow(
            [
                f"{rpm_value:.17g}",
                f"{power[idx]:.17g}",
                f"{current[idx]:.17g}",
                f"{pf[idx]:.17g}",
                f"{efficiency[idx]:.17g}",
                f"{torque[idx]:.17g}",
            ],
        )
    return buf.getvalue()


def main() -> int:
    """エントリポイント。"""
    parser = argparse.ArgumentParser(
        description="Generate example teacher performance curve CSV.",
    )
    parser.add_argument(
        "--series-name",
        default="SlipAndCurrentDependent03",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=_REPO_ROOT / "examples/input/performance_curve.csv",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=_REPO_ROOT / "examples/config/forward_by_operating_points.yaml",
    )
    parser.add_argument(
        "--im-catalog",
        type=Path,
        default=_REPO_ROOT
        / "src/im_cable_system/catalog/im_series_catalog.yaml",
    )
    parser.add_argument(
        "--cable-catalog",
        type=Path,
        default=_REPO_ROOT
        / "src/im_cable_system/catalog/cable_series_catalog.yaml",
    )
    parser.add_argument(
        "--rpm-max",
        type=float,
        default=_SYNC_RPM,
        help=(
            "回転数格子の上限 [rpm]（既定は同期速度 = slip 0 を含む）。"
            "軸出力控除の教師曲線では同期速度未満を指定して s≈0 を除外する。"
        ),
    )
    parser.add_argument("--rpm-min", type=float, default=_RPM_MIN)
    parser.add_argument("--rpm-step", type=float, default=_RPM_STEP)
    args = parser.parse_args()
    work_dir = _REPO_ROOT / "examples" / "_tmp_teacher_curve"
    work_dir.mkdir(parents=True, exist_ok=True)
    rpm, power, current, pf, efficiency, torque = _run_forward(
        series_name=args.series_name,
        config_path=args.config,
        im_catalog=args.im_catalog,
        cable_catalog=args.cable_catalog,
        work_dir=work_dir,
        rpm_max=args.rpm_max,
        rpm_min=args.rpm_min,
        rpm_step=args.rpm_step,
    )
    csv_text = _format_performance_curve_csv(
        args.series_name,
        rpm,
        power,
        current,
        pf,
        efficiency,
        torque,
    )
    args.output.write_text(csv_text, encoding="utf-8")
    logger = Logger.create(Config.create(config_file_path=None))
    logger.info(
        "teacher performance curve saved: %s (%d points)",
        args.output,
        rpm.shape[0],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
