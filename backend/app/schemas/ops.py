"""运营·安全·质量模块 schema（对应 op_* 表）。

枚举约定：
  action:       1拦截 2替换 3告警（敏感词）
  is_no_answer: 1是 0否
  status:       1启用 0禁用
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


# ---------------- 问答日志 ----------------
class QueryLogRead(ORMModel):
    id: int
    user_id: Optional[int]
    conversation_id: Optional[int]
    message_id: Optional[int]
    question: str
    answer_brief: Optional[str]
    hit_doc_count: Optional[int]
    is_no_answer: int
    latency_ms: Optional[int]
    client_ip: Optional[str]
    channel: Optional[str]
    created_at: datetime


# ---------------- 敏感词 ----------------
class SensitiveWordBase(BaseModel):
    word: str = Field(max_length=128, description="敏感词/违规词")
    category: Optional[str] = Field(default=None, max_length=64, description="分类")
    action: int = Field(default=1, description="1拦截2替换3告警")
    status: int = Field(default=1, description="1启用0禁用")


class SensitiveWordCreate(SensitiveWordBase):
    pass


class SensitiveWordUpdate(BaseModel):
    word: Optional[str] = Field(default=None, max_length=128)
    category: Optional[str] = Field(default=None, max_length=64)
    action: Optional[int] = None
    status: Optional[int] = None


class SensitiveWordRead(ORMModel):
    id: int
    word: str
    category: Optional[str]
    action: int
    status: int
    created_at: datetime


# ---------------- 评测集 ----------------
class EvalCaseBase(BaseModel):
    question: str = Field(max_length=1024, description="评测问题")
    expected_answer: Optional[str] = Field(default=None, description="参考标准答案")
    expected_doc_id: Optional[int] = Field(default=None, description="期望命中文档ID")
    category: Optional[str] = Field(default=None, max_length=64, description="问题类别")
    status: int = Field(default=1, description="1启用0禁用")


class EvalCaseCreate(EvalCaseBase):
    pass


class EvalCaseUpdate(BaseModel):
    question: Optional[str] = Field(default=None, max_length=1024)
    expected_answer: Optional[str] = None
    expected_doc_id: Optional[int] = None
    category: Optional[str] = Field(default=None, max_length=64)
    status: Optional[int] = None


class EvalCaseRead(ORMModel):
    id: int
    question: str
    expected_answer: Optional[str]
    expected_doc_id: Optional[int]
    category: Optional[str]
    status: int
    created_at: datetime


# ---------------- 评测执行 ----------------
class EvalRunRequest(BaseModel):
    top_k: int = Field(default=5, ge=1, le=50, description="检索Top-K")
    category: Optional[str] = Field(default=None, description="仅评测某类别，为空则全部")
    limit: Optional[int] = Field(default=None, ge=1, le=500, description="最多评测条数")


class EvalCaseResult(BaseModel):
    case_id: int
    question: str
    expected_doc_id: Optional[int]
    hit: bool = Field(description="期望文档是否出现在检索命中中")
    hit_rank: Optional[int] = Field(default=None, description="命中排名(从1开始)，未命中为None")
    top_doc_ids: list[int] = Field(default_factory=list, description="检索命中的文档ID列表")
    top_score: Optional[float] = Field(default=None, description="最高相似度")


class EvalRunResult(BaseModel):
    total: int = Field(description="参与评测的用例数(含已跳过)")
    evaluated: int = Field(description="实际计入指标的用例数(有expected_doc_id)")
    skipped: int = Field(description="跳过数(无expected_doc_id)")
    hit_count: int = Field(description="命中数")
    hit_rate: float = Field(description="命中率 = hit_count/evaluated")
    details: list[EvalCaseResult] = Field(default_factory=list)


# ---------------- 无答案问题 ----------------
class UnansweredRead(ORMModel):
    id: int
    question: str
    ask_count: int
    last_user_id: Optional[int]
    status: int  # 1未解决 2已解决
    resolve_note: Optional[str]
    first_asked_at: datetime
    last_asked_at: datetime


class UnansweredResolve(BaseModel):
    status: int = Field(description="1未解决 2已解决")
    resolve_note: Optional[str] = Field(default=None, max_length=512, description="处理说明")


# ---------------- 统计看板 ----------------
class StatsOverview(BaseModel):
    total_questions: int = Field(description="累计问答数")
    no_answer_rate: float = Field(description="无答案率")
    like_rate: float = Field(description="点赞率")
    total_documents: int = Field(description="文档总数")
    indexed_documents: int = Field(description="已索引文档数")
