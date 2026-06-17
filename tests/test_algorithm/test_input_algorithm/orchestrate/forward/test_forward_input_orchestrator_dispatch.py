"""``ForwardInputOrchestrator`` のステージ呼び出し順 / 失敗時の停止挙動テスト。

依存（loader / assembler / job_spec_validator / input_dto_validator）を
すべて mock 化し、``build_input_dto`` が
``_validate_job_spec → _load_data → _assemble_input_dto → _validate_input_dto``
の順で呼ばれること、および途中で失敗した場合は以降のステージが呼ばれない
ことを契約として固定する。``reference_axes`` の値はこのフローに影響しない
ため、両モード共通で 1 系統だけ検証する。
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from im_cable_system.engine.algorithm.input_algorithm.orchestrate.forward import (  # noqa: E501
    ForwardInputOrchestrator,
)


def _make_orchestrator(
    *,
    loader: MagicMock,
    assembler: MagicMock,
    job_spec_validator: MagicMock,
    input_dto_validator: MagicMock,
) -> ForwardInputOrchestrator:
    return ForwardInputOrchestrator(
        config=MagicMock(),
        logger=MagicMock(),
        loader=loader,
        assembler=assembler,
        job_spec_validator=job_spec_validator,
        input_dto_validator=input_dto_validator,
    )


class TestBuildInputDtoStageOrder:
    """4 ステージが規定の順序で呼ばれることを確認する。"""

    def test_calls_four_stages_in_order_on_happy_path(self) -> None:
        spec = MagicMock(name="spec")
        loaded = MagicMock(name="loaded")
        assembled = MagicMock(name="assembled")

        parent = MagicMock()
        parent.job_spec_validator = MagicMock()
        parent.loader = MagicMock()
        parent.assembler = MagicMock()
        parent.input_dto_validator = MagicMock()
        parent.loader.load.return_value = loaded
        parent.assembler.assemble.return_value = assembled

        orch = _make_orchestrator(
            loader=parent.loader,
            assembler=parent.assembler,
            job_spec_validator=parent.job_spec_validator,
            input_dto_validator=parent.input_dto_validator,
        )

        result = orch.build_input_dto(spec)

        assert result is assembled
        parent.job_spec_validator.validate.assert_called_once_with(spec)
        parent.loader.load.assert_called_once_with(spec)
        parent.assembler.assemble.assert_called_once_with(loaded_data=loaded)
        parent.input_dto_validator.validate.assert_called_once_with(assembled)
        call_order = [name for name, _, _ in parent.mock_calls]
        assert call_order == [
            "job_spec_validator.validate",
            "loader.load",
            "assembler.assemble",
            "input_dto_validator.validate",
        ]


class TestBuildInputDtoShortCircuitOnFailure:
    """前段が失敗したら後段は呼ばれないことを確認する。"""

    def test_job_spec_validator_failure_short_circuits(self) -> None:
        spec = MagicMock(name="spec")
        job_spec_validator = MagicMock()
        job_spec_validator.validate.side_effect = ValueError("bad spec")
        loader = MagicMock()
        assembler = MagicMock()
        input_dto_validator = MagicMock()
        orch = _make_orchestrator(
            loader=loader,
            assembler=assembler,
            job_spec_validator=job_spec_validator,
            input_dto_validator=input_dto_validator,
        )

        with pytest.raises(ValueError, match="bad spec"):
            orch.build_input_dto(spec)

        loader.load.assert_not_called()
        assembler.assemble.assert_not_called()
        input_dto_validator.validate.assert_not_called()

    def test_loader_failure_short_circuits(self) -> None:
        spec = MagicMock(name="spec")
        job_spec_validator = MagicMock()
        loader = MagicMock()
        loader.load.side_effect = ValueError("bad file")
        assembler = MagicMock()
        input_dto_validator = MagicMock()
        orch = _make_orchestrator(
            loader=loader,
            assembler=assembler,
            job_spec_validator=job_spec_validator,
            input_dto_validator=input_dto_validator,
        )

        with pytest.raises(ValueError, match="bad file"):
            orch.build_input_dto(spec)

        job_spec_validator.validate.assert_called_once_with(spec)
        assembler.assemble.assert_not_called()
        input_dto_validator.validate.assert_not_called()

    def test_assembler_failure_short_circuits(self) -> None:
        spec = MagicMock(name="spec")
        loaded = MagicMock(name="loaded")
        job_spec_validator = MagicMock()
        loader = MagicMock()
        loader.load.return_value = loaded
        assembler = MagicMock()
        assembler.assemble.side_effect = ValueError("bad dto")
        input_dto_validator = MagicMock()
        orch = _make_orchestrator(
            loader=loader,
            assembler=assembler,
            job_spec_validator=job_spec_validator,
            input_dto_validator=input_dto_validator,
        )

        with pytest.raises(ValueError, match="bad dto"):
            orch.build_input_dto(spec)

        job_spec_validator.validate.assert_called_once_with(spec)
        loader.load.assert_called_once_with(spec)
        input_dto_validator.validate.assert_not_called()

    def test_input_dto_validator_failure_propagates(self) -> None:
        spec = MagicMock(name="spec")
        loaded = MagicMock(name="loaded")
        assembled = MagicMock(name="assembled")
        job_spec_validator = MagicMock()
        loader = MagicMock()
        loader.load.return_value = loaded
        assembler = MagicMock()
        assembler.assemble.return_value = assembled
        input_dto_validator = MagicMock()
        input_dto_validator.validate.side_effect = ValueError("bad si unit")

        orch = _make_orchestrator(
            loader=loader,
            assembler=assembler,
            job_spec_validator=job_spec_validator,
            input_dto_validator=input_dto_validator,
        )

        with pytest.raises(ValueError, match="bad si unit"):
            orch.build_input_dto(spec)

        job_spec_validator.validate.assert_called_once_with(spec)
        loader.load.assert_called_once_with(spec)
        assembler.assemble.assert_called_once_with(loaded_data=loaded)
        input_dto_validator.validate.assert_called_once_with(assembled)
