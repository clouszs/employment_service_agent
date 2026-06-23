"""同义词词典管理接口。"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.core.response import success
from app.models import SysUser
from app.schemas.knowledge import SynonymCreate, SynonymRead, SynonymUpdate
from app.services import knowledge_service as svc

router = APIRouter(prefix="/synonyms", tags=["知识库-同义词"])


@router.get("", summary="同义词列表(分页)")
def list_synonyms(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
    keyword: Optional[str] = Query(None, description="标准词模糊搜索"),
    status_: Optional[int] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    _: SysUser = Depends(get_current_user),
) -> dict:
    rows, total = svc.list_synonyms(db, offset=(page - 1) * size, limit=size, keyword=keyword, status=status_)
    return success(
        {
            "total": total,
            "page": page,
            "size": size,
            "items": [SynonymRead.model_validate(s).model_dump() for s in rows],
        }
    )


@router.post("", summary="新建同义词", status_code=status.HTTP_201_CREATED)
def create_synonym(
    payload: SynonymCreate,
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_roles("admin", "editor")),
) -> dict:
    syn = svc.create_synonym(db, payload)
    return success(SynonymRead.model_validate(syn).model_dump(), message="创建成功")


@router.put("/{synonym_id}", summary="修改同义词")
def update_synonym(
    synonym_id: int,
    payload: SynonymUpdate,
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_roles("admin", "editor")),
) -> dict:
    syn = svc.get_synonym(db, synonym_id)
    if syn is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="同义词不存在")
    syn = svc.update_synonym(db, syn, payload)
    return success(SynonymRead.model_validate(syn).model_dump(), message="更新成功")


@router.delete("/{synonym_id}", summary="删除同义词")
def delete_synonym(
    synonym_id: int,
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_roles("admin", "editor")),
) -> dict:
    syn = svc.get_synonym(db, synonym_id)
    if syn is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="同义词不存在")
    svc.delete_synonym(db, syn)
    return success(message="已删除")
