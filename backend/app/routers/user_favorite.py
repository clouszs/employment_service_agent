"""用户收藏管理接口。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.response import success
from app.models import SysUser, UserFavorite
from app.schemas.user_favorite import UserFavoriteCreate, UserFavoriteRead, UserFavoriteUpdate
from app.services import user_favorite_service as svc

router = APIRouter(prefix="/favorites", tags=["用户-收藏"])


@router.get("", summary="我的收藏列表(分页)")
def list_my_favorites(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
) -> dict:
    rows, total = svc.list_user_favorites(db, current_user.id, offset=(page - 1) * size, limit=size)
    return success(
        {
            "total": total,
            "page": page,
            "size": size,
            "items": [UserFavoriteRead.model_validate(r).model_dump() for r in rows],
        }
    )


@router.post("", summary="添加收藏", status_code=status.HTTP_201_CREATED)
def create_favorite(
    payload: UserFavoriteCreate,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
) -> dict:
    # 防止重复收藏
    existing = svc.get_user_favorite_by_message(db, current_user.id, payload.message_id)
    if existing:
        return success(UserFavoriteRead.model_validate(existing).model_dump(), message="收藏已存在")
    obj = svc.create_user_favorite(db, current_user.id, payload)
    return success(UserFavoriteRead.model_validate(obj).model_dump(), message="收藏成功")


@router.put("/{fav_id}", summary="修改收藏备注")
def update_favorite(
    fav_id: int,
    payload: UserFavoriteUpdate,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
) -> dict:
    fav = svc.get_user_favorite(db, fav_id, current_user.id)
    if fav is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="收藏不存在")
    fav = svc.update_user_favorite(db, fav, payload)
    return success(UserFavoriteRead.model_validate(fav).model_dump(), message="更新成功")


@router.delete("/{fav_id}", summary="取消收藏")
def delete_favorite(
    fav_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
) -> dict:
    fav = svc.get_user_favorite(db, fav_id, current_user.id)
    if fav is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="收藏不存在")
    svc.delete_user_favorite(db, fav)
    return success(message="已取消收藏")
