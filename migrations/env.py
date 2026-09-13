from logging.config import fileConfig

from alembic import context
from flask import current_app

from app import db

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = db.metadata


def get_engine():
    try:
        return current_app.extensions["migrate"].db.engine
    except (TypeError, AttributeError, KeyError):
        return current_app.extensions["sqlalchemy"].db.engine


def get_engine_url():
    return str(get_engine().url).replace("%", "%%")


def run_migrations_offline():
    url = get_engine_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = get_engine()
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
