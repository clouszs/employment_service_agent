"""评测集管理 + 评测执行接口。"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.core.response import success
from app.models import SysUser
from app.schemas.ops import EvalCaseCreate, EvalCaseRead, EvalCaseUpdate, EvalRunRequest
from app.services import ops_service as svc

router = APIRouter(prefix="/eval-cases", tags=["运营-评测集"])


@router.post("/run", summary="执行评测(检索命中率，同步)")
def run_eval(
    payload: EvalRunRequest,
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_roles("admin", "editor")),
) -> dict:
    result = svc.run_eval(db, top_k=payload.top_k, category=payload.category, limit=payload.limit)
    return success(result)


@router.get("", summary="评测集列表(分页)")
def list_cases(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
    category: Optional[str] = Query(None),
    status_: Optional[int] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    _: SysUser = Depends(get_current_user),
) -> dict:
    rows, total = svc.list_eval_cases(db, (page - 1) * size, size, category=category, status=status_)
    return success(
        {
            "total": total,
            "page": page,
            "size": size,
            "items": [EvalCaseRead.model_validate(c).model_dump() for c in rows],
        }
    )


@router.post("", summary="新建评测用例", status_code=status.HTTP_201_CREATED)
def create_case(
    payload: EvalCaseCreate,
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_roles("admin", "editor")),
) -> dict:
    obj = svc.create_eval_case(db, payload)
    return success(EvalCaseRead.model_validate(obj).model_dump(), message="创建成功")


@router.put("/{case_id}", summary="修改评测用例")
def update_case(
    case_id: int,
    payload: EvalCaseUpdate,
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_roles("admin", "editor")),
) -> dict:
    obj = svc.get_eval_case(db, case_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="评测用例不存在")
    obj = svc.update_eval_case(db, obj, payload)
    return success(EvalCaseRead.model_validate(obj).model_dump(), message="更新成功")


@router.delete("/{case_id}", summary="删除评测用例")
def delete_case(
    case_id: int,
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_roles("admin", "editor")),
) -> dict:
    obj = svc.get_eval_case(db, case_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="评测用例不存在")
    svc.delete_eval_case(db, obj)
    return success(message="已删除")
