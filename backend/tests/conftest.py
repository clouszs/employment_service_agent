"""测试公共 Fixtures：数据库会话、测试用户、FastAPI TestClient。"""

from __future__ import annotations

import os
import sys

# 确保 backend 目录在 sys.path 中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.base import Base


# 使用 SQLite 内存数据库做单元测试（不依赖 MySQL）
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def test_engine():
    """创建测试用内存数据库引擎。"""
    engine = create_engine(TEST_DATABASE_URL, echo=False)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(test_engine):
    """每个测试函数使用独立事务，自动回滚。"""
    SessionLocal = sessionmaker(bind=test_engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture()
def client():
    """FastAPI TestClient，用于测试路由层。"""
    from fastapi.testclient import TestClient

    # 使用环境变量覆盖数据库连接，确保测试使用 SQLite
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL
    os.environ["AGENT_ENABLED"] = "false"
    os.environ["REDIS_URL"] = "redis://localhost:6379/0"

    from app.main import app

    with TestClient(app) as client:
        yield client
