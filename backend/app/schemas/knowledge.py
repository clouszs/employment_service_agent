"""知识库模块 schema（对应 kb_* 表）。

枚举约定：
  source_level:       1国家 2省 3市 4校级
  confidential_level: 1公开 2校内 3受限
  parse_status:       0待解析 1解析中 2成功 3失败
  index_status:       0未索引 1索引中 2已索引 3失败
  status:             1上架 0下架
  task_type:          1解析 2向量化入库 3重建 4删除索引
"""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


# ---------------- 分类 ----------------
class CategoryBase(BaseModel):
    parent_id: int = Field(default=0, description="父分类ID,0为顶级")
    name: str = Field(max_length=128, description="分类名称")
    sort: int = Field(default=0, description="排序值")


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    parent_id: Optional[int] = None
    name: Optional[str] = Field(default=None, max_length=128)
    sort: Optional[int] = None


class CategoryRead(ORMModel):
    id: int
    parent_id: int
    name: str
    sort: int
    created_at: datetime


# ---------------- 文档 ----------------
class DocumentBase(BaseModel):
    title: str = Field(max_length=255, description="文档标题")
    category_id: Optional[int] = Field(default=None, description="所属分类ID")
    source: Optional[str] = Field(default=None, max_length=255, description="来源")
    source_level: Optional[int] = Field(default=None, description="政策层级1国2省3市4校")
    effective_date: Optional[date] = Field(default=None, description="生效日期")
    expire_date: Optional[date] = Field(default=None, description="失效日期")
    confidential_level: int = Field(default=1, description="密级1公开2校内3受限")
    remark: Optional[str] = Field(default=None, max_length=512, description="备注")


class DocumentCreate(DocumentBase):
    file_name: Optional[str] = Field(default=None, max_length=255)
    file_type: Optional[str] = Field(default=None, max_length=32)


class DocumentUpdate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=255)
    category_id: Optional[int] = None
    source: Optional[str] = Field(default=None, max_length=255)
    source_level: Optional[int] = None
    effective_date: Optional[date] = None
    expire_date: Optional[date] = None
    confidential_level: Optional[int] = None
    status: Optional[int] = Field(default=None, description="1上架0下架")
    remark: Optional[str] = Field(default=None, max_length=512)


class DocumentRead(ORMModel):
    id: int
    title: str
    category_id: Optional[int]
    source: Optional[str]
    source_level: Optional[int]
    file_name: Optional[str]
    file_type: Optional[str]
    file_size: Optional[int]
    effective_date: Optional[date]
    expire_date: Optional[date]
    confidential_level: int
    parse_status: int
    index_status: int
    status: int
    uploader_id: Optional[int]
    remark: Optional[str]
    created_at: datetime
    updated_at: datetime


# ---------------- 文档分片 ----------------
class ChunkRead(ORMModel):
    id: int
    document_id: int
    chunk_index: int
    content: str
    content_tokens: Optional[int]
    heading_path: Optional[str]
    page_no: Optional[int]
    vector_id: Optional[str]
    embedding_model: Optional[str]
    created_at: datetime


# ---------------- 同义词 ----------------
class SynonymBase(BaseModel):
    term: str = Field(max_length=128, description="标准词")
    synonyms: str = Field(max_length=512, description="同义词,逗号分隔")
    status: int = Field(default=1, description="1启用0禁用")


class SynonymCreate(SynonymBase):
    pass


class SynonymUpdate(BaseModel):
    term: Optional[str] = Field(default=None, max_length=128)
    synonyms: Optional[str] = Field(default=None, max_length=512)
    status: Optional[int] = None


class SynonymRead(ORMModel):
    id: int
    term: str
    synonyms: str
    status: int
    created_at: datetime


# ---------------- FAQ ----------------
class FaqBase(BaseModel):
    question: str = Field(max_length=512, description="标准问题")
    answer: str = Field(description="标准答案")
    category_id: Optional[int] = Field(default=None, description="所属分类ID")
    status: int = Field(default=1, description="1启用0禁用")


class FaqCreate(FaqBase):
    pass


class FaqUpdate(BaseModel):
    question: Optional[str] = Field(default=None, max_length=512)
    answer: Optional[str] = None
    category_id: Optional[int] = None
    status: Optional[int] = None


class FaqStatusUpdate(BaseModel):
    status: int = Field(description="1启用 0禁用")


class FaqBatchAction(BaseModel):
    action: str = Field(description="enable / disable / delete")
    ids: list[int] = Field(description="目标 FAQ ID 列表")


class FaqRead(ORMModel):
    id: int
    question: str
    answer: str
    category_id: Optional[int]
    vector_id: Optional[str]
    hit_count: int
    ask_count: int
    status: int
    created_at: datetime
    updated_at: datetime


# ---------------- 索引任务 ----------------
class IndexTaskRead(ORMModel):
    id: int
    document_id: int
    task_type: int
    status: int
    progress: int
    error_msg: Optional[str]
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    created_at: datetime
