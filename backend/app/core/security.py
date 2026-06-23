"""安全工具：密码哈希(pbkdf2，stdlib) + JWT 令牌。"""

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt

from app.core.config import settings

_PBKDF2_ITERATIONS = 260_000
_PBKDF2_ALGO = "sha256"


def hash_password(plain: str) -> str:
    """生成 pbkdf2 密码哈希，格式 pbkdf2_sha256$iters$salt$hash。"""
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac(_PBKDF2_ALGO, plain.encode(), salt.encode(), _PBKDF2_ITERATIONS)
    return f"pbkdf2_{_PBKDF2_ALGO}${_PBKDF2_ITERATIONS}${salt}${dk.hex()}"


def verify_password(plain: str, stored: Optional[str]) -> bool:
    """校验明文密码与存储的哈希是否匹配。"""
    if not stored:
        return False
    try:
        algo_tag, iters_s, salt, hash_hex = stored.split("$")
        iters = int(iters_s)
        algo = algo_tag.replace("pbkdf2_", "")
    except (ValueError, AttributeError):
        return False
    dk = hashlib.pbkdf2_hmac(algo, plain.encode(), salt.encode(), iters)
    return hmac.compare_digest(dk.hex(), hash_hex)


def create_access_token(subject: str | int, extra: Optional[dict] = None) -> str:
    """签发 JWT 访问令牌，sub 为用户ID。"""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(subject),
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_expire_minutes),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    """解析 JWT，失败抛 jwt 异常（由调用方捕获）。"""
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
