"""Input algorithm package for the IM cable system (``im_cable_system``).

Bundles the algorithms that build and validate ``InputDto`` from
``InputFile``-derived data, split into per-step subpackages. This
package itself is not an import window (it does not define
``__all__``). Layer-external and cross-layer code must import via the
public windows of each subpackage listed below.

Note:
    The module :mod:`i_input_algorithms_orchestrator` directly under
    this package provides the common orchestrator interface
    (:class:`IInputAlgorithmsOrchestrator`) shared by all modes.
    Per-mode interfaces specialize this common interface by extending
    it.

    The common interface is intended only as a base contract for
    defining per-mode interfaces; it is not intended to be received
    directly by layer-external code (e.g., processor / pipeline). Such
    code should reference the **per-mode interface** through the
    public window matching the execution mode
    (``orchestrate.forward`` / ``orchestrate.estimate_params``).
    For that reason, the common interface is not re-exported from
    this package.

    If, in the future, a layer-external component needs to accept any
    Input orchestrator regardless of mode (e.g., a mode-agnostic
    common process), it is reasonable to consider adding a public
    window that exposes the common interface on this package (or on
    ``orchestrate``) at that point and promoting it to a public API.
"""
