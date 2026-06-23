"""语义分块：基于句子嵌入相似度的百分位落差法（LangChain SemanticChunker 思路）。

步骤：
  1. 按句子边界分句（保证 chunk 不切断句子）
  2. 给每个句子算嵌入向量
  3. 计算相邻句子距离 = 1 - 余弦相似度
  4. 取所有距离的 P 百分位为阈值，距离超阈值处视为"语义断点"
  5. 按断点分组，并叠加大小约束：
     - 当前块未达 min_chars 时，即使遇到断点也不切（短句合并）
     - 当前块超过 max_chars 时，在句子边界强制切（长句单独成块）

注意：本模块会调用 embedding（每个句子一次，批量），解析阶段会因此变慢。
"""

import math
import re

from app.core.config import settings
from app.core.embedding import embed_texts
from app.core.text_splitter import _split_sentences

_EMBED_BATCH = 10


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def _percentile(values: list[float], p: float) -> float:
    """线性插值百分位（p 为 0~100）。"""
    if not values:
        return 0.0
    s = sorted(values)
    if len(s) == 1:
        return s[0]
    k = (len(s) - 1) * p / 100.0
    f = int(math.floor(k))
    c = min(f + 1, len(s) - 1)
    if f == c:
        return s[f]
    return s[f] + (s[c] - s[f]) * (k - f)


def split_text_semantic(
    text: str,
    min_chars: int | None = None,
    max_chars: int | None = None,
    percentile: int | None = None,
) -> list[str]:
    """语义分块，返回 chunk 文本列表。"""
    min_chars = min_chars or settings.chunk_min_chars
    max_chars = max_chars or settings.chunk_max_chars
    pct = percentile if percentile is not None else settings.semantic_breakpoint_percentile

    text = re.sub(r"[ \t]+", " ", text).strip()
    if not text:
        return []

    sentences = [s.strip() for s in _split_sentences(text) if s.strip()]
    if len(sentences) <= 1:
        # 0 或 1 句：单句即使超长也单独成块（不切断句子）
        return sentences

    # 句子嵌入（批量）
    vecs: list[list[float]] = []
    for i in range(0, len(sentences), _EMBED_BATCH):
        vecs.extend(embed_texts(sentences[i : i + _EMBED_BATCH]))

    # 相邻句子距离与百分位阈值
    distances = [1.0 - _cosine(vecs[i], vecs[i + 1]) for i in range(len(sentences) - 1)]
    threshold = _percentile(distances, pct)
    breakpoints = {i for i, d in enumerate(distances) if d > threshold}

    # 按语义断点 + 大小约束分组
    chunks: list[str] = []
    cur: list[str] = []
    cur_len = 0
    for i, sent in enumerate(sentences):
        slen = len(sent)
        # 加入前：当前块非空且加入后会超过上限 → 先在句子边界断开
        if cur and cur_len + slen > max_chars:
            chunks.append("".join(cur))
            cur, cur_len = [], 0
        cur.append(sent)
        cur_len += slen
        # 语义断点且当前块已达最小长度 → 断开（短于 min 则继续合并）
        if i in breakpoints and cur_len >= min_chars:
            chunks.append("".join(cur))
            cur, cur_len = [], 0

    # 处理结尾：过小的尾块在不超上限时并回上一块，否则独立成块
    if cur:
        tail = "".join(cur)
        if chunks and cur_len < min_chars and len(chunks[-1]) + len(tail) <= max_chars:
            chunks[-1] += tail
        else:
            chunks.append(tail)

    return [c.strip() for c in chunks if c.strip()]
