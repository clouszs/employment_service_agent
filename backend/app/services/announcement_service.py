"""公告服务层。"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.announcement import Announcement
from app.schemas.announcement import AnnouncementCreate, AnnouncementUpdate


def list_announcements(
    db: Session,
    offset: int = 0,
    limit: int = 20,
    status: Optional[int] = None,
    priority: Optional[int] = None,
    keyword: Optional[str] = None,
) -> tuple[list[Announcement], int]:
    """分页查询公告列表。"""
    stmt = select(Announcement)
    if status is not None:
        stmt = stmt.where(Announcement.status == status)
    if priority is not None:
        stmt = stmt.where(Announcement.priority == priority)
    if keyword:
        stmt = stmt.where(
            or_(Announcement.title.contains(keyword), Announcement.content.contains(keyword))
        )

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.order_by(Announcement.id.desc()).offset(offset).limit(limit)).all()
    return list(rows), total


def get_announcement(db: Session, announcement_id: int) -> Announcement | None:
    """按 ID 查询公告。"""
    return db.get(Announcement, announcement_id)


def create_announcement(db: Session, payload: AnnouncementCreate, created_by: int) -> Announcement:
    """新建公告。"""
    obj = Announcement(
        title=payload.title,
        content=payload.content,
        priority=payload.priority,
        expire_at=payload.expire_at,
        status=payload.status,
        created_by=created_by,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_announcement(db: Session, announcement: Announcement, data: AnnouncementUpdate) -> Announcement:
    """更新公告（仅更新传入的字段）。"""
    update_dict = data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(announcement, field, value)
    db.commit()
    db.refresh(announcement)
    return announcement


def delete_announcement(db: Session, announcement: Announcement) -> None:
    """删除公告。"""
    db.delete(announcement)
    db.commit()


def toggle_announcement_status(db: Session, announcement: Announcement, new_status: int) -> Announcement:
    """切换公告状态（发布/撤回）。"""
    announcement.status = new_status
    db.commit()
    db.refresh(announcement)
    return announcement
