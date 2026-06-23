"""消息相关接口：答案反馈、引用来源查看。"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.response import success
from app.models import SysUser
from app.schemas.qa import FeedbackCreate, FeedbackRead, MessageReferenceRead
from app.services import ops_service
from app.services import qa_service as svc

router = APIRouter(prefix="/messages", tags=["问答-消息"])


@router.post("/{message_id}/feedback", summary="对答案点赞/点踩")
def submit_feedback(
    message_id: int,
    payload: FeedbackCreate,
    db: Session = Depends(get_db),
    current: SysUser = Depends(get_current_user),
) -> dict:
    msg = svc.get_message(db, message_id)
    if msg is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="消息不存在")
    if msg.role != 2:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="只能对系统答案评价")
    if payload.rating not in (1, -1):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="rating 只能为 1 或 -1")

    reason = (payload.reason or "").strip()
    # 点踩必须填写原因
    if payload.rating == -1 and not reason:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="点踩时请填写反馈原因")
    # 原因内容敏感词拦截
    if reason and ops_service.moderate(db, reason)["action"] == 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="反馈内容包含违规词，请修改后再提交")

    fb = svc.upsert_feedback(db, message_id, current.id, payload.rating, reason or None)
    return success(FeedbackRead.model_validate(fb).model_dump(), message="反馈已提交")


@router.get("/{message_id}/references", summary="查看答案引用来源(溯源)")
def get_references(
    message_id: int,
    db: Session = Depends(get_db),
    _: SysUser = Depends(get_current_user),
) -> dict:
    if svc.get_message(db, message_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="消息不存在")
    refs = svc.list_message_references(db, message_id)
    return success([MessageReferenceRead.model_validate(r).model_dump() for r in refs])
