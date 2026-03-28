import os
from logging.config import fileConfig

from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool

from alembic import context

# Load DATABASE_URL directly from the environment.
# override=False so an explicitly set DATABASE_URL (e.g. in the Cloud Run Job
# or injected by make migrate) takes precedence over .env.local.
load_dotenv(override=False, dotenv_path=".env.local")
DATABASE_URL = os.environ["DATABASE_URL"]

# The model imports below transitively import core.config which validates
# ALL required env vars (OPENAI_API_KEY, ANTHROPIC_API_KEY, FAL_API_KEY etc.).
# The Cloud Run migration job only has DATABASE_URL — it doesn't need API keys.
# We set dummy values for the vars that core.config checks so the import
# succeeds. These values are never used — alembic only uses DATABASE_URL.
_MIGRATION_ONLY_ENV_DEFAULTS = {
    "OPENAI_API_KEY": "migration-placeholder",
    "ANTHROPIC_API_KEY": "migration-placeholder",
    "FAL_API_KEY": "migration-placeholder",
    "GCP_PROJECT_ID": "migration-placeholder",
    "GCP_STORAGE_BUCKET": "migration-placeholder",
}
for key, value in _MIGRATION_ONLY_ENV_DEFAULTS.items():
    os.environ.setdefault(key, value)

# Model imports needed for autogenerate support (alembic revision --autogenerate).
from core.auth import models  # noqa: F401, E402
from core.common import ORMBase  # noqa: E402

# from core.comic_builder import models as comic_builder_models  # noqa: F401
from core.story_engine import models as story_engine_models  # noqa: F401, E402

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config
config.set_main_option("sqlalchemy.url", DATABASE_URL)
print("DATABASE_URL: ", config.get_main_option("sqlalchemy.url"))

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel

# target_metadata = mymodel.Base.metadata
target_metadata = ORMBase.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

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

    In this scenario we need to create an Engine
    and associate a connection with the context.

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
