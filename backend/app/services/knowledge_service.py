"""知识库业务逻辑：分类 / 文档 / 分片 / FAQ / 同义词 / 索引任务。"""

import hashlib
from pathlib import Path
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core import vectorstore
from app.core.config import settings
from app.core.embedding import embed_query
from app.models import (
    KbCategory,
    KbDocument,
    KbDocumentChunk,
    KbFaq,
    KbIndexTask,
    KbSynonym,
)
from app.schemas.knowledge import (
    CategoryCreate,
    CategoryUpdate,
    DocumentUpdate,
    FaqCreate,
    FaqUpdate,
    SynonymCreate,
    SynonymUpdate,
)


# ==================== 分类 ====================
def list_categories(db: Session) -> list[KbCategory]:
    return list(db.execute(select(KbCategory).order_by(KbCategory.sort, KbCategory.id)).scalars().all())


def get_category(db: Session, category_id: int) -> Optional[KbCategory]:
    return db.get(KbCategory, category_id)


def create_category(db: Session, data: CategoryCreate) -> KbCategory:
    cat = KbCategory(parent_id=data.parent_id, name=data.name, sort=data.sort)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


def update_category(db: Session, cat: KbCategory, data: CategoryUpdate) -> KbCategory:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(cat, field, value)
    db.commit()
    db.refresh(cat)
    return cat


def has_children(db: Session, category_id: int) -> bool:
    """是否存在子分类或挂在该分类下的文档。"""
    child = db.scalar(select(KbCategory.id).where(KbCategory.parent_id == category_id).limit(1))
    doc = db.scalar(select(KbDocument.id).where(KbDocument.category_id == category_id).limit(1))
    return child is not None or doc is not None


def delete_category(db: Session, cat: KbCategory) -> None:
    db.delete(cat)
    db.commit()


# ==================== 文档 ====================
def list_documents(
    db: Session,
    offset: int,
    limit: int,
    keyword: Optional[str] = None,
    category_id: Optional[int] = None,
    status: Optional[int] = None,
    index_status: Optional[int] = None,
) -> tuple[list[KbDocument], int]:
    stmt = select(KbDocument)
    if keyword:
        stmt = stmt.where(KbDocument.title.like(f"%{keyword}%"))
    if category_id is not None:
        stmt = stmt.where(KbDocument.category_id == category_id)
    if status is not None:
        stmt = stmt.where(KbDocument.status == status)
    if index_status is not None:
        stmt = stmt.where(KbDocument.index_status == index_status)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.execute(stmt.order_by(KbDocument.id.desc()).offset(offset).limit(limit)).scalars().all()
    return list(rows), total


def get_document(db: Session, document_id: int) -> Optional[KbDocument]:
    return db.get(KbDocument, document_id)


def save_upload_file(file_bytes: bytes, filename: str) -> tuple[str, str, int]:
    """保存上传文件到本地，返回 (绝对路径, sha256, 大小)。"""
    file_hash = hashlib.sha256(file_bytes).hexdigest()
    ext = Path(filename).suffix
    sub = Path(settings.upload_dir) / file_hash[:2]
    sub.mkdir(parents=True, exist_ok=True)
    dest = sub / f"{file_hash}{ext}"
    dest.write_bytes(file_bytes)
    return str(dest.resolve()).replace("\\", "/"), file_hash, len(file_bytes)


def create_document(db: Session, fields: dict) -> KbDocument:
    """按字段字典创建文档记录（含文件元数据）。"""
    doc = KbDocument(**fields)
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def update_document(db: Session, doc: KbDocument, data: DocumentUpdate) -> KbDocument:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(doc, field, value)
    db.commit()
    db.refresh(doc)
    return doc


def delete_document(db: Session, doc: KbDocument) -> None:
    """删除文档及其分片（ORM 级联）。"""
    db.delete(doc)
    db.commit()


# ==================== 分片 ====================
def list_chunks(db: Session, document_id: int) -> list[KbDocumentChunk]:
    return list(
        db.execute(
            select(KbDocumentChunk)
            .where(KbDocumentChunk.document_id == document_id)
            .order_by(KbDocumentChunk.chunk_index)
        )
        .scalars()
        .all()
    )


# ==================== 索引任务 ====================
def list_index_tasks(
    db: Session,
    offset: int,
    limit: int,
    document_id: Optional[int] = None,
    status: Optional[int] = None,
) -> tuple[list[KbIndexTask], int]:
    stmt = select(KbIndexTask)
    if document_id is not None:
        stmt = stmt.where(KbIndexTask.document_id == document_id)
    if status is not None:
        stmt = stmt.where(KbIndexTask.status == status)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.execute(stmt.order_by(KbIndexTask.id.desc()).offset(offset).limit(limit)).scalars().all()
    return list(rows), total


