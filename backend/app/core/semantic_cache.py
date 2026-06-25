"""语义缓存：相似问题直接返回缓存答案，降低 LLM 成本。"""

from __future__ import annotations

import hashlib
import json
import logging
import math
import struct
import time
from typing import Any

from app.core.config import settings
from app.core.redis_client import get_redis, redis_get, redis_setex

logger = logging.getLogger(__name__)

# 缓存 key 前缀
_CACHE_PREFIX = "semantic_cache"
# 索引 key（存储所有缓存条目 ID）
_INDEX_KEY = f"{_CACHE_PREFIX}:index"
# 最大缓存条目数（防止无限增长）
_MAX_ENTRIES = 1000
# 相似度计算：向量维度（与 embedding 模型一致）
_EMBEDDING_DIM = 1024


class SemanticCache:
    """语义缓存：相似问题直接返回缓存答案。

    工作流程：
    1. 计算 query 的 embedding
    2. 在 Redis 中查找语义相似的问题（余弦相似度 > threshold）
    3. 命中则直接返回缓存答案
    4. 未命中则执行正常流程，执行完后写入缓存

    存储结构：
    - semantic_cache:{hash} → JSON({query, response, embedding, timestamp})
    - semantic_cache:index → Set of all cache entry hashes
    """

    def __init__(
        self,
        similarity_threshold: float | None = None,
        ttl: int | None = None,
        max_entries: int = _MAX_ENTRIES,
    ) -> None:
        self.similarity_threshold = similarity_threshold or settings.semantic_cache_similarity_threshold
        self.ttl = ttl or settings.semantic_cache_ttl
        self.max_entries = max_entries
        self._enabled = settings.semantic_cache_enabled

    def _hash(self, text: str) -> str:
        """生成查询的哈希键。"""
        return hashlib.sha256(f"{text}|{settings.embedding_model}|{settings.embedding_dim}".encode()).hexdigest()[:16]

    def _serialize_embedding(self, embedding: list[float]) -> bytes:
        """将 embedding 列表序列化为紧凑的 bytes（float32 二进制）。"""
        return struct.pack(f"{len(embedding)}f", *embedding)

    def _deserialize_embedding(self, data: bytes) -> list[float]:
        """从 bytes 反序列化 embedding。"""
        count = len(data) // 4
        return list(struct.unpack(f"{count}f", data))

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        """计算余弦相似度。"""
        if len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    async def get(self, query: str) -> dict | None:
        """查询缓存：找到语义相似的问题则返回。

        返回格式：{"response": str, "confidence": float, "cached": bool}
        未命中返回 None。
        """
        if not self._enabled:
            return None

        redis = get_redis()
        if redis is None:
            return None

        try:
            # 1. 先查精确匹配
            key = f"{_CACHE_PREFIX}:{self._hash(query)}"
            raw = redis_get(key)
            if raw:
                entry = json.loads(raw)
                logger.debug("缓存精确命中: query='%s'", query[:50])
                return {
                    "response": entry["response"],
                    "confidence": entry.get("confidence", 1.0),
                    "cached": True,
                    "cache_type": "exact",
                }

            # 2. 语义相似匹配
            similar = await self._find_similar(query, redis)
            if similar:
                logger.debug("缓存语义命中: query='%s', similar='%s', score=%.3f", query[:50], similar["query"][:50], similar["score"])
                return {
                    "response": similar["response"],
                    "confidence": similar.get("confidence", 0.95),
                    "cached": True,
                    "cache_type": "semantic",
                    "similar_query": similar["query"],
                }

            return None
        except Exception as e:
            logger.warning("语义缓存查询异常: %s", str(e))
            return None

    async def _find_similar(self, query: str, redis: Any) -> dict | None:
        """查找语义相似的缓存条目。"""
        # 计算 query embedding
        from app.core.embedding import embed_query
        try:
            query_embedding = embed_query(query)
        except Exception as e:
            logger.warning("计算 query embedding 失败: %s", str(e))
            return None

        # 获取所有缓存条目 ID
        try:
            entry_ids = redis.smembers(_INDEX_KEY)
        except Exception:
            return None

        if not entry_ids:
            return None

        # 遍历条目，找最相似的（V1 简化：限制扫描数量）
        # 生产环境应使用 Redis 向量索引或专用向量数据库
        best_match = None
        best_score = 0.0

        # 只扫描最近加入的 N 条（通过 score/时间戳过滤）
        # 这里简化处理：随机采样最多 200 条
        entries_to_check = list(entry_ids)[:200]

        for entry_id in entries_to_check:
            try:
                raw = redis_get(f"{_CACHE_PREFIX}:{entry_id.decode() if isinstance(entry_id, bytes) else entry_id}")
                if not raw:
                    continue
                entry = json.loads(raw)
                cached_embedding = entry.get("embedding")
                if not cached_embedding:
                    continue

                score = self._cosine_similarity(query_embedding, cached_embedding)
                if score > best_score:
                    best_score = score
                    best_match = entry
                    best_match["score"] = score
            except Exception:
                continue

        if best_match and best_score >= self.similarity_threshold:
            return best_match

        return None

    async def set(self, query: str, response: dict) -> None:
        """缓存答案，带 TTL 和容量限制。"""
        if not self._enabled:
            return

        redis = get_redis()
        if redis is None:
            return

        try:
            # 计算 embedding
            from app.core.embedding import embed_query
            query_embedding = embed_query(query)
        except Exception as e:
            logger.warning("计算 query embedding 失败，跳过缓存: %s", str(e))
            return

        try:
            key = f"{_CACHE_PREFIX}:{self._hash(query)}"
            entry = {
                "query": query,
                "response": response.get("answer", ""),
                "confidence": response.get("confidence", 1.0),
                "embedding": query_embedding,
                "timestamp": int(time.time()),
            }
            raw = json.dumps(entry, ensure_ascii=False)

            # 写入缓存条目
            redis_setex(key, self.ttl, raw.encode("utf-8"))

            # 加入索引
            redis.sadd(_INDEX_KEY, key.split(":")[-1])

            # 容量限制：超过则随机清理旧条目
            self._enforce_capacity(redis)
        except Exception as e:
            logger.warning("语义缓存写入异常: %s", str(e))

    def _enforce_capacity(self, redis: Any) -> None:
        """ enforce 容量限制，超过则删除旧条目。"""
        try:
            count = redis.scard(_INDEX_KEY)
            if count > self.max_entries:
                # 随机移除 (count - max_entries) 个条目
                excess = count - self.max_entries
                keys = redis.smembers(_INDEX_KEY)
                if keys:
                    import random
                    to_remove = random.sample(list(keys), min(excess, len(keys)))
                    pipe = redis.pipeline()
                    for k in to_remove:
                        pipe.delete(f"{_CACHE_PREFIX}:{k.decode() if isinstance(k, bytes) else k}")
                        pipe.srem(_INDEX_KEY, k)
                    pipe.execute()
                    logger.info("语义缓存容量限制：清理 %d 条旧记录", len(to_remove))
        except Exception as e:
            logger.warning("语义缓存容量清理异常: %s", str(e))

    def clear(self) -> None:
        """清空全部缓存（测试用）。"""
        redis = get_redis()
        if redis is None:
            return
        try:
            keys = redis.smembers(_INDEX_KEY)
            if keys:
                pipe = redis.pipeline()
                for k in keys:
                    pipe.delete(f"{_CACHE_PREFIX}:{k.decode() if isinstance(k, bytes) else k}")
                pipe.delete(_INDEX_KEY)
                pipe.execute()
                logger.info("语义缓存已清空")
        except Exception as e:
            logger.warning("清空语义缓存异常: %s", str(e))


# 全局单例
semantic_cache = SemanticCache()
