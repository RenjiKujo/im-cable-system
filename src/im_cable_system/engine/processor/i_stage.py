"""Common stage interface for the simulation engine.

``IStage`` is the sole **leaf contract** at the ``processor`` package root.
There is no ``__init__.py`` at the ``processor`` root; public entry points per
stage kind are ``input_stage``, ``execute_stage``, and ``output_stage``.

Import ``IStage`` from outside the layer (e.g. pipeline) as::

    from im_cable_system.engine.processor.i_stage import IStage

Do not add a separate subpackage for this module (e.g. ``stage_interface``).

Minimal contract for upper components such as Pipeline:

- **create**: Factory method that constructs a stage instance.
- **process**: Accepts stage input and returns output (often a collection DTO).

All stage kinds (Input / Execute / Output) implement ``IStage``.
There are no derived interfaces such as ``IInputStage``; input and output are
distinguished by type parameters. Pipelines refer only to ``IStage[...]``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from im_cable_system.engine.shared.config import IConfig, ILogger

InputT_contra = TypeVar("InputT_contra", contravariant=True)
OutputT_co = TypeVar("OutputT_co", covariant=True)


class IStage(Generic[InputT_contra, OutputT_co], ABC):
    """Common interface for all stages.

    Every stage implements ``create`` and ``process``.

    Type parameters:
        InputT_contra: Argument type of ``process``. For InputStage this is often
            a job spec (e.g. ``ForwardJobSpecs``), not ``InputDtos``.
            Execute / Output stages usually take collection DTOs.
        OutputT_co: Return type of ``process``.

    Variance (for static type checkers):
        InputT_contra (contravariant): An implementation that accepts a wider
            input type may be used where a narrower ``IStage`` input is expected.
        OutputT_co (covariant): An implementation that returns a more specific
            type may be used where a wider ``IStage`` output is expected.

    Example (im_cable_system, forward_by_cartesian_grid)::

        input_dtos = input_stage.process(job_specs)
        itm_dtos = execute_stage.process(input_dtos)
        output_dtos = output_stage.process(itm_dtos)
    """

    @classmethod
    @abstractmethod
    def create(
        cls,
        config: IConfig,
        logger: ILogger,
    ) -> IStage[InputT_contra, OutputT_co]:
        """Factory method that constructs a stage instance.

        Args:
            config: Configuration required to build the stage.
            logger: Logger instance.

        Returns:
            New stage instance (interface type).
        """

    @abstractmethod
    def process(self, stage_input: InputT_contra) -> OutputT_co:
        """Run the stage.

        Args:
            stage_input: Stage input (job spec, collection DTO, etc.; implementation-specific).

        Returns:
            Stage output (often a collection DTO).

        Example (im_cable_system):
            - InputStage: ``ForwardJobSpecs`` → ``InputDtos``
            - ExecuteStage: ``InputDtos`` → ``ItmDtos``
            - OutputStage: ``ItmDtos`` → ``OutputDtos``
        """
