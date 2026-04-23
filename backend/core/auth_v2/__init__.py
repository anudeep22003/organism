"""Auth package root.

Keep this module side-effect free so non-runtime consumers such as Alembic can
import `core.auth_v2.*` modules without triggering runtime config imports.
"""

__all__: list[str] = []
