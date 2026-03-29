from logging.config import fileConfig

from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool

from alembic import context

# Load DATABASE_URL from .env.local if present.
# override=False so an explicitly set DATABASE_URL (Cloud Run Job, CI, make migrate)
# takes precedence over the file. Missing file is silently ignored.
load_dotenv(override=False, dotenv_path=".env.local")

# DatabaseSettings only requires DATABASE_URL — no API keys, no GCP vars.
#
# Why this works cleanly now:
#   1. AppSettings (the full singleton in config.py) is never imported here,
#      so the API key validation in AppSettings never runs.
#   2. core/services/database.py is now lazy — importing it no longer creates
#      a live engine or DB connection. The engine is only created on the first
#      call to get_async_db_session(), which never happens in alembic context.
#   3. Therefore importing app models below is safe even without API keys set.
#
# Adding a new required var to AppSettings in future requires zero changes here.
from core.config import DatabaseSettings  # noqa: E402

db_settings = DatabaseSettings()  # type: ignore[call-arg]

# Model imports for autogenerate support (alembic revision --autogenerate).
# These drag in core.auth, core.services.database etc. — all safe now.
from core.auth import models  # noqa: F401, E402
from core.common import ORMBase  # noqa: E402

# from core.comic_builder import models as comic_builder_models  # noqa: F401
from core.story_engine import models as story_engine_models  # noqa: F401, E402

# Alembic config object — access to values within the .ini file.
config = context.config
config.set_main_option("sqlalchemy.url", db_settings.database_url)

# Set up loggers from the alembic.ini [loggers] section.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata for autogenerate — includes all registered ORM models.
target_metadata = ORMBase.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    Configures the context with just a URL — no Engine or DBAPI needed.
    Calls to context.execute() emit SQL strings to the output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    Creates an Engine and associates a connection with the context.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
