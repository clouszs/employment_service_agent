"""公告管理接口。"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.core.response import success
from app.models import Announcement, SysUser
from app.schemas.announcement import AnnouncementCreate, AnnouncementRead, AnnouncementUpdate
from app.services import announcement_service as svc

router = APIRouter(prefix="/announcements", tags=["运营-公告管理"])


# ===== 公共接口（所有登录用户可读）=====


@router.get("", summary="公告列表(分页，公开)")
def list_announcements(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
    status_: int | None = Query(None, alias="status"),
    db: Session = Depends(get_db),
    _: SysUser = Depends(get_current_user),
) -> dict:
    rows, total = svc.list_announcements(
        db,
        offset=(page - 1) * size,
        limit=size,
        status=status_,
    )
    return success(
        {
            "total": total,
            "page": page,
            "size": size,
            "items": [AnnouncementRead.model_validate(r).model_dump() for r in rows],
        }
    )


@router.get("/list/active", summary="获取生效中的公告")
def list_active_announcements(
    db: Session = Depends(get_db),
    _: SysUser = Depends(get_current_user),
) -> dict:
    """获取当前时间范围内生效且状态为发布的公告。"""
    now = datetime.now()
    stmt = (
        select(Announcement)
        .where(
            Announcement.status == 1,
            Announcement.publish_at == None,  # noqa: E711
            Announcement.expire_at == None,  # noqa: E711
        )
        .order_by(Announcement.id.desc())
        .limit(10)
    )
    rows = db.scalars(stmt).all()
    return success([AnnouncementRead.model_validate(r).model_dump() for r in rows])


# ===== 管理接口（admin/editor）=====


@router.get("/admin", summary="公告管理列表(分页，带筛选)")
def admin_list_announcements(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
    keyword: str | None = Query(None),
    status_: int | None = Query(None, alias="status"),
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_roles("admin", "editor")),
) -> dict:
    rows, total = svc.list_announcements(
        db,
        offset=(page - 1) * size,
        limit=size,
        status=status_,
        keyword=keyword,
    )
    return success(
        {
            "total": total,
            "page": page,
            "size": size,
            "items": [AnnouncementRead.model_validate(r).model_dump() for r in rows],
        }
    )


@router.post("", summary="新建公告", status_code=status.HTTP_201_CREATED)
def create_announcement(
    payload: AnnouncementCreate,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_roles("admin", "editor")),
) -> dict:
    obj = svc.create_announcement(db, payload, created_by=current_user.id)
    return success(AnnouncementRead.model_validate(obj).model_dump(), message="创建成功")


@router.put("/{announcement_id}", summary="修改公告")
def update_announcement(
    announcement_id: int,
    payload: AnnouncementUpdate,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_roles("admin", "editor")),
) -> dict:
    obj = svc.get_announcement(db, announcement_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="公告不存在")
    obj = svc.update_announcement(db, obj, payload)
    return success(AnnouncementRead.model_validate(obj).model_dump(), message="更新成功")


@router.delete("/{announcement_id}", summary="删除公告")
def delete_announcement(
    announcement_id: int,
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_roles("admin")),
) -> dict:
    obj = svc.get_announcement(db, announcement_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="公告不存在")
    svc.delete_announcement(db, obj)
    return success(message="已删除")
