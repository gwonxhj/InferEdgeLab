"""Service-layer helpers for InferEdgeLab.

Keep this package initializer light. Several services are intentionally allowed
to import report/rendering modules, so importing compare_service here can create
cycles during direct module imports.
"""

__all__: list[str] = []
