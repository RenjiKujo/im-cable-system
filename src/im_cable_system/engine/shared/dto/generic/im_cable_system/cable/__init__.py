"""Cable-related DTOs (internal package).

Implementation:
  - ``cable_dto``: Input DTOs
  - ``cable_*_name``: Opaque identifiers
  - ``cable_model_dto`` / ``cable_types_dto``: Closed vocabulary (conductor
    models and pi dictionary keys)

For cross-layer use, import only from the ``generic.im_cable_system`` export.
This ``__init__.py`` is not a public export (no ``__all__``).
"""
