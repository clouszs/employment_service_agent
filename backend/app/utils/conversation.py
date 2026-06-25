"""通用工具函数：会话、时间、字符串等。"""

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.models import QaConversation


def resolve_conversation(
    db: Session,
    user_id: int,
    conversation_id: Optional[int],
    question: str,
) -> QaConversation:
    """获取或创建会话。

    如果 conversation_id 有效且属于该用户，则返回已有会话；
    否则创建新会话。
    """
    if conversation_id:
        conv = db.get(QaConversation, conversation_id)
        if conv and conv.status == 1 and conv.user_id == user_id:
            return conv
    conv = QaConversation(user_id=user_id, title=question[:30], status=1)
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv
