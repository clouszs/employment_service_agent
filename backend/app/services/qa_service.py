"""问答与会话业务逻辑：会话 / 消息 / 反馈 / Agent 问答集成。"""

from __future__ import annotations

import logging
import time
from datetime import date, datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from typing import Optional

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.agent.graph import get_agent_graph
from app.core.config import settings
from app.models import QaConversation, QaFeedback, QaMessage, QaMessageReference, OpQueryLog, SysUser
from app.utils.conversation import resolve_conversation

logger = logging.getLogger(__name__)


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


# ==================== Agent 问答集成 ====================


def agent_chat(
    db: Session,
    user_id: int,
    query: str,
    conversation_id: Optional[int] = None,
    client_ip: Optional[str] = None,
    history: Optional[list[dict]] = None,
) -> dict:
    """Agent 问答入口（V1 简化版）。

    流程：
    1. 创建/获取会话
    2. 执行 Agent 工作流
    3. 保存用户消息 + AI 回答
    4. 保存引用
    5. 记录查询日志

    Args:
        db: 数据库会话
        user_id: 用户 ID
        query: 用户问题
        conversation_id: 会话 ID（可选）
        client_ip: 客户端 IP（可选）

    Returns:
        结果字典（包含 conversation_id / message_id / response / citations 等）
    """
    from app.core.config import settings

    start = datetime.now()

    # 1. 创建/获取会话
    conv = resolve_conversation(db, user_id, conversation_id, query)

    # 2. 执行 Agent 工作流
    try:
        workflow = get_agent_graph().build()
        app = workflow.compile()

        request_id = str(__import__("uuid").uuid4())
        state: dict = {
            "current_query": query,
            "conversation_id": conv.id,
            "user_id": user_id,
            "request_id": request_id,
            "created_at": datetime.now().isoformat(),
            "retry_attempt": 0,
            "tool_call_count": 0,
            "regenerate_count": 0,
            "forced_exit": False,
            "is_low_confidence": False,
            "skipped_consistency_check": False,
            "is_error": False,
            "should_refuse": False,
            "refusal_reason": "",
            "content_safe": True,
            "search_results": [],
            "citations": [],
            "confidence": 0.0,
            "query_risk_level": "medium",
            "route": "",
            "response": "",
            "consistency_issues": [],
            "fact_issues": [],
            "temporal_warnings": [],
            "history": history or [],
            "reasoning_chain": [],
            "error": {},
            "partial_effects": [],
            "last_search_query": "",
            "llm_tokens_in": 0,
            "llm_tokens_out": 0,
            "warnings": [],
        }

        config = {"configurable": {"thread_id": str(conv.id)}}

        # 超时保护：使用线程池执行工作流，超时后返回降级响应
        timeout_seconds = settings.agent_timeout_seconds
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(app.invoke, state, config)
            try:
                result = future.result(timeout=timeout_seconds)
            except TimeoutError:
                logger.error(
                    "Agent 工作流超时：user=%d conv=%d timeout=%ds",
                    user_id,
                    conv.id,
                    timeout_seconds,
                )
                result = {
                    "response": "抱歉，系统处理您的请求时遇到了超时，请稍后再试或联系就业中心老师。",
                    "confidence": 0.0,
                    "should_refuse": True,
                    "route": "error",
                    "citations": [],
                    "consistency_issues": [],
                    "fact_issues": [],
                    "temporal_warnings": [],
                    "warnings": ["系统响应超时，请稍后再试。"],
                    "query_risk_level": "medium",
                    "is_low_confidence": True,
                    "is_error": True,
                    "llm_tokens_in": 0,
                    "llm_tokens_out": 0,
                }

        response = result.get("response", "")
        is_no_answer = result.get("should_refuse", False)
        route = result.get("route", "")
        confidence = result.get("confidence", 0.0)
        citations = result.get("citations", [])
        consistency_issues = result.get("consistency_issues", [])
        fact_issues = result.get("fact_issues", [])
        temporal_warnings = result.get("temporal_warnings", [])
        warnings = result.get("warnings", [])
        query_risk_level = result.get("query_risk_level", "medium")
        is_low_confidence = result.get("is_low_confidence", False)
        llm_tokens_in = result.get("llm_tokens_in", 0)
        llm_tokens_out = result.get("llm_tokens_out", 0)

    except Exception as e:
        logger.error("Agent 工作流执行失败: %s", str(e))
        response = "抱歉，系统处理您的请求时遇到了问题，请稍后再试或联系就业中心老师。"
        is_no_answer = True
        route = "error"
        confidence = 0.0
        citations = []
        consistency_issues = []
        fact_issues = []
        temporal_warnings = []
        warnings = []
        query_risk_level = "medium"
        is_low_confidence = False
        llm_tokens_in = 0
        llm_tokens_out = 0

    # 3. 保存用户消息 + AI 回答
    latency = int((datetime.now() - start).total_seconds() * 1000)

    answer_msg = QaMessage(
        conversation_id=conv.id,
        role=2,
        content=response,
        answer_type=4 if is_no_answer else 1,
        is_no_answer=1 if is_no_answer else 0,
        llm_model="agent-workflow",
        latency_ms=latency,
        confidence=confidence,
        query_risk_level=query_risk_level,
        consistency_issues=str(consistency_issues),
        fact_issues=str(fact_issues),
        temporal_warnings=str(temporal_warnings),
        prompt_tokens=llm_tokens_in,
        completion_tokens=llm_tokens_out,
    )
    db.add(answer_msg)
    db.add(QaMessage(conversation_id=conv.id, role=1, content=query))
    db.commit()
    db.refresh(answer_msg)

    # 4. 保存引用
    if not is_no_answer:
        for rank, cit in enumerate(citations, start=1):
            db.add(
                QaMessageReference(
                    message_id=answer_msg.id,
                    document_id=cit.get("document_id"),
                    chunk_id=cit.get("chunk_id"),
                    score=cit.get("score"),
                    rank_no=rank,
                    snippet=(cit.get("snippet") or "")[:300],
                )
            )

    # 5. 记录查询日志
    db.add(
        OpQueryLog(
            user_id=user_id,
            conversation_id=conv.id,
            message_id=answer_msg.id,
            question=query[:1024],
            answer_brief=response[:2048],
            hit_doc_count=len(citations),
            is_no_answer=1 if is_no_answer else 0,
            latency_ms=latency,
            client_ip=client_ip,
            channel="web",
        )
    )
    db.commit()

    return {
        "conversation_id": conv.id,
        "message_id": answer_msg.id,
        "response": response,
        "is_no_answer": is_no_answer,
        "blocked": False,
        "from_faq": False,
        "references": citations,
        "citations": citations,
        "confidence": confidence,
        "route": route,
        "query_risk_level": query_risk_level,
        "is_low_confidence": is_low_confidence,
        "is_error": False,
        "consistency_issues": consistency_issues,
        "fact_issues": fact_issues,
        "temporal_warnings": temporal_warnings,
        "warnings": warnings,
        "request_id": request_id,
        "llm_tokens_in": llm_tokens_in,
        "llm_tokens_out": llm_tokens_out,
    }

