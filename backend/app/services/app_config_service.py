"""系统配置服务层。"""

from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.app_config import AppConfig
from app.schemas.app_config import AppConfigCreate, AppConfigUpdate


def list_app_configs(
    db: Session,
    offset: int = 0,
    limit: int = 20,
    keyword: str | None = None,
    group_name: str | None = None,
    status: int | None = None,
) -> tuple[list[AppConfig], int]:
    """分页查询系统配置列表。"""
    stmt = select(AppConfig)
    if keyword:
        stmt = stmt.where(
            or_(AppConfig.config_key.contains(keyword), AppConfig.description.contains(keyword))
        )
    if group_name:
        stmt = stmt.where(AppConfig.group_name == group_name)
    if status is not None:
        stmt = stmt.where(AppConfig.status == status)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.order_by(AppConfig.id).offset(offset).limit(limit)).all()
    return list(rows), total


def get_app_config(db: Session, config_id: int) -> AppConfig | None:
    """按 ID 查询配置。"""
    return db.get(AppConfig, config_id)


def get_app_config_by_key(db: Session, config_key: str) -> AppConfig | None:
    """按配置键查询。"""
    stmt = select(AppConfig).where(AppConfig.config_key == config_key)
    return db.scalar(stmt)


def create_app_config(db: Session, data: AppConfigCreate, updated_by: int | None = None) -> AppConfig:
    """新建配置。"""
    obj = AppConfig(
        config_key=data.config_key,
        config_value=data.config_value,
        description=data.description,
        group_name=data.group_name,
        is_sensitive=data.is_sensitive,
        status=data.status,
        updated_by=updated_by,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_app_config(db: Session, config: AppConfig, data: AppConfigUpdate) -> AppConfig:
    """更新配置（仅更新传入的字段）。"""
    update_dict = data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(config, field, value)
    db.commit()
    db.refresh(config)
    return config


def delete_app_config(db: Session, config: AppConfig) -> None:
    """删除配置（软逻辑删除，仅改状态）。"""
    config.status = 0
    db.commit()


def upsert_app_config(
    db: Session,
    config_key: str,
    config_value: str,
    description: str | None = None,
    group_name: str | None = None,
    updated_by: int | None = None,
) -> AppConfig:
    """upsert：若 key 存在则更新，否则新建。"""
    existing = get_app_config_by_key(db, config_key)
    if existing:
        existing.config_value = config_value
        if description is not None:
            existing.description = description
        if group_name is not None:
            existing.group_name = group_name
        if updated_by is not None:
            existing.updated_by = updated_by
        db.commit()
        db.refresh(existing)
        return existing
    return create_app_config(
        db,
        AppConfigCreate(
            config_key=config_key,
            config_value=config_value,
            description=description,
            group_name=group_name,
        ),
        updated_by=updated_by,
    )
