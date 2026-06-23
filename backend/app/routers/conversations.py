"""会话管理接口（会话增删查、会话内消息查看）。"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.response import success
from app.models import KbDocument, QaMessage, SysUser
from app.schemas.qa import (
    ConversationCreate,
    ConversationRead,
    ConversationUpdate,
    ConversationWithMessages,
    MessageRead,
    MessageReferenceRead,
    MessageWithReferences,
)
from app.services import qa_service as svc

router = APIRouter(prefix="/conversations", tags=["问答-会话"])


def _build_messages_with_refs(db: Session, messages: list[QaMessage]) -> list[dict]:
    """组装消息列表：为答案消息附带 references（含 document_title / page_no）。"""
    answer_ids = [m.id for m in messages if m.role == 2]
    refs_map: dict[int, list] = {mid: [] for mid in answer_ids}
    if answer_ids:
        refs = svc.list_references_by_message_ids(db, answer_ids)
        # 收集所有涉及到的 document_id
        doc_ids = {r.document_id for r in refs if r.document_id is not None}
        title_map: dict[int, str] = {}
        if doc_ids:
            for d in db.query(KbDocument).filter(KbDocument.id.in_(doc_ids)).all():
                title_map[d.id] = d.title
        for r in refs:
            refs_map[r.message_id].append({
                "id": r.id,
                "message_id": r.message_id,
                "document_id": r.document_id,
                "document_title": title_map.get(r.document_id) if r.document_id else None,
                "chunk_id": r.chunk_id,
                "score": r.score,
                "rank_no": r.rank_no,
                "snippet": r.snippet,
                "page_no": None,  # 历史引用未存 page_no，前端显示不区分
                "created_at": r.created_at,
            })

    result: list[dict] = []
    for m in messages:
        base = MessageRead.model_validate(m).model_dump()
        if m.role == 2:
            base["references"] = refs_map.get(m.id, [])
        else:
            base["references"] = []
        result.append(base)
    return result


def _owned_or_404(db: Session, conversation_id: int, user: SysUser):
    conv = svc.get_conversation(db, conversation_id)
    if conv is None or conv.status == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")
    if conv.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问该会话")
    return conv


@router.get("", summary="我的会话列表(分页)")
def list_conversations(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    current: SysUser = Depends(get_current_user),
) -> dict:
    rows, total = svc.list_conversations(db, current.id, (page - 1) * size, size)
    return success(
        {
            "total": total,
            "page": page,
            "size": size,
            "items": [ConversationRead.model_validate(c).model_dump() for c in rows],
        }
    )


@router.post("", summary="新建会话", status_code=status.HTTP_201_CREATED)
def create_conversation(
    payload: ConversationCreate,
    db: Session = Depends(get_db),
    current: SysUser = Depends(get_current_user),
) -> dict:
    conv = svc.create_conversation(db, current.id, payload.title)
    return success(ConversationRead.model_validate(conv).model_dump(), message="创建成功")


@router.get("/{conversation_id}", summary="会话详情(含消息)")
def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current: SysUser = Depends(get_current_user),
) -> dict:
    conv = _owned_or_404(db, conversation_id, current)
    messages = svc.list_messages(db, conversation_id)
    data = ConversationRead.model_validate(conv).model_dump()
    data["messages"] = _build_messages_with_refs(db, messages)
    return success(data)


@router.put("/{conversation_id}", summary="重命名会话")
def update_conversation(
    conversation_id: int,
    payload: ConversationUpdate,
    db: Session = Depends(get_db),
    current: SysUser = Depends(get_current_user),
) -> dict:
    conv = _owned_or_404(db, conversation_id, current)
    conv = svc.update_conversation(db, conv, title=payload.title, status=payload.status)
    return success(ConversationRead.model_validate(conv).model_dump(), message="更新成功")


@router.delete("/{conversation_id}", summary="删除会话(软删除)")
def delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current: SysUser = Depends(get_current_user),
) -> dict:
    conv = _owned_or_404(db, conversation_id, current)
    svc.soft_delete_conversation(db, conv)
    return success(message="已删除")


@router.get("/{conversation_id}/messages", summary="会话内消息列表")
def list_messages(
    conversation_id: int,
    db: Session = Depends(get_db),
    current: SysUser = Depends(get_current_user),
) -> dict:
    _owned_or_404(db, conversation_id, current)
    messages = svc.list_messages(db, conversation_id)
    return success(_build_messages_with_refs(db, messages))
