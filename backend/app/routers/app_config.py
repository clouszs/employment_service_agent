"""系统配置管理接口。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.core.response import success
from app.models import SysUser
from app.schemas.app_config import AppConfigCreate, AppConfigRead, AppConfigUpdate
from app.services import app_config_service as svc

router = APIRouter(prefix="/app-configs", tags=["运营-系统配置"])


@router.get("", summary="系统配置列表(分页)")
def list_configs(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
    keyword: str | None = Query(None, description="配置键/说明模糊搜索"),
    group_name: str | None = Query(None),
    status_: int | None = Query(None, alias="status"),
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_roles("admin", "editor")),
) -> dict:
    rows, total = svc.list_app_configs(
        db,
        offset=(page - 1) * size,
        limit=size,
        keyword=keyword,
        group_name=group_name,
        status=status_,
    )
    return success(
        {
            "total": total,
            "page": page,
            "size": size,
            "items": [AppConfigRead.model_validate(r).model_dump() for r in rows],
        }
    )


@router.get("/{config_id}", summary="配置详情")
def get_config(
    config_id: int,
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_roles("admin", "editor")),
) -> dict:
    obj = svc.get_app_config(db, config_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="配置不存在")
    return success(AppConfigRead.model_validate(obj).model_dump())


@router.post("", summary="新建配置", status_code=status.HTTP_201_CREATED)
def create_config(
    payload: AppConfigCreate,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_roles("admin")),
) -> dict:
    existing = svc.get_app_config_by_key(db, payload.config_key)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"配置键已存在：{payload.config_key}")
    obj = svc.create_app_config(db, payload, updated_by=current_user.id)
    return success(AppConfigRead.model_validate(obj).model_dump(), message="创建成功")


@router.put("/{config_id}", summary="修改配置")
def update_config(
    config_id: int,
    payload: AppConfigUpdate,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_roles("admin")),
) -> dict:
    obj = svc.get_app_config(db, config_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="配置不存在")
    obj = svc.update_app_config(db, obj, payload)
    return success(AppConfigRead.model_validate(obj).model_dump(), message="更新成功")


@router.delete("/{config_id}", summary="删除配置")
def delete_config(
    config_id: int,
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_roles("admin")),
) -> dict:
    obj = svc.get_app_config(db, config_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="配置不存在")
    svc.delete_app_config(db, obj)
    return success(message="已删除")
