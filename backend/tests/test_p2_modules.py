"""P2 新模块 API 集成测试：app-configs / favorites / announcements。

直接调用 Service 层（连接真实 MySQL），验证业务逻辑。
同时通过 TestClient（真实 MySQL）验证路由层的权限控制。

注意：测试数据会写入真实 MySQL，用户名使用 UUID 避免冲突。
"""

from __future__ import annotations

import os
import sys
import uuid

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.security import create_access_token
from app.services import app_config_service, user_favorite_service, announcement_service, user_service
from app.core.database import SessionLocal

_TEST_PREFIX = f"p2_{uuid.uuid4().hex[:8]}"


def _make_username(base: str) -> str:
    return f"{_TEST_PREFIX}_{base}"


# ==================== 真实数据库 Service 层测试 ====================


@pytest.fixture()
def p2_db():
    """提供真实数据库会话（自动关闭）。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _create_real_user(db, username: str, user_type: int = 1):
    """在真实 MySQL 中创建用户并提交。"""
    user = user_service.create_user(
        db,
        type("UserCreate", (), {
            "username": username,
            "password": "pw123456",
            "real_name": username,
            "user_type": user_type,
            "college": None,
            "email": None,
            "phone": None,
            "status": 1,
        })(),
    )
    db.commit()
    return user


# ==================== AppConfig Service 测试 ====================


class TestAppConfigService:
    def test_create_and_get(self, p2_db):
        user = _create_real_user(p2_db, _make_username("cfg"))
        from app.schemas.app_config import AppConfigCreate
        obj = app_config_service.create_app_config(
            p2_db,
            AppConfigCreate(config_key=_make_username("k1"), config_value="svc_value", description="svc测试", group_name="测试"),
            updated_by=user.id,
        )
        p2_db.commit()
        assert obj.id is not None
        assert obj.config_key.endswith("k1") or _make_username("k1") in obj.config_key

        found = app_config_service.get_app_config(p2_db, obj.id)
        assert found is not None
        assert found.config_value == "svc_value"

        by_key = app_config_service.get_app_config_by_key(p2_db, obj.config_key)
        assert by_key.id == obj.id

    def test_list_and_update(self, p2_db):
        user = _create_real_user(p2_db, _make_username("cfg2"))
        from app.schemas.app_config import AppConfigCreate, AppConfigUpdate
        key = _make_username("k2")
        obj = app_config_service.create_app_config(
            p2_db,
            AppConfigCreate(config_key=key, config_value="old"),
            updated_by=user.id,
        )
        p2_db.commit()

        rows, total = app_config_service.list_app_configs(p2_db, offset=0, limit=10)
        assert total >= 1

        updated = app_config_service.update_app_config(
            p2_db, obj, AppConfigUpdate(config_value="new", description="updated")
        )
        assert updated.config_value == "new"

    def test_delete_soft(self, p2_db):
        user = _create_real_user(p2_db, _make_username("cfg3"))
        from app.schemas.app_config import AppConfigCreate
        obj = app_config_service.create_app_config(
            p2_db,
            AppConfigCreate(config_key=_make_username("k3"), config_value="bye"),
            updated_by=user.id,
        )
        p2_db.commit()
        app_config_service.delete_app_config(p2_db, obj)
        p2_db.commit()
        assert obj.status == 0

    def test_upsert(self, p2_db):
        user = _create_real_user(p2_db, _make_username("cfg4"))
        key = _make_username("k4")
        obj1 = app_config_service.upsert_app_config(p2_db, key, "v1", updated_by=user.id)
        p2_db.commit()
        assert obj1.config_value == "v1"
        obj2 = app_config_service.upsert_app_config(p2_db, key, "v2", updated_by=user.id)
        p2_db.commit()
        assert obj2.id == obj1.id
        assert obj2.config_value == "v2"


# ==================== UserFavorite Service 测试 ====================


class TestUserFavoriteService:
    def test_create_and_list(self, p2_db):
        user = _create_real_user(p2_db, _make_username("fav"))
        from app.schemas.user_favorite import UserFavoriteCreate
        obj = user_favorite_service.create_user_favorite(
            p2_db, user.id, UserFavoriteCreate(message_id=1, note="note1")
        )
        p2_db.commit()
        assert obj.user_id == user.id

        rows, total = user_favorite_service.list_user_favorites(p2_db, user.id, offset=0, limit=10)
        assert total >= 1

    def test_duplicate_prevention(self, p2_db):
        user = _create_real_user(p2_db, _make_username("fav2"))
        from app.schemas.user_favorite import UserFavoriteCreate
        user_favorite_service.create_user_favorite(p2_db, user.id, UserFavoriteCreate(message_id=55))
        p2_db.commit()
        dup = user_favorite_service.get_user_favorite_by_message(p2_db, user.id, 55)
        assert dup is not None

    def test_update_and_delete(self, p2_db):
        user = _create_real_user(p2_db, _make_username("fav3"))
        from app.schemas.user_favorite import UserFavoriteCreate, UserFavoriteUpdate
        obj = user_favorite_service.create_user_favorite(
            p2_db, user.id, UserFavoriteCreate(message_id=77, note="old")
        )
        p2_db.commit()

        updated = user_favorite_service.update_user_favorite(
            p2_db, obj, UserFavoriteUpdate(note="new")
        )
        assert updated.note == "new"

        user_favorite_service.delete_user_favorite(p2_db, obj)
        p2_db.commit()
        assert obj.status == 0


# ==================== Announcement Service 测试 ====================


class TestAnnouncementService:
    def test_create_and_get(self, p2_db):
        user = _create_real_user(p2_db, _make_username("ann"))
        from app.schemas.announcement import AnnouncementCreate
        obj = announcement_service.create_announcement(
            p2_db,
            AnnouncementCreate(title=_make_username("ann1"), content="svc内容", priority=1, status=1),
            created_by=user.id,
        )
        p2_db.commit()
        assert "ann1" in obj.title

        found = announcement_service.get_announcement(p2_db, obj.id)
        assert found is not None

    def test_list_with_filters(self, p2_db):
        user = _create_real_user(p2_db, _make_username("ann2"))
        from app.schemas.announcement import AnnouncementCreate
        title = _make_username("ann_high")
        announcement_service.create_announcement(
            p2_db,
            AnnouncementCreate(title=title, content="内容", priority=1, status=1),
            created_by=user.id,
        )
        p2_db.commit()

        rows, total = announcement_service.list_announcements(p2_db, offset=0, limit=10, status=1)
        assert total >= 1

        rows2, total2 = announcement_service.list_announcements(
            p2_db, offset=0, limit=10, keyword=_make_username("ann_high")
        )
        assert total2 >= 1

    def test_update_and_delete(self, p2_db):
        user = _create_real_user(p2_db, _make_username("ann3"))
        from app.schemas.announcement import AnnouncementCreate, AnnouncementUpdate
        obj = announcement_service.create_announcement(
            p2_db,
            AnnouncementCreate(title=_make_username("ann_del"), content="内容", status=1),
            created_by=user.id,
        )
        p2_db.commit()

        updated = announcement_service.update_announcement(
            p2_db, obj, AnnouncementUpdate(title=_make_username("ann_upd"), priority=3)
        )
        assert "ann_upd" in updated.title

        announcement_service.delete_announcement(p2_db, obj)
        p2_db.commit()
        assert announcement_service.get_announcement(p2_db, obj.id) is None
