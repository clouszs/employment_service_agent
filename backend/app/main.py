"""FastAPI 应用入口。

启动方式（任选其一）：
    1) 命令行(推荐，带热重载)：cd backend && uvicorn app.main:app --reload
    2) 模块方式：           cd backend && python -m app.main
    3) 直接运行本文件 / IDE 点运行：python app/main.py
文档：http://127.0.0.1:8000/docs
"""

import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import find_dotenv, load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.langsmith_setup import setup_langsmith
from app.core.logging_config import setup_logging
from app.core.response import register_exception_handlers
from app.routers import (
    agent,
    app_config,
    announcements,
    auth,
    career,
    categories,
    conversations,
    documents,
    eval_cases,
    faqs,
    feedback,
    health,
    index_tasks,
    kb_health,
    llm_cost,
    messages,
    qa,
    query_logs,
    refusal,
    roles,
    sensitive_words,
    stats,
    synonyms,
    unanswered,
    user_favorite,
    users,
    admin_conversations,
)

load_dotenv(find_dotenv())

# 让"直接运行本文件"也能找到 app 包：把 backend 目录(本文件上两级)加入 sys.path
_BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

logger = logging.getLogger(__name__)


# ==================== 生命周期管理 ====================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理（FastAPI >= 0.93 推荐模式）。"""
    # 启动时初始化
    setup_logging()
    setup_langsmith()
    from app.monitor.scheduler import setup_scheduler

    setup_scheduler()

    # 初始化默认问答配置
    from app.services.app_config_service import seed_qa_defaults
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        seed_qa_defaults(db)
    except Exception as e:  # pragma: no cover - 防御性降级
        logger.warning("初始化默认问答配置失败: %s", str(e))
    finally:
        db.close()

    logger.info("应用启动完成，环境=%s，debug=%s", settings.app_env, settings.app_debug)
    yield
    # 关闭时优雅释放资源
    logger.info("正在关闭应用，释放资源...")
    try:
        from app.core.database import engine

        engine.dispose()
        logger.info("数据库连接池已释放")
    except Exception as e:
        logger.warning("释放数据库连接池失败: %s", e)
    from app.monitor.scheduler import shutdown_scheduler

    shutdown_scheduler()
    logger.info("应用已关闭")


# ==================== FastAPI 实例 ====================


app = FastAPI(
    title=settings.app_name,
    debug=settings.app_debug,
    description="高校智慧就业服务平台 - AI问答模块后端 API",
    version="0.1.0",
    lifespan=lifespan,
)


# CORS：根据环境变量动态配置
# 开发环境允许 localhost；生产环境只放前端域名（通过 APP_ENV 区分）
if settings.app_env == "production":
    _cors_origins = [
        # 生产环境：按实际部署的前端域名添加
        # 示例："https://career.example.com",
    ]
else:
    _cors_origins = [
        "http://localhost:5173",  # Vite 开发服务器
        "http://localhost:3000",  # 备用前端端口
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",  # Swagger UI / 自测
        "http://localhost:8000",  # 本地直连
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局异常处理
register_exception_handlers(app)

# 路由
app.include_router(health.router, prefix=settings.api_prefix)
app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(users.router, prefix=settings.api_prefix)
app.include_router(roles.router, prefix=settings.api_prefix)
app.include_router(categories.router, prefix=settings.api_prefix)
app.include_router(documents.router, prefix=settings.api_prefix)
app.include_router(index_tasks.router, prefix=settings.api_prefix)
app.include_router(faqs.router, prefix=settings.api_prefix)
app.include_router(synonyms.router, prefix=settings.api_prefix)
# P3 检索问答
app.include_router(qa.router, prefix=settings.api_prefix)
# Agent 对话（渐进式迁移，默认 agent_enabled=False）
app.include_router(agent.router, prefix=settings.api_prefix)
# P5 监控告警
app.include_router(kb_health.router, prefix=settings.api_prefix)
app.include_router(llm_cost.router, prefix=settings.api_prefix)
app.include_router(refusal.router, prefix=settings.api_prefix)
# P4 会话与反馈
app.include_router(conversations.router, prefix=settings.api_prefix)
app.include_router(messages.router, prefix=settings.api_prefix)
# P5 运营·安全·统计
app.include_router(sensitive_words.router, prefix=settings.api_prefix)
app.include_router(query_logs.router, prefix=settings.api_prefix)
app.include_router(stats.router, prefix=settings.api_prefix)
app.include_router(eval_cases.router, prefix=settings.api_prefix)
app.include_router(feedback.router, prefix=settings.api_prefix)
app.include_router(unanswered.router, prefix=settings.api_prefix)
# P2 系统配置/收藏/公告
app.include_router(app_config.router, prefix=settings.api_prefix)
app.include_router(user_favorite.router, prefix=settings.api_prefix)
app.include_router(announcements.router, prefix=settings.api_prefix)
app.include_router(admin_conversations.router, prefix=settings.api_prefix)
# 学生生涯服务：简历/职位/日历
app.include_router(career.router, prefix=settings.api_prefix)


@app.get("/")
def root() -> dict:
    return {"message": f"{settings.app_name} API 运行中，文档见 /docs"}


# ==================== 直接运行入口 ====================


if __name__ == "__main__":
    # 直接运行本文件时启动服务（开发用）。
    # 监听地址由 .env 的 SERVER_HOST 控制：
    #   127.0.0.1 = 仅本机访问（默认，安全）
    #   0.0.0.0   = 允许局域网其他设备直接访问后端 8000
    # 注意：直接运行不带热重载；想改代码自动重启请用：uvicorn app.main:app --reload
    import uvicorn

    uvicorn.run(app, host=settings.server_host, port=settings.server_port)
