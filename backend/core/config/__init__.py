# Import only from app.py — NOT from database.py.
#
# This is the key design decision:
#   - app code does:    from core.config import settings, AppSettings
#     → __init__.py imports from app.py → AppSettings() runs → validates all vars
#
#   - alembic does:     from core.config.database import DatabaseSettings
#     → bypasses __init__.py entirely → app.py is never imported
#     → AppSettings() never runs → no API key validation
#
# If we also imported DatabaseSettings here, alembic could still use
# `from core.config import DatabaseSettings` — but that would also trigger
# this __init__.py, which imports app.py, which instantiates AppSettings().
# So alembic must import directly from core.config.database, not from here.
from core.config.app import AppSettings, settings

__all__ = ["AppSettings", "settings"]
