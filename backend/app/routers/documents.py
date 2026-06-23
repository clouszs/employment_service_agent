"""文档管理接口（含文件上传、分片查看）。

注意：文档解析(parse)与向量化入库(index)的实际执行依赖向量库/embedding 选型，
待该决策确定后再实现；本阶段提供文档与元数据的完整管理能力。
"""

from datetime import date
from pathlib import Path
from typing import Optional

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.core.response import success
from app.models import SysUser
from app.schemas.knowledge import ChunkRead, DocumentRead, DocumentUpdate, IndexTaskRead
from app.services import index_service
from app.services import knowledge_service as svc

router = APIRouter(prefix="/documents", tags=["知识库-文档"])


@router.get("", summary="文档列表(分页)")
def list_documents(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
    keyword: Optional[str] = Query(None, description="标题模糊搜索"),
    category_id: Optional[int] = Query(None),
    status_: Optional[int] = Query(None, alias="status"),
    index_status: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    _: SysUser = Depends(get_current_user),
) -> dict:
    rows, total = svc.list_documents(
        db, offset=(page - 1) * size, limit=size, keyword=keyword,
        category_id=category_id, status=status_, index_status=index_status,
    )
    return success(
        {
            "total": total,
            "page": page,
            "size": size,
            "items": [DocumentRead.model_validate(d).model_dump() for d in rows],
        }
    )


@router.get("/{document_id}", summary="文档详情")
def get_document(
    document_id: int, db: Session = Depends(get_db), _: SysUser = Depends(get_current_user)
) -> dict:
    doc = svc.get_document(db, document_id)
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文档不存在")
    return success(DocumentRead.model_validate(doc).model_dump())


@router.post("", summary="上传文档", status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(..., description="文档文件"),
    title: str = Form(..., description="文档标题"),
    category_id: Optional[int] = Form(None),
    source: Optional[str] = Form(None),
    source_level: Optional[int] = Form(None),
    effective_date: Optional[date] = Form(None),
    expire_date: Optional[date] = Form(None),
    confidential_level: int = Form(1),
    remark: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current: SysUser = Depends(require_roles("admin", "editor")),
) -> dict:
    content = await file.read()
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"文件超过{settings.max_upload_mb}MB")

    file_path, file_hash, file_size = svc.save_upload_file(content, file.filename or "unknown")
    fields = {
        "title": title,
        "category_id": category_id,
        "source": source,
        "source_level": source_level,
        "effective_date": effective_date,
        "expire_date": expire_date,
        "confidential_level": confidential_level,
        "remark": remark,
        "file_name": file.filename,
        "file_path": file_path,
        "file_type": (Path(file.filename).suffix.lstrip(".").lower() if file.filename else None),
        "file_size": file_size,
        "file_hash": file_hash,
        "uploader_id": current.id,
        "parse_status": 0,
        "index_status": 0,
        "status": 1,
    }
    doc = svc.create_document(db, fields)
    return success(DocumentRead.model_validate(doc).model_dump(), message="上传成功")


@router.put("/{document_id}", summary="修改文档元数据")
def update_document(
    document_id: int,
    payload: DocumentUpdate,
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_roles("admin", "editor")),
) -> dict:
    doc = svc.get_document(db, document_id)
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文档不存在")
    doc = svc.update_document(db, doc, payload)
    return success(DocumentRead.model_validate(doc).model_dump(), message="更新成功")


@router.delete("/{document_id}", summary="删除文档(连带分片)")
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_roles("admin", "editor")),
) -> dict:
    doc = svc.get_document(db, document_id)
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文档不存在")
    index_service.remove_document_vectors(document_id)
    svc.delete_document(db, doc)
    return success(message="已删除")


@router.get("/{document_id}/chunks", summary="查看文档分片")
def list_chunks(
    document_id: int, db: Session = Depends(get_db), _: SysUser = Depends(get_current_user)
) -> dict:
    if svc.get_document(db, document_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文档不存在")
    chunks = svc.list_chunks(db, document_id)
    return success([ChunkRead.model_validate(c).model_dump() for c in chunks])


@router.post("/{document_id}/parse", summary="解析文档(后台:提取+切分)")
def parse_document(
    document_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_roles("admin", "editor")),
) -> dict:
    doc = svc.get_document(db, document_id)
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文档不存在")
    if not doc.file_path:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="文档无关联文件")
    task = index_service.create_task(db, document_id, task_type=1)
    doc.parse_status = 1
    db.commit()
    background_tasks.add_task(index_service.run_parse, document_id, task.id)
    return success(IndexTaskRead.model_validate(task).model_dump(), message="解析任务已提交")


@router.post("/{document_id}/index", summary="向量化入库(后台:embedding+写向量库)")
def index_document(
    document_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_roles("admin", "editor")),
) -> dict:
    doc = svc.get_document(db, document_id)
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文档不存在")
    if doc.parse_status != 2 or not svc.list_chunks(db, document_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请先解析文档生成分片")
    task = index_service.create_task(db, document_id, task_type=2)
    doc.index_status = 1
    db.commit()
    background_tasks.add_task(index_service.run_index, document_id, task.id)
    return success(IndexTaskRead.model_validate(task).model_dump(), message="入库任务已提交")
