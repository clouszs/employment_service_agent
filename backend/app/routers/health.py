"""健康检查接口：验证服务与数据库连通。"""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.response import success

router = APIRouter(tags=["health"])


@router.get("/health")
def health(db: Session = Depends(get_db)) -> dict:
    """返回服务状态及数据库连通情况。"""
    db_ok = True
    db_error = None
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001
        db_ok = False
        db_error = str(exc)

    return success(
        {
            "app": settings.app_name,
            "env": settings.app_env,
            "database": {
                "ok": db_ok,
                "host": settings.db_host,
                "port": settings.db_port,
                "name": settings.db_name,
                "error": db_error,
            },
        }
    )