# ==================== FAQ ====================
def list_faqs(
    db: Session,
    offset: int,
    limit: int,
    keyword: Optional[str] = None,
    category_id: Optional[int] = None,
    status: Optional[int] = None,
) -> tuple[list[KbFaq], int]:
    stmt = select(KbFaq)
    if keyword:
        stmt = stmt.where(KbFaq.question.like(f"%{keyword}%"))
    if category_id is not None:
        stmt = stmt.where(KbFaq.category_id == category_id)
    if status is not None:
        stmt = stmt.where(KbFaq.status == status)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.execute(stmt.order_by(KbFaq.id.desc()).offset(offset).limit(limit)).scalars().all()
    return list(rows), total


def get_faq(db: Session, faq_id: int) -> Optional[KbFaq]:
    return db.get(KbFaq, faq_id)


def _faq_vector_id(faq_id: int) -> str:
    return f"faq{faq_id}"


def _index_faq(db: Session, faq: KbFaq) -> None:
    """将 FAQ 问题向量化写入向量库(FAQ 专用集合)，回填 vector_id。失败不阻断保存。"""
    try:
        vec = embed_query(faq.question)
        vid = _faq_vector_id(faq.id)
        vectorstore.upsert(
            ids=[vid],
            embeddings=[vec],
            documents=[faq.question],
            metadatas=[{"faq_id": faq.id}],
            collection=settings.faq_collection,
        )
        if faq.vector_id != vid:
            faq.vector_id = vid
            db.commit()
    except Exception:
        pass


def _remove_faq_vector(faq_id: int) -> None:
    try:
        vectorstore.delete(ids=[_faq_vector_id(faq_id)], collection=settings.faq_collection)
    except Exception:
        pass


def create_faq(db: Session, data: FaqCreate) -> KbFaq:
    faq = KbFaq(
        question=data.question, answer=data.answer, category_id=data.category_id, status=data.status
    )
    db.add(faq)
    db.commit()
    db.refresh(faq)
    _index_faq(db, faq)  # 自动向量化入库
    return faq


def update_faq(db: Session, faq: KbFaq, data: FaqUpdate) -> KbFaq:
    fields = data.model_dump(exclude_unset=True)
    for field, value in fields.items():
        setattr(faq, field, value)
    db.commit()
    db.refresh(faq)
    # 问题文本变化或被禁用时，更新/清理向量
    if "question" in fields:
        _index_faq(db, faq)
    if fields.get("status") == 0:
        _remove_faq_vector(faq.id)
    return faq


def set_faq_status(db: Session, faq: KbFaq, status: int) -> KbFaq:
    """仅切换 FAQ 启用状态（轻量，不改动问题/答案文本）。

    同步维护向量：启用→重建可检索向量；禁用→移除向量。
    这样重新启用的 FAQ 仍可被检索命中，避免“启用后搜不到”的问题。
    """
    new_status = 1 if status else 0
    faq.status = new_status
    db.commit()
    db.refresh(faq)
    if new_status == 0:
        _remove_faq_vector(faq.id)
    else:
        _index_faq(db, faq)
    return faq


def delete_faq(db: Session, faq: KbFaq) -> None:
    _remove_faq_vector(faq.id)
    db.delete(faq)
    db.commit()


# ==================== 同义词 ====================
def list_synonyms(
    db: Session, offset: int, limit: int, keyword: Optional[str] = None, status: Optional[int] = None
) -> tuple[list[KbSynonym], int]:
    stmt = select(KbSynonym)
    if keyword:
        stmt = stmt.where(KbSynonym.term.like(f"%{keyword}%"))
    if status is not None:
        stmt = stmt.where(KbSynonym.status == status)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.execute(stmt.order_by(KbSynonym.id.desc()).offset(offset).limit(limit)).scalars().all()
    return list(rows), total


def get_synonym(db: Session, synonym_id: int) -> Optional[KbSynonym]:
    return db.get(KbSynonym, synonym_id)


def create_synonym(db: Session, data: SynonymCreate) -> KbSynonym:
    syn = KbSynonym(term=data.term, synonyms=data.synonyms, status=data.status)
    db.add(syn)
    db.commit()
    db.refresh(syn)
    return syn


def update_synonym(db: Session, syn: KbSynonym, data: SynonymUpdate) -> KbSynonym:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(syn, field, value)
    db.commit()
    db.refresh(syn)
    return syn


def delete_synonym(db: Session, syn: KbSynonym) -> None:
    db.delete(syn)
    db.commit()
