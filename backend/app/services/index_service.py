"""文档解析入库服务：parse(解析切分) 与 index(向量化入库)。

均设计为后台任务执行，自带独立 DB 会话；通过 kb_index_task 记录进度与状态。
任务状态：0排队 1执行中 2成功 3失败
文档 parse_status / index_status：0待处理 1处理中 2成功 3失败
"""

from datetime import datetime

from sqlalchemy import select

from app.core import vectorstore
from app.core.config import settings
from app.core.database import SessionLocal
from app.core.document_parser import parse_file
from app.core.embedding import embed_texts
from app.core.semantic_chunker import split_text_semantic
from app.models import KbDocument, KbDocumentChunk, KbIndexTask

_EMBED_BATCH = 10  # 每次向量化的分片数


def create_task(db, document_id: int, task_type: int) -> KbIndexTask:
    """创建索引任务记录(排队状态)。task_type: 1解析 2入库。"""
    task = KbIndexTask(document_id=document_id, task_type=task_type, status=0, progress=0)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def _vector_id(document_id: int, chunk_id: int) -> str:
    return f"doc{document_id}_c{chunk_id}"


def _finish_task(db, task: KbIndexTask, status: int, progress: int, error: str | None = None) -> None:
    task.status = status
    task.progress = progress
    task.error_msg = error
    task.finished_at = datetime.now()
    db.commit()


# ==================== 解析（解析+切分→分片） ====================
def run_parse(document_id: int, task_id: int) -> None:
    """后台任务：解析文档并写入分片。"""
    db = SessionLocal()
    try:
        task = db.get(KbIndexTask, task_id)
        doc = db.get(KbDocument, document_id)
        if doc is None:
            _finish_task(db, task, 3, 0, "文档不存在")
            return
        task.status = 1
        task.started_at = datetime.now()
        doc.parse_status = 1
        db.commit()

        if not doc.file_path:
            _finish_task(db, task, 3, 0, "文档无关联文件")
            doc.parse_status = 3
            db.commit()
            return

        segments = parse_file(doc.file_path)

        # 清理旧分片与旧向量(重新解析后 chunk 重建，旧向量作废)
        db.query(KbDocumentChunk).filter(KbDocumentChunk.document_id == document_id).delete()
        db.commit()
        try:
            vectorstore.delete(where={"document_id": document_id})
        except Exception:
            pass

        chunk_index = 0
        for seg in segments:
            for piece in split_text_semantic(seg["text"]):
                db.add(
                    KbDocumentChunk(
                        document_id=document_id,
                        chunk_index=chunk_index,
                        content=piece,
                        content_tokens=len(piece),
                        page_no=seg["page_no"],
                    )
                )
                chunk_index += 1
        doc.parse_status = 2
        doc.index_status = 0  # 需重新索引
        db.commit()
        _finish_task(db, task, 2, 100)
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        task = db.get(KbIndexTask, task_id)
        doc = db.get(KbDocument, document_id)
        if doc:
            doc.parse_status = 3
        if task:
            _finish_task(db, task, 3, 0, str(exc)[:1000])
        db.commit()
    finally:
        db.close()


# ==================== 入库（向量化→写向量库） ====================
def run_index(document_id: int, task_id: int) -> None:
    """后台任务：将文档分片向量化并写入向量库。"""
    db = SessionLocal()
    try:
        task = db.get(KbIndexTask, task_id)
        doc = db.get(KbDocument, document_id)
        if doc is None:
            _finish_task(db, task, 3, 0, "文档不存在")
            return
        task.status = 1
        task.started_at = datetime.now()
        doc.index_status = 1
        db.commit()

        chunks = list(
            db.execute(
                select(KbDocumentChunk)
                .where(KbDocumentChunk.document_id == document_id)
                .order_by(KbDocumentChunk.chunk_index)
            )
            .scalars()
            .all()
        )
        if not chunks:
            _finish_task(db, task, 3, 0, "无分片，请先解析")
            doc.index_status = 3
            db.commit()
            return

        # 清理旧向量后重建
        try:
            vectorstore.delete(where={"document_id": document_id})
        except Exception:
            pass

        done = 0
        for start in range(0, len(chunks), _EMBED_BATCH):
            batch = chunks[start : start + _EMBED_BATCH]
            vectors = embed_texts([c.content for c in batch])
            ids, embeds, docs, metas = [], [], [], []
            for chunk, vec in zip(batch, vectors):
                vid = _vector_id(document_id, chunk.id)
                chunk.vector_id = vid
                chunk.embedding_model = settings.embedding_model
                ids.append(vid)
                embeds.append(vec)
                docs.append(chunk.content)
                metas.append(
                    {
                        "document_id": document_id,
                        "chunk_id": chunk.id,
                        "page_no": chunk.page_no if chunk.page_no is not None else -1,
                    }
                )
            vectorstore.upsert(ids=ids, embeddings=embeds, documents=docs, metadatas=metas)
            done += len(batch)
            task.progress = int(done / len(chunks) * 100)
            db.commit()

        doc.index_status = 2
        db.commit()
        _finish_task(db, task, 2, 100)
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        task = db.get(KbIndexTask, task_id)
        doc = db.get(KbDocument, document_id)
        if doc:
            doc.index_status = 3
        if task:
            _finish_task(db, task, 3, 0, str(exc)[:1000])
        db.commit()
    finally:
        db.close()


def remove_document_vectors(document_id: int) -> None:
    """删除文档时清理其向量(供 router 调用)。"""
    try:
        vectorstore.delete(where={"document_id": document_id})
    except Exception:
        pass
