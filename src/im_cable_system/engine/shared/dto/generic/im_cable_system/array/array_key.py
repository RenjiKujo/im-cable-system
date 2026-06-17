"""Array layout keys for the IM cable system (Enum).

Enumerates keys used in
:class:`~im_cable_system.engine.shared.dto.generic.im_cable_system.array.array_layout_dto.ArrayLayoutDto`
``arrays`` and ``reference_axes``.

Note:
    Layout contract validation is performed in
    :class:`~im_cable_system.engine.shared.dto.generic.im_cable_system.array.array_layout_dto.ArrayLayoutDto`
    ``__post_init__`` (this module defines enumeration members only).
"""

from __future__ import annotations

from enum import Enum


class ArrayKey(str, Enum):
    """Keys for array layouts in the IM cable system.

    **Independent variables (reference-axis candidates)**
        - ``SLIP``: Slip
        - ``FREQUENCY``: Frequency [Hz]
        - ``INPUT_LINE_VOLTAGE``: Input line-to-line voltage

    **Cable input currents (results, not reference axes)**
        - ``INPUT_LINE_CURRENT``: Cable input line current [A]. Computed by
          the simulation; never used as a reference axis.

    **IM currents (may be merged across iterations)**
        - ``IM_INPUT_CURRENT``, ``IM_PRIMARY_CURRENT``, ``IM_EXCITATION_CURRENT``:
          Phase currents [A] at each node

    **IM secondary currents (layout keys split by cage count)**
        - ``SINGLE_CAGE_IM_SECONDARY_CURRENT``: Single-cage secondary current
          [A]. On the circuit model, ``im_secondary_base`` / ``load`` / ``total``
          share the same value, so the layout uses this single key.
        - ``DOUBLE_CAGE_IM_SECONDARY_INNER_CURRENT`` / ``OUTER``: Inner and
          outer branch secondary currents [A] for double-cage models (map to
          ``im_cable_system.engine.shared.dto.generic.im_cable_system.im.ImSecondaryCageBranchType``
          INNER / OUTER).

    **Pi-type cable (pie model contract)**
        - ``CONDUCTOR_CURRENT_PIE_SINGLE``: Conductor current (key ``pie_single``)
        - ``GROUND_CURRENT_PIE_UPSTREAM`` / ``DOWNSTREAM``: Upstream and
          downstream ground currents

    **Cable phase currents (match ``ItmCableVoltageCurrentDto`` attribute names)**
        - ``INPUT_PHASE_CURRENT``: Cable input phase current (same node as
          phase voltage)
        - ``END_POINT_PHASE_CURRENT``: Cable end-point / IM input phase current

    Only independent inputs allowed as reference axes appear in
    :meth:`reference_axes_members`. All current-type keys are simulation
    results and are excluded from reference axes.

    Note:
        When adding ``temperature`` or ``time`` in the future, update members
        and :meth:`reference_axes_members` accordingly.
    """

    # Reference-axis candidates (independent inputs)
    SLIP = "slip"
    FREQUENCY = "frequency"
    INPUT_LINE_VOLTAGE = "input_line_voltage"

    # Cable input line current (result of simulation; not a reference axis)
    INPUT_LINE_CURRENT = "input_line_current"

    # IM currents (merged from simulation results)
    IM_INPUT_CURRENT = "im_input_current"
    IM_PRIMARY_CURRENT = "im_primary_current"
    IM_EXCITATION_CURRENT = "im_excitation_current"

    # IM secondary currents (layout does not split base/load/total)
    SINGLE_CAGE_IM_SECONDARY_CURRENT = "single_cage_im_secondary_current"
    DOUBLE_CAGE_IM_SECONDARY_INNER_CURRENT = (
        "double_cage_im_secondary_inner_current"
    )
    DOUBLE_CAGE_IM_SECONDARY_OUTER_CURRENT = (
        "double_cage_im_secondary_outer_current"
    )

    # Pi-type cable: pie_cable_model_builder / ItmCableVoltageCurrentDto contract
    CONDUCTOR_CURRENT_PIE_SINGLE = "conductor_current.pie_single"
    GROUND_CURRENT_PIE_UPSTREAM = "ground_current.pie_upstream"
    GROUND_CURRENT_PIE_DOWNSTREAM = "ground_current.pie_downstream"

    # Cable phase currents (flat keys from get_currents_for_array_layout)
    INPUT_PHASE_CURRENT = "input_phase_current"
    END_POINT_PHASE_CURRENT = "end_point_phase_current"

    @classmethod
    def reference_axes_members(cls) -> tuple[ArrayKey, ...]:
        """Members allowed as reference axes (independent input variables).

        Currents are never allowed as reference axes; they are simulation
        results.
        """
        return (
            cls.SLIP,
            cls.FREQUENCY,
            cls.INPUT_LINE_VOLTAGE,
        )

    @classmethod
    def reference_axis_values(cls) -> frozenset[str]:
        """Set of key strings allowed as reference axes."""
        return frozenset(m.value for m in cls.reference_axes_members())

    @classmethod
    def all_array_key_values(cls) -> frozenset[str]:
        """Set of key strings allowed in ``arrays`` (enum member values only)."""
        return frozenset(m.value for m in cls)
