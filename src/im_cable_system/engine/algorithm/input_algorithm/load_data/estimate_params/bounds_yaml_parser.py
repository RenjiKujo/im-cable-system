"""パラメータフィット境界 YAML（IM / ケーブル）のロード。

estimate_params の InputStage が `IConfig` から受け取った YAML パスを
:class:`ImParameterFitDescriptorBounds` /
:class:`CableParameterFitDescriptorBounds` に変換する薄いラッパ。

責務:
    - load_data 横断の :func:`load_yaml_root_map` で YAML を読み込む。
    - 各境界 DTO の ``from_estimation_document`` に委譲する。

YAML のスキーマ解釈そのものは
:mod:`im_cable_system.engine.shared.estimate_params_fit_spec` 側の
``from_estimation_document`` が担当する。本モジュールはパスとの結合だけを担う。
"""

from __future__ import annotations

from pathlib import Path

from im_cable_system.engine.algorithm.input_algorithm.load_data.util import (
    load_yaml_root_map,
)
from im_cable_system.engine.shared.estimate_params_fit_spec import (  # noqa: E501
    CableParameterFitDescriptorBounds,
    ImParameterFitDescriptorBounds,
)


def load_im_parameter_fit_descriptor_bounds(
    path: Path,
) -> ImParameterFitDescriptorBounds:
    """IM 境界 YAML を読み、:class:`ImParameterFitDescriptorBounds` を返す。

    Args:
        path: IM 境界 YAML のパス。

    Returns:
        ImParameterFitDescriptorBounds: 解釈結果。

    Raises:
        ValueError: YAML のルートがマッピングでない場合。
    """
    document = load_yaml_root_map(path)
    return ImParameterFitDescriptorBounds.from_estimation_document(document)


def load_cable_parameter_fit_descriptor_bounds(
    path: Path,
) -> CableParameterFitDescriptorBounds:
    """ケーブル境界 YAML を読み、
    :class:`CableParameterFitDescriptorBounds` を返す。

    Args:
        path: ケーブル境界 YAML のパス。

    Returns:
        CableParameterFitDescriptorBounds: 解釈結果。

    Raises:
        ValueError: YAML のルートがマッピングでない場合。
    """
    document = load_yaml_root_map(path)
    return CableParameterFitDescriptorBounds.from_estimation_document(document)
