"""LangSmith 全局追踪初始化。

作用：把 settings 里的 LangSmith 配置导出为 LangChain/LangSmith SDK 在运行时识别的
环境变量，使阶段 1+ 节点上的 @traceable 装饰器自动上报调用链路。

为什么用环境变量而非代码传参：
  LangChain 与 langsmith SDK 在导入/运行时直接读取 LANGSMITH_*/LANGCHAIN_* 环境变量，
  统一在这里设置即"全局生效"；用户改 .env 即可开关或换项目，无需改代码。

调用时机：app 启动时（main.py）调用一次 setup_langsmith()。
"""

from __future__ import annotations

import logging
import os

from app.core.config import settings

logger = logging.getLogger(__name__)


def setup_langsmith() -> bool:
    """根据配置设置 LangSmith 全局环境变量。返回是否启用了追踪。"""
    if not settings.langsmith_enabled:
        # 显式关闭，确保不会因为系统里残留的变量而误开
        os.environ["LANGSMITH_TRACING"] = "false"
        os.environ["LANGCHAIN_TRACING_V2"] = "false"
        logger.info("LangSmith 追踪已关闭（langsmith_enabled=false）")
        return False

    api_key = settings.langsmith_api_key or os.environ.get("LANGSMITH_API_KEY", "")
    if not api_key:
        logger.warning("LangSmith 已启用但未读到 API Key（环境变量 LANGSMITH_API_KEY 为空），追踪不会生效")
        return False

    # 新版 langsmith SDK 读 LANGSMITH_*；LangChain 集成读 LANGCHAIN_*，两套都设置最稳妥
    env = {
        "LANGSMITH_TRACING": "true",
        "LANGSMITH_API_KEY": api_key,
        "LANGSMITH_PROJECT": settings.langsmith_project,
        "LANGSMITH_ENDPOINT": settings.langsmith_endpoint,
        "LANGCHAIN_TRACING_V2": "true",
        "LANGCHAIN_API_KEY": api_key,
        "LANGCHAIN_PROJECT": settings.langsmith_project,
        "LANGCHAIN_ENDPOINT": settings.langsmith_endpoint,
    }
    os.environ.update(env)
    logger.info("LangSmith 追踪已启用：project=%s endpoint=%s", settings.langsmith_project, settings.langsmith_endpoint)
    return True
