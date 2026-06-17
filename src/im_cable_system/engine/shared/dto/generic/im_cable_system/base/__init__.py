"""Internal base types for name/ID implementations (non-public package).

Implementation:
  - ``base_name_id``: ``BaseNameId`` and validation helpers (for ``im`` / ``cable``
    name DTOs only)

Do not import from outside this layer. Use the ``generic.im_cable_system`` export
for name DTOs. This ``__init__.py`` is not a public export (no ``__all__``).
"""
