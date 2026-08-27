"""subprocess を回す薄い皮。HTTP も DB も import しない。

``apps/web/api`` から見た公開窓口。ジョブディレクトリのレイアウト決定・入力保存・
config.yaml のマテリアライズ（``job_layout``）、mode → argv 変換（``command_builder``）、
subprocess の起動・タイムアウト・kill（``executor``）、成果物走査（``artifacts``）、
実行時設定（``settings``）を再エクスポートする。
"""

from apps.web.runner_gateway.artifacts import (
    ArtifactInfo,
    list_artifacts,
    resolve_artifact_path,
)
from apps.web.runner_gateway.command_builder import (
    EstimateParamsInputs,
    ForwardInputs,
    JobInputs,
    JobMode,
    build_command,
)
from apps.web.runner_gateway.executor import (
    ErrorKind,
    ExecutionResult,
    JobStatus,
    RunningJob,
    start_process,
    terminate,
    wait_for_completion,
)
from apps.web.runner_gateway.job_layout import (
    ConfigMaterializeResult,
    JobLayout,
    delete_job_dir,
    materialize_config,
    read_config_timezone,
    save_input_file,
    write_cmd_json,
)
from apps.web.runner_gateway.settings import RunnerGatewaySettings

__all__ = [
    "ArtifactInfo",
    "ConfigMaterializeResult",
    "ErrorKind",
    "EstimateParamsInputs",
    "ExecutionResult",
    "ForwardInputs",
    "JobInputs",
    "JobLayout",
    "JobMode",
    "JobStatus",
    "RunnerGatewaySettings",
    "RunningJob",
    "build_command",
    "delete_job_dir",
    "list_artifacts",
    "materialize_config",
    "read_config_timezone",
    "resolve_artifact_path",
    "save_input_file",
    "start_process",
    "terminate",
    "wait_for_completion",
    "write_cmd_json",
]
