"""向量库封装：Chroma 本地嵌入式持久化。

存储约定：
  - 每个向量的 id 用文档分片的 vector_id（字符串）
  - metadata 至少含 document_id / chunk_id，便于检索后回查 MySQL
  - 向量由外部(embedding 模块)生成后传入，本模块不负责向量化
"""

from functools import lru_cache
from typing import Optional

import chromadb

from app.core.config import settings


@lru_cache
def _collection(name: str):
    """获取(或创建)持久化集合，余弦距离。"""
    client = chromadb.PersistentClient(path=settings.chroma_dir)
    return client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},
    )


def _col(collection: Optional[str]):
    return _collection(collection or settings.chroma_collection)


def upsert(
    ids: list[str],
    embeddings: list[list[float]],
    documents: list[str],
    metadatas: list[dict],
    collection: Optional[str] = None,
) -> None:
    """新增/更新向量。collection 默认文档分片集合。"""
    if not ids:
        return
    _col(collection).upsert(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)


def query(
    embedding: list[float], top_k: int = 5, where: Optional[dict] = None, collection: Optional[str] = None
) -> list[dict]:
    """向量检索，返回 [{id, document, metadata, score}]，score 为相似度(1-距离)。"""
    res = _col(collection).query(
        query_embeddings=[embedding],
        n_results=top_k,
        where=where,
        include=["documents", "metadatas", "distances"],
    )
    hits: list[dict] = []
    ids = res.get("ids", [[]])[0]
    docs = res.get("documents", [[]])[0]
    metas = res.get("metadatas", [[]])[0]
    dists = res.get("distances", [[]])[0]
    for i in range(len(ids)):
        hits.append(
            {
                "id": ids[i],
                "document": docs[i] if i < len(docs) else None,
                "metadata": metas[i] if i < len(metas) else {},
                "score": round(1 - dists[i], 4) if i < len(dists) else None,
            }
        )
    return hits


def delete(ids: Optional[list[str]] = None, where: Optional[dict] = None, collection: Optional[str] = None) -> None:
    """按 id 或条件删除向量。"""
    if ids:
        _col(collection).delete(ids=ids)
    elif where:
        _col(collection).delete(where=where)


def count(collection: Optional[str] = None) -> int:
    """集合内向量数量。"""
    return _col(collection).count()
