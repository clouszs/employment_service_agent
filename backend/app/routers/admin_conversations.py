"""管理端会话管理接口。"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.core.response import success
from app.models import QaConversation, QaMessage, SysUser
from app.schemas.qa import ConversationRead, MessageRead
from app.services import qa_service as svc

router = APIRouter(prefix="/admin/conversations", tags=["运营-会话管理"])


def _get_conversation_or_404(db: Session, conversation_id: int) -> QaConversation:
    conv = svc.get_conversation(db, conversation_id)
    if conv is None or conv.status == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")
    return conv


@router.get("", summary="管理端会话列表(跨用户，分页)")
def admin_list_conversations(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
    keyword: str | None = Query(None, description="按会话标题/用户名模糊搜索"),
    status_: int | None = Query(None, alias="status", description="状态筛选"),
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_roles("admin", "editor")),
) -> dict:
    stmt = (
        db.query(QaConversation, SysUser.username, SysUser.real_name)
        .outerjoin(SysUser, QaConversation.user_id == SysUser.id)
    )

    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.filter(
            or_(
                QaConversation.title.ilike(like),
                SysUser.username.ilike(like),
                SysUser.real_name.ilike(like),
            )
        )
    if status_ is not None:
        stmt = stmt.filter(QaConversation.status == status_)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = (
        stmt.order_by(QaConversation.updated_at.desc())
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )

    items = []
    for conv, username, real_name in rows:
        data = ConversationRead.model_validate(conv).model_dump()
        data["username"] = username or real_name or "匿名"
        last_msg = (
            db.query(QaMessage)
            .filter(QaMessage.conversation_id == conv.id, QaMessage.role == 1)
            .order_by(QaMessage.created_at.desc())
            .first()
        )
        data["last_message"] = (last_msg.content or "")[:120] if last_msg else ""
        items.append(data)

    return success({"total": total, "page": page, "size": size, "items": items})


@router.get("/{conversation_id}", summary="管理端会话详情(跨用户)")
def admin_get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_roles("admin", "editor")),
) -> dict:
    conv = _get_conversation_or_404(db, conversation_id)
    messages = svc.list_messages(db, conversation_id)
    data = ConversationRead.model_validate(conv).model_dump()
    data["messages"] = [
        MessageRead.model_validate(m).model_dump() for m in messages
    ]
    return success(data)


@router.delete("/{conversation_id}", summary="管理端强制删除会话(硬删除)")
def admin_delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_roles("admin")),
) -> dict:
    conv = _get_conversation_or_404(db, conversation_id)
    svc.force_delete_conversation(db, conv)
    return success(message="已强制删除")
