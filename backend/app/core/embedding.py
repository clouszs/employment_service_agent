"""文本向量化客户端：DashScope text-embedding-v4（OpenAI 兼容接口）。"""

import logging
from functools import lru_cache

from openai import APIError, RateLimitError, Timeout
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.config import settings

logger = logging.getLogger(__name__)

# 超时配置
_EMBEDDING_TIMEOUT = 60.0  # 单次请求超时（秒）
_EMBEDDING_MAX_RETRIES = 3  # 最大重试次数

# DashScope text-embedding 单次请求最多 10 条
_MAX_BATCH = 10


@lru_cache
def _client() -> "OpenAI":
    """创建 OpenAI 客户端（带超时配置）。"""
    from openai import OpenAI
    return OpenAI(
        api_key=settings.dashscope_api_key,
        base_url=settings.dashscope_base_url,
        timeout=Timeout(_EMBEDDING_TIMEOUT),
        max_retries=0,  # 我们自己控制重试
    )


@retry(
    stop=stop_after_attempt(_EMBEDDING_MAX_RETRIES),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
    before_sleep=lambda retry_state: logger.warning(
        "Embedding API调用失败，第%d次重试中... (等待%d秒)",
        retry_state.attempt_number,
        2 * (2 ** (retry_state.attempt_number - 1)),
    ),
)
def _create_embedding_with_retry(client, model: str, input_texts: list[str]) -> "Any":
    """带重试的嵌入创建。"""
    try:
        return client.embeddings.create(
            model=model,
            input=input_texts,
            dimensions=settings.embedding_dim,
            encoding_format="float",
        )
    except (RateLimitError, Timeout, APIError) as e:
        logger.warning("Embedding API错误: %s", str(e))
        raise


def embed_texts(texts: list[str]) -> list[list[float]]:
    """批量向量化，返回与输入顺序一致的向量列表（内部自动按 10 条分批）。"""
    if not texts:
        return []

    out: list[list[float]] = []
    client = _client()

    for i in range(0, len(texts), _MAX_BATCH):
        batch = texts[i: i + _MAX_BATCH]
        try:
            resp = _create_embedding_with_retry(client, settings.embedding_model, batch)
            items = sorted(resp.data, key=lambda d: d.index)
            out.extend(item.embedding for item in items)
        except Exception as e:
            logger.error("Embedding批处理最终失败: %s", str(e))
            # 返回空向量，后续检索会走兜底
            out.extend([[0.0] * settings.embedding_dim for _ in batch])

    return out


def embed_query(text: str) -> list[float]:
    """单条文本向量化（用于检索查询），带三级缓存（L1内存→L2 Redis→L3 MySQL→API）。

    缓存命中直接返回；未命中调用 API 后回写缓存。
    API 失败兜底的零向量不写入缓存，避免污染。
    """
    from app.core import embedding_cache

    cached = embedding_cache.get(text)
    if cached is not None:
        return cached

    results = embed_texts([text])
    vec = results[0] if results else [0.0] * settings.embedding_dim

    # 仅缓存有效向量（排除 API 失败时返回的全零兜底向量）
    if any(vec):
        embedding_cache.put(text, vec)

    return vec
