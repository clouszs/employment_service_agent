"""统一响应结构与全局异常处理。"""

import logging
import traceback
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings

logger = logging.getLogger(__name__)


def success(data: Any = None, message: str = "ok") -> dict:
    """成功响应：{code:0, message, data}。"""
    return {"code": 0, "message": message, "data": data}


def error(code: int, message: str, data: Any = None) -> dict:
    """失败响应：code 非 0。"""
    return {"code": code, "message": message, "data": data}


def register_exception_handlers(app: FastAPI) -> None:
    """注册全局异常处理，统一错误返回结构。"""

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        # 5xx 服务器错误不暴露详情给客户端
        if exc.status_code >= 500:
            return JSONResponse(
                status_code=exc.status_code,
                content=error(code=exc.status_code, message="服务器内部错误"),
            )
        return JSONResponse(
            status_code=exc.status_code,
            content=error(code=exc.status_code, message=str(exc.detail)),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content=error(code=422, message="参数校验失败", data=exc.errors()),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        # 记录完整异常信息到日志
        logger.error(
            "Unhandled exception: %s",
            str(exc),
            extra={
                "path": request.url.path,
                "method": request.method,
                "traceback": traceback.format_exc(),
            },
        )

        # 生产环境不返回异常详情
        if settings.app_env == "production":
            return JSONResponse(
                status_code=500,
                content=error(code=500, message="服务器内部错误"),
            )
        else:
            # 开发环境返回详细信息便于调试
            return JSONResponse(
                status_code=500,
                content=error(
                    code=500,
                    message="服务器内部错误",
                    data={
                        "type": type(exc).__name__,
                        "detail": str(exc),
                    },
                ),
            )
