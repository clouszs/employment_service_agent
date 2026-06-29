"""公告服务层。"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.announcement import Announcement
from app.schemas.announcement import AnnouncementCreate, AnnouncementUpdate

logger = logging.getLogger(__name__)

# 公告配置文件路径（backend/data/announcements.json）
_ANNOUNCEMENT_CONFIG_PATH = Path(__file__).resolve().parents[2] / "data" / "announcements.json"


def get_active_config_announcements(query: str = "", max_results: int = 5) -> list[dict]:
    """读取配置文件中当前生效的公告（供 Agent news 分支轻量调用）。

    从 data/announcements.json 过滤出 status=active 且当前时间在 effective_time
    与 expire_time 之间的公告；query 非空时按标题/正文做关键词过滤。
    文件缺失或损坏时降级返回空列表，不抛异常。

    注意：这是基于文件的轻量来源，与 DB 版公告（list_announcements）相互独立。
    后续可统一到 DB 单一数据源（见 ARCHITECTURE_DECISIONS）。
    """
    try:
        if not _ANNOUNCEMENT_CONFIG_PATH.exists():
            logger.debug("公告配置文件不存在: %s", _ANNOUNCEMENT_CONFIG_PATH)
            return []

        data = json.loads(_ANNOUNCEMENT_CONFIG_PATH.read_text(encoding="utf-8"))
        items = data.get("announcements", [])

        now = datetime.now()
        active: list[dict] = []
        for item in items:
            if item.get("status") != "active":
                continue
            effective = item.get("effective_time")
            expire = item.get("expire_time")
            if effective:
                try:
                    if now < datetime.fromisoformat(effective):
                        continue
                except (ValueError, TypeError):
                    continue
            if expire:
                try:
                    if now > datetime.fromisoformat(expire):
                        continue
                except (ValueError, TypeError):
                    continue
            active.append(item)

        if query:
            q = query.lower()
            active = [
                a
                for a in active
                if q in a.get("title", "").lower() or q in a.get("content", "").lower()
            ]

        return active[: max(1, max_results)]
    except Exception as exc:  # noqa: BLE001
        logger.warning("get_active_config_announcements 失败: %s", exc)
        return []


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
