"""Alembic environment for OpenFatture.

Runs programmatically from :mod:`openfatture.storage.schema`, which passes an
open connection in ``config.attributes["connection"]``, or from the
``alembic`` CLI during development, which uses the configured database URL.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from openfatture.payment.domain import models as payment_models
from openfatture.storage.database import models as storage_models
from openfatture.storage.database.base import Base

# Importing the model modules registers every table on Base.metadata.
_REGISTERED_MODEL_MODULES = (payment_models, storage_models)

config = context.config
target_metadata = Base.metadata

if config.attributes.get("connection") is None:
    from openfatture.platform.config import get_settings

    config.set_main_option("sqlalchemy.url", get_settings().database_url)
    if config.config_file_name is not None:
        fileConfig(config.config_file_name)


def run_migrations_offline() -> None:
    """Emit SQL for the configured URL without a live connection."""
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Migrate through the provided connection, or open one from the URL."""
    connection = config.attributes.get("connection")
    if connection is not None:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()
        return

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as owned:
        context.configure(connection=owned, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
