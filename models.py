"""
高校智慧就业服务平台 - AI问答模块 —— ORM 实体模型
配套：数据库设计.sql、ER图.md
ORM：SQLAlchemy 2.0（Declarative + Mapped 类型注解风格）
数据库：MySQL 8.0

依赖：
    pip install "sqlalchemy>=2.0" pymysql

用法示例见文件末尾 __main__。
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.mysql import JSON, MEDIUMTEXT
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """所有模型的基类。"""


# 通用建表参数：utf8mb4 + InnoDB
_TABLE_ARGS = {
    "mysql_engine": "InnoDB",
    "mysql_charset": "utf8mb4",
    "mysql_collate": "utf8mb4_0900_ai_ci",
}


# =============================================================
# 一、用户与权限
# =============================================================
class SysUser(Base):
    """用户表：学生/老师/管理员账号。"""

    __tablename__ = "sys_user"
    __table_args__ = {"comment": "用户表：学生/老师/管理员账号", **_TABLE_ARGS}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="用户ID")
    username: Mapped[str] = mapped_column(String(64), unique=True, comment="登录账号(学工号/管理员名)")
    password_hash: Mapped[Optional[str]] = mapped_column(String(128), comment="密码哈希")
    real_name: Mapped[Optional[str]] = mapped_column(String(64), comment="真实姓名")
    user_type: Mapped[int] = mapped_column(SmallInteger, default=1, comment="1学生2毕业生3辅导员4老师5管理员")
    college: Mapped[Optional[str]] = mapped_column(String(128), comment="所属学院")
    email: Mapped[Optional[str]] = mapped_column(String(128), comment="邮箱")
    phone: Mapped[Optional[str]] = mapped_column(String(32), comment="手机号(展示脱敏)")
    status: Mapped[int] = mapped_column(SmallInteger, default=1, comment="1启用0禁用")
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime, comment="最后登录时间")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )

    roles: Mapped[list["SysUserRole"]] = relationship(back_populates="user")


class SysRole(Base):
    """角色表：后台权限控制(RBAC)。"""

    __tablename__ = "sys_role"
    __table_args__ = {"comment": "角色表：后台权限控制(RBAC)", **_TABLE_ARGS}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="角色ID")
    role_code: Mapped[str] = mapped_column(String(64), unique=True, comment="角色编码 admin/editor/student")
    role_name: Mapped[str] = mapped_column(String(64), comment="角色名称")
    description: Mapped[Optional[str]] = mapped_column(String(255), comment="角色描述")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment="创建时间")


class SysUserRole(Base):
    """用户角色关联表：多对多。"""

    __tablename__ = "sys_user_role"
    __table_args__ = {"comment": "用户角色关联表：多对多", **_TABLE_ARGS}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="主键")
    user_id: Mapped[int] = mapped_column(BigInteger, index=True, comment="用户ID")
    role_id: Mapped[int] = mapped_column(BigInteger, index=True, comment="角色ID")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment="创建时间")

    user: Mapped["SysUser"] = relationship(back_populates="roles", foreign_keys=[user_id], primaryjoin="SysUserRole.user_id==SysUser.id")


# =============================================================
# 二、知识库与文档
# =============================================================
class KbCategory(Base):
    """文档分类表：支持多级分类。"""

    __tablename__ = "kb_category"
    __table_args__ = {"comment": "文档分类表：支持多级分类", **_TABLE_ARGS}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="分类ID")
    parent_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True, comment="父分类ID,0为顶级")
    name: Mapped[str] = mapped_column(String(128), comment="分类名称")
    sort: Mapped[int] = mapped_column(Integer, default=0, comment="排序值,越小越靠前")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment="创建时间")


class KbDocument(Base):
    """文档主表：知识库文档及其元数据。"""

    __tablename__ = "kb_document"
    __table_args__ = {"comment": "文档主表：知识库文档及其元数据", **_TABLE_ARGS}

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

    chunks: Mapped[list["KbDocumentChunk"]] = relationship(back_populates="document", cascade="all, delete-orphan")


class KbDocumentChunk(Base):
    """文档分片表：切分后的文本块，向量存外部向量库。"""

    __tablename__ = "kb_document_chunk"
    __table_args__ = {"comment": "文档分片表：切分文本块,含关键词全文索引", **_TABLE_ARGS}

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
        back_populates="chunks", foreign_keys=[document_id], primaryjoin="KbDocumentChunk.document_id==KbDocument.id"
    )


class KbSynonym(Base):
    """同义词词典表：校内黑话/专有名词映射。"""

    __tablename__ = "kb_synonym"
    __table_args__ = {"comment": "同义词词典表：提升召回", **_TABLE_ARGS}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="主键")
    term: Mapped[str] = mapped_column(String(128), index=True, comment="标准词")
    synonyms: Mapped[str] = mapped_column(String(512), comment="同义词,逗号分隔")
    status: Mapped[int] = mapped_column(SmallInteger, default=1, comment="1启用0禁用")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment="创建时间")


class KbFaq(Base):
    """FAQ问答对表：高频问题标准答复。"""

    __tablename__ = "kb_faq"
    __table_args__ = {"comment": "FAQ问答对表", **_TABLE_ARGS}

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
    __table_args__ = {"comment": "索引任务表：文档解析/入库任务监控", **_TABLE_ARGS}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="任务ID")
    document_id: Mapped[int] = mapped_column(BigInteger, index=True, comment="关联文档ID")
    task_type: Mapped[int] = mapped_column(SmallInteger, comment="1解析2入库3重建4删除索引")
    status: Mapped[int] = mapped_column(SmallInteger, default=0, index=True, comment="0排队1执行中2成功3失败")
    progress: Mapped[int] = mapped_column(SmallInteger, default=0, comment="进度百分比0-100")
    error_msg: Mapped[Optional[str]] = mapped_column(String(1024), comment="失败原因")
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, comment="开始时间")
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, comment="结束时间")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment="创建时间")


# =============================================================
# 三、问答与会话
# =============================================================
class QaConversation(Base):
    """会话表：一次多轮对话。"""

    __tablename__ = "qa_conversation"
    __table_args__ = {"comment": "会话表：一次多轮对话", **_TABLE_ARGS}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="会话ID")
    user_id: Mapped[Optional[int]] = mapped_column(BigInteger, index=True, comment="所属用户ID(匿名可空)")
    title: Mapped[Optional[str]] = mapped_column(String(255), comment="会话标题(常取首问)")
    status: Mapped[int] = mapped_column(SmallInteger, default=1, comment="1正常0已删除")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )

    messages: Mapped[list["QaMessage"]] = relationship(back_populates="conversation", cascade="all, delete-orphan")


class QaMessage(Base):
    """消息表：对话中的每条提问/回答。"""

    __tablename__ = "qa_message"
    __table_args__ = {"comment": "消息表：每条提问/回答", **_TABLE_ARGS}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="消息ID")
    conversation_id: Mapped[int] = mapped_column(BigInteger, index=True, comment="所属会话ID")
    role: Mapped[int] = mapped_column(SmallInteger, comment="1用户提问2系统回答")
    content: Mapped[str] = mapped_column(MEDIUMTEXT, comment="消息内容")
    rewritten_query: Mapped[Optional[str]] = mapped_column(String(1024), comment="查询改写后的问题")
    answer_type: Mapped[Optional[int]] = mapped_column(SmallInteger, comment="1知识库生成2FAQ命中3无答案兜底")
    is_no_answer: Mapped[int] = mapped_column(SmallInteger, default=0, comment="是否兜底无答案1是0否")
    llm_model: Mapped[Optional[str]] = mapped_column(String(64), comment="生成所用大模型名")
    prompt_tokens: Mapped[Optional[int]] = mapped_column(Integer, comment="Prompt消耗token")
    completion_tokens: Mapped[Optional[int]] = mapped_column(Integer, comment="生成消耗token")
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, comment="响应耗时(毫秒)")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True, comment="创建时间")

    conversation: Mapped["QaConversation"] = relationship(
        back_populates="messages", foreign_keys=[conversation_id], primaryjoin="QaMessage.conversation_id==QaConversation.id"
    )
    references: Mapped[list["QaMessageReference"]] = relationship(back_populates="message", cascade="all, delete-orphan")


class QaMessageReference(Base):
    """答案引用来源表：溯源核心。"""

    __tablename__ = "qa_message_reference"
    __table_args__ = {"comment": "答案引用来源表：记录命中分片,支持溯源", **_TABLE_ARGS}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="主键")
    message_id: Mapped[int] = mapped_column(BigInteger, index=True, comment="所属回答消息ID")
    document_id: Mapped[Optional[int]] = mapped_column(BigInteger, index=True, comment="来源文档ID")
    chunk_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment="来源分片ID")
    score: Mapped[Optional[float]] = mapped_column(Numeric(6, 4), comment="检索相关度得分")
    rank_no: Mapped[Optional[int]] = mapped_column(Integer, comment="引用排序")
    snippet: Mapped[Optional[str]] = mapped_column(Text, comment="引用片段摘要")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment="创建时间")

    message: Mapped["QaMessage"] = relationship(
        back_populates="references", foreign_keys=[message_id], primaryjoin="QaMessageReference.message_id==QaMessage.id"
    )


class QaFeedback(Base):
    """答案反馈表：点赞/点踩，回流优化。"""

    __tablename__ = "qa_feedback"
    __table_args__ = {"comment": "答案反馈表：点赞/点踩", **_TABLE_ARGS}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="主键")
    message_id: Mapped[int] = mapped_column(BigInteger, index=True, comment="被评价的回答消息ID")
    user_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment="评价用户ID")
    rating: Mapped[int] = mapped_column(SmallInteger, comment="1点赞-1点踩")
    reason: Mapped[Optional[str]] = mapped_column(String(512), comment="点踩原因/补充")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment="创建时间")


# =============================================================
# 四、运营·安全·质量
# =============================================================
class OpQueryLog(Base):
    """问答日志表：全量审计与统计。"""

    __tablename__ = "op_query_log"
    __table_args__ = {"comment": "问答日志表：审计与统计", **_TABLE_ARGS}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="日志ID")
    user_id: Mapped[Optional[int]] = mapped_column(BigInteger, index=True, comment="用户ID")
    conversation_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment="会话ID")
    message_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment="消息ID")
    question: Mapped[str] = mapped_column(String(1024), comment="用户问题")
    answer_brief: Mapped[Optional[str]] = mapped_column(String(2048), comment="答案摘要")
    hit_doc_count: Mapped[Optional[int]] = mapped_column(Integer, comment="命中文档数")
    is_no_answer: Mapped[int] = mapped_column(SmallInteger, default=0, index=True, comment="是否无答案1是0否")
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, comment="总耗时(毫秒)")
    client_ip: Mapped[Optional[str]] = mapped_column(String(64), comment="客户端IP")
    channel: Mapped[Optional[str]] = mapped_column(String(32), comment="来源渠道web/h5/wecom")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True, comment="创建时间")


class OpSensitiveWord(Base):
    """敏感词表：提问内容合规过滤。"""

    __tablename__ = "op_sensitive_word"
    __table_args__ = {"comment": "敏感词表：合规过滤", **_TABLE_ARGS}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="主键")
    word: Mapped[str] = mapped_column(String(128), unique=True, comment="敏感词/违规词")
    category: Mapped[Optional[str]] = mapped_column(String(64), comment="分类")
    action: Mapped[int] = mapped_column(SmallInteger, default=1, comment="1拦截2替换3告警")
    status: Mapped[int] = mapped_column(SmallInteger, default=1, comment="1启用0禁用")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment="创建时间")


class OpEvalCase(Base):
    """评测集表：回归测试准确率/召回率。"""

    __tablename__ = "op_eval_case"
    __table_args__ = {"comment": "评测集表：质量回归", **_TABLE_ARGS}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="主键")
    question: Mapped[str] = mapped_column(String(1024), comment="评测问题")
    expected_answer: Mapped[Optional[str]] = mapped_column(Text, comment="参考标准答案")
    expected_doc_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment="期望命中文档ID")
    category: Mapped[Optional[str]] = mapped_column(String(64), comment="问题类别")
    status: Mapped[int] = mapped_column(SmallInteger, default=1, comment="1启用0禁用")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment="创建时间")


if __name__ == "__main__":
    # 调试用：打印所有表名，确认模型加载正常
    print(f"共 {len(Base.metadata.tables)} 张表：")
    for table in Base.metadata.sorted_tables:
        print(f"  - {table.name}")

    # 真正建表（按需修改连接串后取消注释）：
    # from sqlalchemy import create_engine
    # engine = create_engine(
    #     "mysql+pymysql://user:password@127.0.0.1:3306/claudecode_rag?charset=utf8mb4",
    #     echo=True,
    # )
    # Base.metadata.create_all(engine)
