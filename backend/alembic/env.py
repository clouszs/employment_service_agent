"""Alembic 迁移环境配置。

约定说明（放在此处而非 alembic.ini，因为 alembic.ini 由 configparser 以系统
locale(GBK) 编码读取，含中文会导致命令崩溃；而本文件是 Python 源码，按 UTF-8 读取）：

1. 数据库连接串不写在 alembic.ini，而是在本文件用 settings.database_url 动态覆盖，
   避免把数据库密码明文存进版本库。
2. 迁移版本脚本输出目录由 alembic.ini 的 version_locations 指定为 backend/migrations/，
   而非默认的 alembic/versions/。
3. target_metadata 绑定 app.models.Base.metadata，支持 --autogenerate 自动比对模型。
"""

import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# 将 backend 根目录加入 sys.path，便于 import app.*
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings  # noqa: E402
from app.models import Base  # noqa: E402  导入 Base 会触发全部模型注册

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# 用项目配置中的数据库连接串覆盖 alembic.ini 的占位值（避免在 ini 中明文存放密码）
config.set_main_option("sqlalchemy.url", settings.database_url)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

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
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
