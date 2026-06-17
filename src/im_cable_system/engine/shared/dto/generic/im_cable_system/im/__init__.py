"""Induction motor (IM) related DTOs (internal package).

Implementation:
  - ``im_dto`` / ``im_performance_curve_catalog_dto``: Input and catalog DTOs
  - ``im_*_model_dto`` / ``im_type``: Circuit model types and enumerations
  - ``im_name`` and related modules: Opaque identifiers

For cross-layer use, import only from the ``generic.im_cable_system`` export.
This ``__init__.py`` is not a public export (no ``__all__``).
"""
