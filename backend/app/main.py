"""FastAPI 应用入口。

启动方式（任选其一）：
    1) 命令行(推荐，带热重载)：cd backend && uvicorn app.main:app --reload
    2) 模块方式：           cd backend && python -m app.main
    3) 直接运行本文件 / IDE 点运行：python app/main.py
文档：http://127.0.0.1:8000/docs
"""

import os
import sys
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
# 让"直接运行本文件"也能找到 app 包：把 backend 目录(本文件上两级)加入 sys.path
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.langsmith_setup import setup_langsmith
from app.core.response import register_exception_handlers
from app.routers import (
    auth,
    categories,
    conversations,
    documents,
    eval_cases,
    faqs,
    feedback,
    health,
    index_tasks,
    messages,
    qa,
    query_logs,
    roles,
    sensitive_words,
    stats,
    synonyms,
    unanswered,
    users,
)

app = FastAPI(
    title=settings.app_name,
    debug=settings.app_debug,
    description="高校智慧就业服务平台 - AI问答模块后端 API",
    version="0.1.0",
)

# LangSmith 全局追踪初始化（从 settings 导出 LANGSMITH_*/LANGCHAIN_* 环境变量）
setup_langsmith()

# CORS（开发期放开，生产应收紧）
# 注意：allow_credentials=True 时，allow_origins 不能用 "*"，必须指定具体域名
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite 开发服务器
        "http://localhost:3000",  # 备用前端端口
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
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


@app.get("/")
def root() -> dict:
    return {"message": f"{settings.app_name} API 运行中，文档见 /docs"}


if __name__ == "__main__":
    # 直接运行本文件时启动服务（开发用）。
    # 监听地址由 .env 的 SERVER_HOST 控制：
    #   127.0.0.1 = 仅本机访问（默认，安全）
    #   0.0.0.0   = 允许局域网其他设备直接访问后端 8000
    # 注意：直接运行不带热重载；想改代码自动重启请用：uvicorn app.main:app --reload
    import uvicorn

    uvicorn.run(app, host=settings.server_host, port=settings.server_port)
