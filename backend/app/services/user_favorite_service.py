"""用户收藏服务层。"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.user_favorite import UserFavorite
from app.schemas.user_favorite import UserFavoriteCreate, UserFavoriteUpdate


def list_user_favorites(
    db: Session,
    user_id: int,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[UserFavorite], int]:
    """分页查询用户的收藏列表。"""
    stmt = select(UserFavorite).where(UserFavorite.user_id == user_id, UserFavorite.status == 1)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.order_by(UserFavorite.id.desc()).offset(offset).limit(limit)).all()
    return list(rows), total


def get_user_favorite(db: Session, fav_id: int, user_id: int) -> UserFavorite | None:
    """按 ID 查询某用户的收藏。"""
    return db.scalar(
        select(UserFavorite).where(UserFavorite.id == fav_id, UserFavorite.user_id == user_id)
    )


def get_user_favorite_by_message(db: Session, user_id: int, message_id: int) -> UserFavorite | None:
    """按消息 ID 查询是否已收藏（防止重复）。"""
    return db.scalar(
        select(UserFavorite).where(
            UserFavorite.user_id == user_id,
            UserFavorite.message_id == message_id,
            UserFavorite.status == 1,
        )
    )


def create_user_favorite(db: Session, user_id: int, data: UserFavoriteCreate) -> UserFavorite:
    """新建收藏。"""
    obj = UserFavorite(user_id=user_id, message_id=data.message_id, note=data.note)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_user_favorite(db: Session, fav: UserFavorite, data: UserFavoriteUpdate) -> UserFavorite:
    """更新收藏备注。"""
    if data.note is not None:
        fav.note = data.note
    db.commit()
    db.refresh(fav)
    return fav


def delete_user_favorite(db: Session, fav: UserFavorite) -> None:
    """软删除收藏。"""
    fav.status = 0
    db.commit()


def batch_delete_user_favorites(db: Session, fav_ids: list[int], user_id: int) -> int:
    """批量软删除收藏，返回删除条数。"""
    stmt = (
        select(UserFavorite)
        .where(UserFavorite.id.in_(fav_ids), UserFavorite.user_id == user_id, UserFavorite.status == 1)
    )
    rows = db.scalars(stmt).all()
    for row in rows:
        row.status = 0
    db.commit()
    return len(rows)
