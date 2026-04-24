import os
from logging.config import fileConfig

from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool

from alembic import context

# Load DATABASE_URL from .env.local if present.
# override=False so an explicitly set DATABASE_URL (Cloud Run Job, CI, make migrate)
# takes precedence over the file. Missing file is silently ignored.
load_dotenv(override=False, dotenv_path=".env.local")

# Read DATABASE_URL directly from the environment — no app imports needed.
#
# We intentionally do NOT import from core.config here. Any import of the
# core.config package (even `from core.config.database import X`) causes Python
# to execute core/config/__init__.py, which imports app.py, which instantiates
# AppSettings() and validates all API keys. The migration job only has
# DATABASE_URL — it doesn't have API keys.
#
# Reading from os.environ directly is simpler, has zero side effects, and is
# the only correct approach when you need exactly one value from the environment.
DATABASE_URL = os.environ["DATABASE_URL"]

# Model imports for autogenerate support (alembic revision --autogenerate).
#
# Import model packages only. Do not import top-level runtime package re-exports
# here: Alembic must register ORM metadata without triggering app settings or any
# other runtime-only initialization.
import core.auth.models as auth_models  # noqa: F401, E402
import core.story_engine.models as story_engine_models  # noqa: F401, E402
from core.common import ORMBase  # noqa: E402

# import core.comic_builder.models as comic_builder_models  # noqa: F401

# Alembic config object — access to values within the .ini file.
config = context.config
config.set_main_option("sqlalchemy.url", DATABASE_URL)

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
