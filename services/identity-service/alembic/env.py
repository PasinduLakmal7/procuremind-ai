import sys
from pathlib import Path
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# Ensure service directory and workspace root are in python path
service_root = Path(__file__).resolve().parents[1]
workspace_root = Path(__file__).resolve().parents[3]
if str(service_root) not in sys.path:
    sys.path.insert(0, str(service_root))
if str(workspace_root) not in sys.path:
    sys.path.insert(0, str(workspace_root))

from app.core.config import settings
from app.models import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def get_url():
    import os
    x_args = context.get_x_argument(as_dictionary=True)
    if "db_url" in x_args:
        return x_args["db_url"]
    return os.getenv("DATABASE_URL") or settings.DATABASE_URL


def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

