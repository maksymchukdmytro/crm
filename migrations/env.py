from alembic import context
from sqlalchemy import engine_from_config, pool

from app import models  # noqa: F401 — реєструє таблиці в metadata
from app.config import config as app_config
from app.db import Base

target_metadata = Base.metadata


def run_migrations_offline():
    context.configure(url=app_config.DATABASE_URL, target_metadata=target_metadata, literal_binds=True,
                      compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config({"sqlalchemy.url": app_config.DATABASE_URL}, prefix="sqlalchemy.",
                                     poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
