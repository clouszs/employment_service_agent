"""日志配置：开发环境控制台输出，生产环境 JSON 格式。"""

from __future__ import annotations

import logging
import sys
from typing import Any

from app.core.config import settings


def setup_logging() -> None:
    """配置全局日志。"""
    log_level = logging.INFO if settings.app_env == "production" else logging.DEBUG

    if settings.app_env == "production" and not settings.app_debug:
        _setup_json_logging(log_level)
    else:
        _setup_console_logging(log_level)


def _setup_console_logging(level: int) -> None:
    """开发环境：控制台可读日志。"""
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.setLevel(level)

    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(handler)


def _setup_json_logging(level: int) -> None:
    """生产环境：JSON 格式日志（便于 ELK/Loki 采集）。"""
    import json
    import traceback

    class JsonFormatter(logging.Formatter):
        def format(self, record: logging.LogRecord) -> str:
            log_entry: dict[str, Any] = {
                "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S.%fZ"),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno,
            }
            if record.exc_info and record.exc_info[0]:
                log_entry["exception"] = traceback.format_exception(*record.exc_info)
            if hasattr(record, "extra"):
                log_entry.update(record.extra)
            return json.dumps(log_entry, ensure_ascii=False, default=str)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    handler.setLevel(level)

    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(handler)
