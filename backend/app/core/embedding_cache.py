"""Embedding 三级缓存（方案 B）：L1 进程内存 LRU → L2 Redis → L3 MySQL → API。

仅用于查询路径（embed_query）：用户问题/FAQ 复用率高，缓存收益大。
文档批量嵌入（embed_texts 建索引）不走本缓存，避免缓存表暴涨且命中率≈0。

命中即逐层回填（lower 命中 → 回写 upper）；任意层异常都不影响主流程（透传到下一层/API）。
key = SHA256(text | model | dim)，模型或维度变更不会串味。
"""

from __future__ import annotations

import hashlib
import json
import logging
import threading
from collections import OrderedDict

from sqlalchemy import text as sql_text

from app.core.config import settings
from app.core.redis_client import redis_get, redis_setex

logger = logging.getLogger(__name__)

# ---------------- L1：进程内存 LRU ----------------
_l1: "OrderedDict[str, list[float]]" = OrderedDict()
_l1_lock = threading.Lock()


def _make_key(text: str) -> str:
    raw = f"{text}|{settings.embedding_model}|{settings.embedding_dim}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _redis_key(cache_key: str) -> str:
    return f"emb:{cache_key}"


def _l1_get(key: str) -> "list[float] | None":
    with _l1_lock:
        if key in _l1:
            _l1.move_to_end(key)  # LRU：访问即置最新
            return _l1[key]
    return None


def _l1_put(key: str, vec: "list[float]") -> None:
    cap = settings.embedding_memory_cache_size
    with _l1_lock:
        _l1[key] = vec
        _l1.move_to_end(key)
        while len(_l1) > cap:
            _l1.popitem(last=False)  # 淘汰最久未用


# ---------------- L3：MySQL embedding_cache ----------------
def _l3_get(cache_key: str) -> "list[float] | None":
    """从 MySQL 读缓存；任何异常都降级返回 None。"""
    try:
        from app.core.database import SessionLocal
    except Exception:  # noqa: BLE001
        return None
    db = None
    try:
        db = SessionLocal()
        row = db.execute(
            sql_text("SELECT embedding FROM embedding_cache WHERE cache_key = :k LIMIT 1"),
            {"k": cache_key},
        ).first()
        if not row:
            return None
        # 命中计数 +1（失败不影响返回）
        db.execute(
            sql_text("UPDATE embedding_cache SET hit_count = hit_count + 1 WHERE cache_key = :k"),
            {"k": cache_key},
        )
        db.commit()
        raw = row[0]
        # embedding 列为 LONGTEXT，存的是 JSON 字符串，精确往返
        return json.loads(raw) if isinstance(raw, (str, bytes, bytearray)) else raw
    except Exception as e:  # noqa: BLE001
        logger.warning("L3(embedding_cache) 读失败，降级：%s", e)
        if db is not None:
            db.rollback()
        return None
    finally:
        if db is not None:
            db.close()


def _l3_put(cache_key: str, text: str, vec: "list[float]") -> None:
    """写入 MySQL 缓存（已存在则忽略）；失败静默。"""
    try:
        from app.core.database import SessionLocal
    except Exception:  # noqa: BLE001
        return
    db = None
    try:
        db = SessionLocal()
        db.execute(
            sql_text(
                "INSERT IGNORE INTO embedding_cache "
                "(cache_key, text_sample, model, dim, embedding, hit_count) "
                "VALUES (:k, :s, :m, :d, :e, 0)"
            ),
            {
                "k": cache_key,
                "s": text[:200],
                "m": settings.embedding_model,
                "d": settings.embedding_dim,
                "e": json.dumps(vec),
            },
        )
        db.commit()
    except Exception as e:  # noqa: BLE001
        logger.warning("L3(embedding_cache) 写失败，忽略：%s", e)
        if db is not None:
            db.rollback()
    finally:
        if db is not None:
            db.close()


# ---------------- 对外 API ----------------
def get(text: str) -> "list[float] | None":
    """三级查询：L1 → L2 → L3；命中则回填上层。全 miss 返回 None。"""
    key = _make_key(text)

    # L1
    vec = _l1_get(key)
    if vec is not None:
        return vec

    # L2 Redis
    raw = redis_get(_redis_key(key))
    if raw is not None:
        try:
            vec = json.loads(raw)
            _l1_put(key, vec)  # 回填 L1
            return vec
        except Exception as e:  # noqa: BLE001
            logger.warning("L2(Redis) 反序列化失败，忽略：%s", e)

    # L3 MySQL
    vec = _l3_get(key)
    if vec is not None:
        _l1_put(key, vec)  # 回填 L1
        redis_setex(_redis_key(key), settings.embedding_cache_ttl, json.dumps(vec).encode("utf-8"))  # 回填 L2
        return vec

    return None


def put(text: str, vec: "list[float]") -> None:
    """写入三级缓存（L1 + L2 + L3）。"""
    if not vec:
        return
    key = _make_key(text)
    _l1_put(key, vec)
    redis_setex(_redis_key(key), settings.embedding_cache_ttl, json.dumps(vec).encode("utf-8"))
    _l3_put(key, text, vec)
