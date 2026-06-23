"""知识库模块 ORM 模型（对应 kb_* 表）。"""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import BigInteger, Date, DateTime, Integer, SmallInteger, String, Text, func
from sqlalchemy.dialects.mysql import JSON, MEDIUMTEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TABLE_ARGS, Base


class KbCategory(Base):
    """文档分类表：支持多级分类。"""

    __tablename__ = "kb_category"
    __table_args__ = {"comment": "文档分类表：支持多级分类", **TABLE_ARGS}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="分类ID")
    parent_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True, comment="父分类ID,0为顶级")
    name: Mapped[str] = mapped_column(String(128), comment="分类名称")
    sort: Mapped[int] = mapped_column(Integer, default=0, comment="排序值,越小越靠前")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment="创建时间")


class KbDocument(Base):
    """文档主表：知识库文档及其元数据。"""

    __tablename__ = "kb_document"
    __table_args__ = {"comment": "文档主表：知识库文档及其元数据", **TABLE_ARGS}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="文档ID")
    title: Mapped[str] = mapped_column(String(255), comment="文档标题")
    category_id: Mapped[Optional[int]] = mapped_column(BigInteger, index=True, comment="所属分类ID")
    source: Mapped[Optional[str]] = mapped_column(String(255), comment="来源(发文机关/网站)")
    source_level: Mapped[Optional[int]] = mapped_column(SmallInteger, comment="政策层级1国2省3市4校")
    file_name: Mapped[Optional[str]] = mapped_column(String(255), comment="原始文件名")
    file_path: Mapped[Optional[str]] = mapped_column(String(512), comment="文件存储路径/对象存储Key")
    file_type: Mapped[Optional[str]] = mapped_column(String(32), comment="pdf/docx/xlsx/txt/html")
    file_size: Mapped[Optional[int]] = mapped_column(BigInteger, comment="文件大小(字节)")
    file_hash: Mapped[Optional[str]] = mapped_column(String(64), index=True, comment="内容哈希SHA-256,去重")
    effective_date: Mapped[Optional[date]] = mapped_column(Date, index=True, comment="生效日期")
    expire_date: Mapped[Optional[date]] = mapped_column(Date, comment="失效日期,空为长期有效")
    confidential_level: Mapped[int] = mapped_column(SmallInteger, default=1, comment="密级1公开2校内3受限")
    parse_status: Mapped[int] = mapped_column(SmallInteger, default=0, comment="0待解析1解析中2成功3失败")
    index_status: Mapped[int] = mapped_column(SmallInteger, default=0, index=True, comment="0未索引1索引中2已索引3失败")
    status: Mapped[int] = mapped_column(SmallInteger, default=1, index=True, comment="1上架可检索0下架")
    uploader_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment="上传人用户ID")
    remark: Mapped[Optional[str]] = mapped_column(String(512), comment="备注")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )

    chunks: Mapped[list["KbDocumentChunk"]] = relationship(
        back_populates="document",
        primaryjoin="KbDocument.id==foreign(KbDocumentChunk.document_id)",
        cascade="all, delete-orphan",
    )


class KbDocumentChunk(Base):
    """文档分片表：切分文本块，向量存外部向量库。"""

    __tablename__ = "kb_document_chunk"
    __table_args__ = {"comment": "文档分片表：切分文本块,含关键词全文索引", **TABLE_ARGS}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="分片ID")
    document_id: Mapped[int] = mapped_column(BigInteger, index=True, comment="所属文档ID")
    chunk_index: Mapped[int] = mapped_column(Integer, comment="分片序号(从0开始)")
    content: Mapped[str] = mapped_column(MEDIUMTEXT, comment="分片文本内容")
    content_tokens: Mapped[Optional[int]] = mapped_column(Integer, comment="分片token数(估算)")
    heading_path: Mapped[Optional[str]] = mapped_column(String(512), comment="标题层级路径")
    page_no: Mapped[Optional[int]] = mapped_column(Integer, comment="原文页码(溯源)")
    vector_id: Mapped[Optional[str]] = mapped_column(String(128), index=True, comment="向量库中的向量ID")
    embedding: Mapped[Optional[dict]] = mapped_column(JSON, comment="向量备份(小规模可选)")
    embedding_model: Mapped[Optional[str]] = mapped_column(String(64), comment="生成向量的模型名")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment="创建时间")

    document: Mapped["KbDocument"] = relationship(
        back_populates="chunks",
        primaryjoin="foreign(KbDocumentChunk.document_id)==KbDocument.id",
    )


class KbSynonym(Base):
    """同义词词典表：校内黑话/专有名词映射。"""

    __tablename__ = "kb_synonym"
    __table_args__ = {"comment": "同义词词典表：提升召回", **TABLE_ARGS}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="主键")
    term: Mapped[str] = mapped_column(String(128), index=True, comment="标准词")
    synonyms: Mapped[str] = mapped_column(String(512), comment="同义词,逗号分隔")
    status: Mapped[int] = mapped_column(SmallInteger, default=1, comment="1启用0禁用")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment="创建时间")


class KbFaq(Base):
    """FAQ问答对表：高频问题标准答复。"""

    __tablename__ = "kb_faq"
    __table_args__ = {"comment": "FAQ问答对表", **TABLE_ARGS}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="FAQ ID")
    question: Mapped[str] = mapped_column(String(512), comment="标准问题")
    answer: Mapped[str] = mapped_column(Text, comment="标准答案")
    category_id: Mapped[Optional[int]] = mapped_column(BigInteger, index=True, comment="所属分类ID")
    vector_id: Mapped[Optional[str]] = mapped_column(String(128), comment="问题向量ID")
    hit_count: Mapped[int] = mapped_column(Integer, default=0, comment="命中次数(热度)")
    status: Mapped[int] = mapped_column(SmallInteger, default=1, comment="1启用0禁用")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )


class KbIndexTask(Base):
    """索引任务表：解析/入库异步任务监控。"""

    __tablename__ = "kb_index_task"
    __table_args__ = {"comment": "索引任务表：文档解析/入库任务监控", **TABLE_ARGS}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="任务ID")
    document_id: Mapped[int] = mapped_column(BigInteger, index=True, comment="关联文档ID")
    task_type: Mapped[int] = mapped_column(SmallInteger, comment="1解析2入库3重建4删除索引")
    status: Mapped[int] = mapped_column(SmallInteger, default=0, index=True, comment="0排队1执行中2成功3失败")
    progress: Mapped[int] = mapped_column(SmallInteger, default=0, comment="进度百分比0-100")
    error_msg: Mapped[Optional[str]] = mapped_column(String(1024), comment="失败原因")
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, comment="开始时间")
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, comment="结束时间")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment="创建时间")
