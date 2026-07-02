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


def get_qa_config_value(db: Session, key: str, default: str | None = None) -> str | None:
    """读取问答配置：优先读数据库启用项，否则返回默认值。"""
    obj = get_app_config_by_key(db, key)
    if obj is not None and obj.status == 1:
        return obj.config_value
    return default


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


def seed_qa_defaults(db: Session) -> list[AppConfig]:
    """确保默认问答配置存在：缺失则创建，已存在则跳过（不覆盖用户自定义值）。"""
    defaults = [
        ("qa_retrieval.top_k", "5", "检索返回条数", "qa_retrieval"),
        ("qa_retrieval.faq_top_k", "1", "FAQ匹配返回条数", "qa_retrieval"),
        ("qa_retrieval.faq_score_threshold", "0.75", "FAQ命中阈值", "qa_retrieval"),
        ("qa_retrieval.score_threshold", "0.4", "检索无答案阈值", "qa_retrieval"),
        ("qa_model.model", "qwen3.7-max", "LLM模型名称", "qa_model"),
        ("qa_model.temperature", "0.3", "回答创造性(0~1)", "qa_model"),
        ("qa_model.max_tokens", "0", "最大生成长度(0=不限制)", "qa_model"),
        ("qa_strategy.enable_reference", "1", "是否显示引用来源(1=是/0=否)", "qa_strategy"),
        ("qa_strategy.no_answer_enabled", "1", "是否启用无答案兜底(1=是/0=否)", "qa_strategy"),
    ]
    results: list[AppConfig] = []
    for key, value, desc, group in defaults:
        existing = get_app_config_by_key(db, key)
        if existing:
            results.append(existing)
            continue
        obj = create_app_config(
            db,
            AppConfigCreate(
                config_key=key,
                config_value=value,
                description=desc,
                group_name=group,
            ),
        )
        results.append(obj)
    db.commit()
    return results


def get_monitor_config(db: Session, key: str, default: str = "0") -> str:
    """读取监控相关配置。"""
    obj = get_app_config_by_key(db, key)
    return obj.config_value if obj else default
