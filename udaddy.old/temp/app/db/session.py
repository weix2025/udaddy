# app/db/session.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# 创建SQLAlchemy的数据库引擎
# create_engine是SQLAlchemy与数据库建立连接的入口点
engine = create_engine(
    settings.DATABASE_URL,
    # connect_args 是特定于数据库驱动的参数
    # 对于PostgreSQL, check_same_thread是False是默认的
    # 对于SQLite，需要设置为False: {"check_same_thread": False}
)

# 创建一个SessionLocal类
# 这个类的实例将是实际的数据库会话
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)