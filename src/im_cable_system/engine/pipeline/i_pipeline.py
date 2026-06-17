"""Common interface for simulation pipelines.

Defines the **minimal contract shared across simulation modes** (construction
and execution).

The type of runtime input passed to :meth:`run` from Workflow (or
similar callers) is defined per pipeline kind via the type parameter
``PipelineInputT_contra``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from im_cable_system.engine.shared.config import IConfig, ILogger

PipelineInputT_contra = TypeVar(
    "PipelineInputT_contra",
    contravariant=True,
)
OutputDtosT_co = TypeVar("OutputDtosT_co", covariant=True)


class IPipeline(
    Generic[PipelineInputT_contra, OutputDtosT_co],
    ABC,
):
    """Common pipeline interface.

    Typical flow:
        1. Obtain a pipeline instance via :meth:`create` (stages are built and
           injected at construction time).
        2. Call :meth:`run` with runtime input (executes the wired
           stages and returns output DTOs).

    Type parameters:
        PipelineInputT_contra: Argument type of :meth:`run` (contravariant).
        OutputDtosT_co: Collection DTO return type of :meth:`run` (covariant).

    Use separate pipeline classes when entry input types differ.
    """

    @classmethod
    @abstractmethod
    def create(
        cls,
        config: IConfig,
        logger: ILogger,
    ) -> IPipeline[PipelineInputT_contra, OutputDtosT_co]:
        """Factory method that constructs a pipeline instance.

        Args:
            config: Configuration.
            logger: Logger.

        Returns:
            New pipeline instance (interface type).
        """

    @abstractmethod
    def run(
        self,
        input: PipelineInputT_contra,
    ) -> OutputDtosT_co:
        """Run the pipeline and return output-side DTO collection.

        Args:
            input: Runtime input from Workflow (job specs, file bundles, etc.).
                Type follows the concrete pipeline's ``PipelineInputT_contra``.

        Returns:
            Collection DTO (concrete pipeline's ``OutputDtosT_co``).
        """
