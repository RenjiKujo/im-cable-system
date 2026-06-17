"""Array layout DTO for model grids.

Defines shape via reference axes (reference_axes) and holds per-axis arrays.
Only CARTESIAN layout is supported.

Note:
    The closed vocabulary for axis names
    (:class:`~im_cable_system.engine.shared.dto.generic.im_cable_system.array.array_key.ArrayKey`)
    is provided by the ``array`` package.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from im_cable_system.engine.shared.dto.generic.im_cable_system.array.array_key import (  # noqa: E501
    ArrayKey,
)
from im_cable_system.engine.shared.dto.generic.interfaces.i_value_with_unit_dto import (  # noqa: E501
    IArrayWithUnitDto,
)


@dataclass(frozen=True)
class ArrayLayoutDto:
    """Model array layout (axis names and array shapes). CARTESIAN with required reference axes.

    Defines multidimensional axes and holds one array per axis.
    Reference-axis combinations (Cartesian product) determine shape;
    non-reference arrays must match that shape.

    Attributes:
        arrays: Mapping from axis key to array DTO.
            Each value is a unit-bearing array DTO with a raw, non-broadcast array.
            Reference axes are 1-D; others are multidimensional with the same shape as
            the reference axes. Key insertion order defines axis order.
        reference_axes: List of reference axis keys (must not be empty).
            Example: for two reference axes with lengths 3 and 2,
            non-reference arrays have shape ``(3, 2)`` and the product size is 6.
    """

    arrays: dict[ArrayKey, IArrayWithUnitDto]
    reference_axes: list[ArrayKey]

    @property
    def axes(self) -> list[ArrayKey]:
        """Axis keys in ``arrays`` key order.

        Returns:
            list[ArrayKey]: Axis keys.
        """
        return list(self.arrays.keys())

    @property
    def shape(self) -> tuple[int, ...]:
        """Shape of the reference axes.

        Returns:
            tuple[int, ...]: Length of each reference axis, in reference-axis order.

        Raises:
            ValueError: If reference axes are missing or not present in ``arrays``.
        """
        return self.get_reference_shape()

    def get_reference_shape(self) -> tuple[int, ...]:
        """Return the shape of the reference axes.

        Reference arrays are not flattened; lengths are taken from each 1-D array.

        Returns:
            tuple[int, ...]: Length tuple for reference axes.

        Raises:
            ValueError: If reference axes are missing or not present in ``arrays``.
        """
        if not self.reference_axes:
            raise ValueError("reference_axes must be specified")
        return tuple(
            len(self.arrays[ref_axis].get_value())
            for ref_axis in self.reference_axes
        )

    def get_reference_total_length(self) -> int:
        """Return the total number of points in the reference Cartesian product.

        Returns:
            int: Product of reference-axis lengths.

        Raises:
            ValueError: If reference axes are missing.
        """
        ref_shape = self.get_reference_shape()
        total_length = 1
        for length in ref_shape:
            total_length *= length
        return total_length

    def __post_init__(self) -> None:
        """Validate structure, CARTESIAN shape, and IM cable-system axis contract.

        Raises:
            ValueError: If any contract check fails.
        """
        self._validate_arrays_structure()
        self._validate_reference_axes_required()

        for axis_name, dto in self.arrays.items():
            self._validate_array_dto(axis_name, dto)

        self._validate_cartesian_mode()
        self._validate_im_cable_reference_axes_contract()

    def _validate_arrays_structure(self) -> None:
        """Validate basic structure of ``arrays``.

        Raises:
            ValueError: If not a dict, empty, or keys are not :class:`ArrayKey`.
        """
        if not isinstance(self.arrays, dict):
            raise ValueError("arrays must be a dict")
        if len(self.arrays) == 0:
            raise ValueError("arrays must not be empty")

        for key in self.arrays:
            if not isinstance(key, ArrayKey):
                raise ValueError(
                    f"arrays key '{key}' must be ArrayKey, got {type(key).__name__}"
                )

    def _validate_reference_axes_required(self) -> None:
        """Validate that ``reference_axes`` is required and non-empty.

        Raises:
            ValueError: If None or an empty list.
        """
        if self.reference_axes is None or len(self.reference_axes) == 0:
            raise ValueError(
                "reference_axes is required and must not be an empty list"
            )

    def _validate_array_dto(
        self, axis_name: ArrayKey, dto: IArrayWithUnitDto
    ) -> None:
        """Validate a single array DTO.

        Reference axes must be 1-D. Non-reference shape is checked in
        :meth:`_validate_cartesian_mode`.

        Raises:
            ValueError: If type, elements, or dimensions violate the contract.
        """
        if not isinstance(dto, IArrayWithUnitDto):
            raise ValueError(f"arrays['{axis_name}'] must be IArrayWithUnitDto")
        arr = dto.get_value()
        if not isinstance(arr, np.ndarray):
            raise ValueError(
                f"arrays['{axis_name}'].get_value() must return a numpy array"
            )
        if arr.dtype.kind not in ("f", "i", "c"):
            raise ValueError(f"arrays['{axis_name}'] elements must be numeric")
        if arr.size <= 0:
            raise ValueError(
                f"arrays['{axis_name}'] must have a positive number of elements "
                f"(current size: {arr.size})"
            )
        is_reference_axis = axis_name in self.reference_axes
        if is_reference_axis and arr.ndim != 1:
            raise ValueError(
                f"arrays['{axis_name}'] must be a 1-D array "
                f"(current ndim: {arr.ndim})"
            )

    def _validate_cartesian_mode(self) -> None:
        """Validate CARTESIAN consistency of reference and non-reference axes.

        - Reference axes are 1-D and match declared lengths.
        - Non-reference arrays have the same multidimensional shape as the
          reference product (flattened 1-D only is not allowed).

        Raises:
            ValueError: If any contract check fails.
        """
        if not self.reference_axes:
            raise ValueError("reference_axes must be specified")
        for ref_axis in self.reference_axes:
            if ref_axis not in self.arrays:
                raise ValueError(
                    f"reference axis '{ref_axis}' is not present in arrays"
                )
        ref_shape = self.get_reference_shape()
        ref_lengths = list(ref_shape)
        for axis_name, dto in self.arrays.items():
            arr = dto.get_value()
            if axis_name in self.reference_axes:
                ref_axis_index = self.reference_axes.index(axis_name)
                expected_length = ref_lengths[ref_axis_index]
                if arr.ndim != 1:
                    raise ValueError(
                        "reference axis arrays must be 1-D. "
                        f"axis '{axis_name}' ndim: {arr.ndim}"
                    )
                if len(arr) != expected_length:
                    raise ValueError(
                        "reference axis length does not match reference shape. "
                        f"axis '{axis_name}' length: {len(arr)}, "
                        f"expected: {expected_length} "
                        f"(reference_axes: {self.reference_axes})"
                    )
                continue
            if arr.shape != ref_shape:
                raise ValueError(
                    "non-reference arrays must be multidimensional arrays whose "
                    "shape exactly matches the reference shape. "
                    f"axis '{axis_name}' shape: {arr.shape}, "
                    f"reference shape: {ref_shape} "
                    f"(reference_axes: {self.reference_axes})"
                )

    def _validate_im_cable_reference_axes_contract(self) -> None:
        """Validate that ``reference_axes`` are independent-input axes only.

        ``arrays`` key types are checked in :meth:`_validate_arrays_structure`.
        This check ensures ``reference_axes`` matches
        :meth:`ArrayKey.reference_axes_members`.

        Raises:
            ValueError: If any reference axis is not an allowed independent input.
        """
        ref_allowed = frozenset(ArrayKey.reference_axes_members())
        bad_reference_axes = sorted(
            axis for axis in self.reference_axes if axis not in ref_allowed
        )
        if bad_reference_axes:
            raise ValueError(
                "reference_axes may only contain independent input variables "
                "(same set as ArrayKey.reference_axes_members). "
                f"Allowed: {sorted(axis.value for axis in ref_allowed)}. "
                f"Invalid axes: {[axis.value for axis in bad_reference_axes]}"
            )
