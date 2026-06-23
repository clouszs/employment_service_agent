"""语义文本切分：按句子边界聚合到目标大小，相邻片重叠。

默认每片 500 字符、重叠 50 字符。优先在句子边界(中英文标点/换行)切，
避免切断句子；超长单句按目标大小硬切。
"""

import re

# 句子结束边界：中英文句末标点、分号、换行
_SENT_PATTERN = re.compile(r"(?<=[。！？!?；;\n])")


def _split_sentences(text: str) -> list[str]:
    parts = [s for s in _SENT_PATTERN.split(text) if s and s.strip()]
    return parts


def split_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """将文本语义切分为若干片。"""
    text = re.sub(r"[ \t]+", " ", text).strip()
    if not text:
        return []

    sentences = _split_sentences(text)
    chunks: list[str] = []
    cur = ""
    for sent in sentences:
        if len(sent) > chunk_size:
            # 超长句：先收尾当前片，再硬切长句
            if cur:
                chunks.append(cur)
                cur = ""
            for i in range(0, len(sent), chunk_size):
                chunks.append(sent[i : i + chunk_size])
            continue
        if len(cur) + len(sent) <= chunk_size:
            cur += sent
        else:
            if cur:
                chunks.append(cur)
            cur = sent
    if cur:
        chunks.append(cur)

    # 加重叠：每片头部拼接上一片尾部 overlap 字符
    if overlap > 0 and len(chunks) > 1:
        result = [chunks[0]]
        for i in range(1, len(chunks)):
            prev_tail = chunks[i - 1][-overlap:]
            result.append(prev_tail + chunks[i])
        chunks = result

    return [c.strip() for c in chunks if c.strip()]
