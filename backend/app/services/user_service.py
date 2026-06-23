"""用户与权限业务逻辑：操作 ORM，供路由层调用。"""

from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models import SysRole, SysUser, SysUserRole
from app.schemas.user import RoleCreate, RoleUpdate, UserCreate, UserUpdate


# ---------------- 用户 ----------------
def list_users(
    db: Session,
    offset: int,
    limit: int,
    keyword: Optional[str] = None,
    user_type: Optional[int] = None,
    status: Optional[int] = None,
) -> tuple[list[SysUser], int]:
    """分页查询用户，返回 (列表, 总数)。"""
    stmt = select(SysUser)
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where((SysUser.username.like(like)) | (SysUser.real_name.like(like)))
    if user_type is not None:
        stmt = stmt.where(SysUser.user_type == user_type)
    if status is not None:
        stmt = stmt.where(SysUser.status == status)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.execute(stmt.order_by(SysUser.id.desc()).offset(offset).limit(limit)).scalars().all()
    return list(rows), total


def get_user(db: Session, user_id: int) -> Optional[SysUser]:
    return db.get(SysUser, user_id)


def get_user_by_username(db: Session, username: str) -> Optional[SysUser]:
    return db.scalar(select(SysUser).where(SysUser.username == username))


def create_user(db: Session, data: UserCreate) -> SysUser:
    """创建用户，密码哈希存储。"""
    user = SysUser(
        username=data.username,
        password_hash=hash_password(data.password),
        real_name=data.real_name,
        user_type=data.user_type,
        college=data.college,
        email=data.email,
        phone=data.phone,
        status=data.status,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user: SysUser, data: UserUpdate) -> SysUser:
    """局部更新用户（仅更新传入的字段）。"""
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


def disable_user(db: Session, user: SysUser) -> None:
    """软删除：禁用用户(status=0)，保留数据。"""
    user.status = 0
    db.commit()


def hard_delete_user(db: Session, user: SysUser) -> None:
    """物理删除：彻底移除用户及其角色关联（历史问答记录保留）。"""
    db.query(SysUserRole).filter(SysUserRole.user_id == user.id).delete()
    db.delete(user)
    db.commit()


def authenticate(db: Session, username: str, password: str) -> Optional[SysUser]:
    """校验账号密码，成功返回用户。"""
    user = get_user_by_username(db, username)
    if user and user.status == 1 and verify_password(password, user.password_hash):
        return user
    return None


def reset_password(db: Session, user: SysUser, new_password: str) -> None:
    """管理员重置用户密码（不校验旧密码）。"""
    user.password_hash = hash_password(new_password)
    db.commit()


def change_password(db: Session, user: SysUser, old_password: str, new_password: str) -> bool:
    """自助改密码：校验旧密码，成功则更新并返回 True，旧密码错返回 False。"""
    if not verify_password(old_password, user.password_hash):
        return False
    user.password_hash = hash_password(new_password)
    db.commit()
    return True


# ---------------- 角色 ----------------
def list_roles(db: Session) -> list[SysRole]:
    return list(db.execute(select(SysRole).order_by(SysRole.id)).scalars().all())


def get_role(db: Session, role_id: int) -> Optional[SysRole]:
    return db.get(SysRole, role_id)


def get_role_by_code(db: Session, role_code: str) -> Optional[SysRole]:
    return db.scalar(select(SysRole).where(SysRole.role_code == role_code))


def create_role(db: Session, data: RoleCreate) -> SysRole:
    role = SysRole(role_code=data.role_code, role_name=data.role_name, description=data.description)
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


def update_role(db: Session, role: SysRole, data: RoleUpdate) -> SysRole:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(role, field, value)
    db.commit()
    db.refresh(role)
    return role


# ---------------- 用户-角色 ----------------
# 角色编码 → 用户类型 映射，按权限从高到低排列（取命中的第一个）
_ROLE_TO_USER_TYPE = [("admin", 5), ("editor", 4), ("student", 1)]


def assign_roles(db: Session, user_id: int, role_ids: list[int]) -> list[SysUserRole]:
    """重置用户的角色为给定集合，并联动更新 user_type（取最高权限角色对应类型）。"""
    db.query(SysUserRole).filter(SysUserRole.user_id == user_id).delete()
    links = [SysUserRole(user_id=user_id, role_id=rid) for rid in role_ids]
    db.add_all(links)

    # 联动 user_type：根据所分配角色中权限最高者确定类型
    if role_ids:
        codes = {
            r.role_code
            for r in db.query(SysRole).filter(SysRole.id.in_(role_ids)).all()
        }
        user = db.get(SysUser, user_id)
        if user:
            for code, utype in _ROLE_TO_USER_TYPE:
                if code in codes:
                    user.user_type = utype
                    break

    db.commit()
    return links


def list_user_roles(db: Session, user_id: int) -> list[SysRole]:
    return list(
        db.execute(
            select(SysRole)
            .join(SysUserRole, SysUserRole.role_id == SysRole.id)
            .where(SysUserRole.user_id == user_id)
        )
        .scalars()
        .all()
    )
