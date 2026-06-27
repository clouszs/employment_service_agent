"""检索问答接口：纯检索 / 同步问答 / 流式问答(SSE) / Agent 问答。"""

import json

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.response import success
from app.models import SysUser
from app.schemas.agent import AgentChatResponse
from app.schemas.qa import AskRequest, SearchRequest
from app.services import qa_service
from app.services import rag_service

router = APIRouter(tags=["问答-RAG"])


@router.post("/search", summary="纯向量检索(返回命中片段)")
def search(
    payload: SearchRequest,
    db: Session = Depends(get_db),
    _: SysUser = Depends(get_current_user),
) -> dict:
    hits = rag_service.search(db, payload.query, top_k=payload.top_k)
    return success(hits)


@router.post("/ask", summary="同步问答(检索+生成+溯源，落库)")
def ask(
    payload: AskRequest,
    request: Request,
    db: Session = Depends(get_db),
    current: SysUser = Depends(get_current_user),
) -> dict:
    client_ip = request.client.host if request.client else None
    result = rag_service.ask(
        db, current.id, payload.question, conversation_id=payload.conversation_id, client_ip=client_ip
    )
    return success(result)


@router.post("/ask/stream", summary="流式问答(SSE逐字输出)")
def ask_stream(
    payload: AskRequest,
    request: Request,
    current: SysUser = Depends(get_current_user),
) -> StreamingResponse:
    client_ip = request.client.host if request.client else None

    def event_gen():
        for evt in rag_service.ask_stream(
            current.id, payload.question, conversation_id=payload.conversation_id, client_ip=client_ip
        ):
            yield f"event: {evt['event']}\ndata: {json.dumps(evt['data'], ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/ask/agent", summary="Agent 问答(同步，集成 Agent 工作流)")
def ask_agent(
    payload: AskRequest,
    request: Request,
    db: Session = Depends(get_db),
    current: SysUser = Depends(get_current_user),
) -> dict:
    """Agent 问答接口（V1 同步版）。

    渐进式迁移：agent_enabled=False 时切回旧 RAG。
    """
    from app.core.config import settings

    client_ip = request.client.host if request.client else None

    if not settings.agent_enabled:
        result = rag_service.ask(
            db, current.id, payload.question, conversation_id=payload.conversation_id, client_ip=client_ip
        )
        return success(result)

    result = qa_service.agent_chat(
        db, current.id, payload.question, conversation_id=payload.conversation_id, client_ip=client_ip, history=payload.history,
    )
    return success(result)
