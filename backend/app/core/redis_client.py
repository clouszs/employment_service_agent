"""Redis 客户端：懒加载单例 + 不可用自动降级。

设计要点：
1. 懒连接：首次使用才建立连接，避免无 Redis 环境下启动即报错。
2. 失败熔断：一旦连接失败，标记为不可用并记下时间，后续 _COOLDOWN 秒内不再尝试，
   避免每次调用都卡 socket 超时（这正是"缓存不可用时透传"的关键——不能让缓存反而拖慢主流程）。
3. 全部操作 try/except 兜底：任何 Redis 异常都不抛给调用方，返回 None / 静默失败。
"""

from __future__ import annotations

import logging
import time
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

# 熔断冷却：标记不可用后，多少秒内不再重试连接
_COOLDOWN_SECONDS = 30.0

_client: "Optional[object]" = None
_unavailable_until: float = 0.0  # 在此时间戳之前视为不可用，直接跳过


def _now() -> float:
    return time.monotonic()


def get_redis() -> "Optional[object]":
    """返回可用的 Redis 客户端；不可用时返回 None（调用方据此降级）。"""
    global _client, _unavailable_until

    if not settings.redis_enabled:
        return None

    # 处于熔断冷却期，直接降级
    if _unavailable_until and _now() < _unavailable_until:
        return None

    if _client is not None:
        return _client

    try:
        import redis  # 局部导入，未安装 redis 包时也不影响其他功能

        client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            password=settings.redis_password or None,
            socket_timeout=settings.redis_socket_timeout,
            socket_connect_timeout=settings.redis_socket_timeout,
            decode_responses=False,  # 存的是 JSON bytes，自己解码
        )
        client.ping()  # 主动探活，失败即降级
        _client = client
        _unavailable_until = 0.0
        logger.info("Redis 连接成功：%s:%s/%s", settings.redis_host, settings.redis_port, settings.redis_db)
        return _client
    except Exception as e:  # noqa: BLE001  任何异常都降级，不影响主流程
        _unavailable_until = _now() + _COOLDOWN_SECONDS
        _client = None
        logger.warning("Redis 不可用，降级透传（%.0fs 内不再重试）：%s", _COOLDOWN_SECONDS, e)
        return None


def redis_get(key: str) -> "Optional[bytes]":
    """安全 GET：不可用或异常返回 None。"""
    client = get_redis()
    if client is None:
        return None
    try:
        return client.get(key)
    except Exception as e:  # noqa: BLE001
        _mark_unavailable(e)
        return None


def redis_setex(key: str, ttl: int, value: bytes) -> bool:
    """安全 SETEX：成功返回 True，失败静默返回 False。"""
    client = get_redis()
    if client is None:
        return False
    try:
        client.setex(key, ttl, value)
        return True
    except Exception as e:  # noqa: BLE001
        _mark_unavailable(e)
        return False


def _mark_unavailable(err: Exception) -> None:
    """运行期出错时熔断，避免后续连续超时。"""
    global _client, _unavailable_until
    _client = None
    _unavailable_until = _now() + _COOLDOWN_SECONDS
    logger.warning("Redis 操作失败，降级透传（%.0fs 内不再重试）：%s", _COOLDOWN_SECONDS, err)
