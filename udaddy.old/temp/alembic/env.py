# alembic/env.py
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
import sys

# 将应用目录添加到Python路径中，以便Alembic能找到你的模型
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.core.config import settings
from app.db.base import Base # 导入你的模型基类

# 这是Alembic的主配置对象，代表了.ini文件
config = context.config

# 从.ini文件配置日志记录
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 设置目标元数据，Alembic将根据这个来检测模型变更
target_metadata = Base.metadata

# 从应用的配置中设置sqlalchemy.url
config.set_main_option('sqlalchemy.url', settings.DATABASE_URL)

def run_migrations_offline() -> None:
    """在“离线”模式下运行迁移。"""
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
    """在“在线”模式下运行迁移。"""
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