"""问答与会话业务逻辑：会话 / 消息 / 反馈（不含 RAG 生成）。"""

from datetime import date, timedelta
from typing import Optional

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models import QaConversation, QaFeedback, QaMessage, QaMessageReference, SysUser


# ==================== 会话 ====================
def list_conversations(
    db: Session, user_id: int, offset: int, limit: int
) -> tuple[list[QaConversation], int]:
    stmt = select(QaConversation).where(
        QaConversation.user_id == user_id, QaConversation.status == 1
    )
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = (
        db.execute(stmt.order_by(QaConversation.updated_at.desc()).offset(offset).limit(limit))
        .scalars()
        .all()
    )
    return list(rows), total


def get_conversation(db: Session, conversation_id: int) -> Optional[QaConversation]:
    return db.get(QaConversation, conversation_id)


def create_conversation(db: Session, user_id: int, title: Optional[str]) -> QaConversation:
    conv = QaConversation(user_id=user_id, title=title, status=1)
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


def update_conversation(
    db: Session, conv: QaConversation, title: Optional[str] = None, status: Optional[int] = None
) -> QaConversation:
    if title is not None:
        conv.title = title
    if status is not None:
        conv.status = status
    db.commit()
    db.refresh(conv)
    return conv


def soft_delete_conversation(db: Session, conv: QaConversation) -> None:
    conv.status = 0
    db.commit()


# ==================== 消息 ====================
def list_messages(db: Session, conversation_id: int) -> list[QaMessage]:
    return list(
        db.execute(
            select(QaMessage)
            .where(QaMessage.conversation_id == conversation_id)
            .order_by(QaMessage.id)
        )
        .scalars()
        .all()
    )


def get_message(db: Session, message_id: int) -> Optional[QaMessage]:
    return db.get(QaMessage, message_id)


def list_message_references(db: Session, message_id: int) -> list[QaMessageReference]:
    return list(
        db.execute(
            select(QaMessageReference)
            .where(QaMessageReference.message_id == message_id)
            .order_by(QaMessageReference.rank_no)
        )
        .scalars()
        .all()
    )


def list_references_by_message_ids(
    db: Session, message_ids: list[int]
) -> list[QaMessageReference]:
    """批量查询多条消息的引用（避免 N+1）。"""
    if not message_ids:
        return []
    return list(
        db.execute(
            select(QaMessageReference)
            .where(QaMessageReference.message_id.in_(message_ids))
            .order_by(QaMessageReference.message_id, QaMessageReference.rank_no)
        )
        .scalars()
        .all()
    )


# ==================== 反馈 ====================
def upsert_feedback(
    db: Session, message_id: int, user_id: Optional[int], rating: int, reason: Optional[str]
) -> QaFeedback:
    """同一用户对同一消息的反馈，存在则更新，否则新建。"""
    fb = db.scalar(
        select(QaFeedback).where(
            QaFeedback.message_id == message_id, QaFeedback.user_id == user_id
        )
    )
    if fb is None:
        fb = QaFeedback(message_id=message_id, user_id=user_id, rating=rating, reason=reason)
        db.add(fb)
    else:
        fb.rating = rating
        fb.reason = reason
    db.commit()
    db.refresh(fb)
    return fb


# ==================== 反馈查询与统计（管理端）====================
def list_feedback(
    db: Session,
    offset: int,
    limit: int,
    rating: Optional[int] = None,
    date_str: Optional[str] = None,
) -> tuple[list[dict], int]:
    """反馈明细列表，关联出问题/答案/用户。rating: 1赞 -1踩；date_str: YYYY-MM-DD。"""
    # 只展示有原因文字的反馈（过滤空原因）
    stmt = select(QaFeedback).where(QaFeedback.reason.isnot(None), QaFeedback.reason != "")
    if rating is not None:
        stmt = stmt.where(QaFeedback.rating == rating)
    if date_str:
        stmt = stmt.where(func.date(QaFeedback.created_at) == date_str)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    fbs = list(
        db.execute(stmt.order_by(QaFeedback.id.desc()).offset(offset).limit(limit)).scalars().all()
    )

    msg_ids = [f.message_id for f in fbs]
    user_ids = [f.user_id for f in fbs if f.user_id]
    msgs = (
        {m.id: m for m in db.query(QaMessage).filter(QaMessage.id.in_(msg_ids)).all()}
        if msg_ids
        else {}
    )
    users = (
        {u.id: u for u in db.query(SysUser).filter(SysUser.id.in_(user_ids)).all()}
        if user_ids
        else {}
    )

    rows: list[dict] = []
    for f in fbs:
        ans = msgs.get(f.message_id)
        question = None
        if ans is not None:
            q = (
                db.query(QaMessage)
                .filter(
                    QaMessage.conversation_id == ans.conversation_id,
                    QaMessage.role == 1,
                    QaMessage.id < ans.id,
                )
                .order_by(QaMessage.id.desc())
                .first()
            )
            question = q.content if q else None
        u = users.get(f.user_id) if f.user_id else None
        rows.append(
            {
                "id": f.id,
                "rating": f.rating,
                "reason": f.reason,
                "created_at": f.created_at,
                "user_name": (u.real_name or u.username) if u else None,
                "question": question,
                "answer": ans.content if ans else None,
            }
        )
    return rows, total


def feedback_stats(db: Session) -> dict:
    """当日反馈统计 + 近 7 天赞/踩趋势。"""
    today = date.today()
    today_str = today.isoformat()

    total = db.scalar(
        select(func.count()).select_from(QaFeedback).where(func.date(QaFeedback.created_at) == today_str)
    ) or 0
    like = db.scalar(
        select(func.count())
        .select_from(QaFeedback)
        .where(func.date(QaFeedback.created_at) == today_str, QaFeedback.rating == 1)
    ) or 0
    dislike = total - like

    # 近 7 天趋势（按天分组统计赞/踩）
    start = today - timedelta(days=6)
    rows = db.execute(
        select(
            func.date(QaFeedback.created_at).label("d"),
            func.sum(case((QaFeedback.rating == 1, 1), else_=0)),
            func.sum(case((QaFeedback.rating == -1, 1), else_=0)),
        )
        .where(QaFeedback.created_at >= start)
        .group_by(func.date(QaFeedback.created_at))
    ).all()
    by_day = {str(r[0]): (int(r[1] or 0), int(r[2] or 0)) for r in rows}
    trend = []
    for i in range(7):
        d = (start + timedelta(days=i)).isoformat()
        lk, dk = by_day.get(d, (0, 0))
        trend.append({"date": d, "like": lk, "dislike": dk})

    return {
        "today": {
            "total": total,
            "like": like,
            "dislike": dislike,
            "dislike_rate": round(dislike / total, 4) if total else 0.0,
        },
        "trend": trend,
    }
