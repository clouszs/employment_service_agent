"""数据库引擎、会话工厂与依赖注入。"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

# 引擎：连接池 + 断线自动重连(pool_pre_ping)
# connect_args 用于传递 PyMySQL 特定参数
engine = create_engine(
    settings.database_url,
    echo=settings.db_echo,
    pool_size=settings.db_pool_size,
    pool_recycle=settings.db_pool_recycle,
    pool_pre_ping=True,
    connect_args={
        "charset": settings.db_charset,
    },
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    """FastAPI 依赖：每请求一个会话，结束自动关闭。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
