# 模块速查

> 来源：从 [功能模块实现文档.md](../功能模块实现文档.md) 提取
> 用途：日常开发中快速查阅各模块的文件清单、职责、关键代码片段

---

## 1. 核心基础设施模块

**目录位置**：`backend/app/core/`

| 文件 | 状态 | 职责 |
|------|------|------|
| `config.py` | ✅ 已存在 | 环境变量配置、参数管理 |
| `database.py` | ✅ 已存在 | MySQL 连接、Session 管理 |
| `deps.py` | ✅ 已存在 | 依赖注入（获取 DB Session、获取当前用户） |
| `security.py` | ✅ 已存在 | JWT 生成/验证、密码哈希 |
| `response.py` | ✅ 已存在 | 统一响应格式 |
| `llm.py` | ✅ 已存在 | LLM 调用封装 |
| `embedding.py` | ✅ 已存在 | Embedding 生成 |
| `vectorstore.py` | ✅ 已存在 | 向量存储管理 |
| `semantic_chunker.py` | ✅ 已存在 | 语义切分 |
| `text_splitter.py` | ✅ 已存在 | 文本切分 |
| `document_parser.py` | ✅ 已存在 | 文档解析 |
| `redis_client.py` | ✅ 已存在 | Redis 懒连接 + 失败熔断降级 |
| `embedding_cache.py` | ✅ 已存在 | Embedding 三级缓存 |
| `langsmith_setup.py` | ✅ 已存在 | LangSmith 全局追踪配置 |
| `semantic_cache.py` | ✅ 已存在 | 语义缓存 |

### 关键代码片段

#### config.py — 配置类

```python
# 文件：backend/app/core/config.py
from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache

class Settings(BaseSettings):
    APP_NAME: str = "高校智慧就业服务平台"
    APP_VERSION: str = "3.0.0"
    DEBUG: bool = False
    API_PREFIX: str = "/api/v1"

    # 数据库
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = ""
    MYSQL_DATABASE: str = "aiqa"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None

    # JWT
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # LLM
    DASHSCOPE_API_KEY: str = ""
    LLM_MODEL: str = "qwen-max"
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 2000

    # Embedding
    EMBEDDING_MODEL: str = "text-embedding-v2"
    EMBEDDING_DIMENSION: int = 1024

    # 向量库
    CHROMADB_HOST: str = "localhost"
    CHROMADB_PORT: int = 8000
    CHROMADB_COLLECTION: str = "knowledge_base"

    # LangSmith
    LANGCHAIN_TRACING_V2: bool = True
    LANGCHAIN_API_KEY: str = ""
    LANGCHAIN_PROJECT: str = "aiqa-agent"
    LANGCHAIN_ENDPOINT: str = "https://api.smith.langchain.com"

    # Agent
    AGENT_MAX_ITERATIONS: int = 10
    AGENT_TIMEOUT_SECONDS: int = 60

    # 检索
    RETRIEVAL_TOP_K: int = 10
    RETRIEVAL_FINAL_K: int = 5
    SIMILARITY_THRESHOLD: float = 0.7

    # 幻觉防御
    HIGH_RISK_THRESHOLD: float = 0.80
    MEDIUM_RISK_THRESHOLD: float = 0.65
    LOW_RISK_THRESHOLD: float = 0.40

    # 时效性
    KB_WARNING_DAYS: int = 30
    KB_FRESHNESS_HALF_LIFE: int = 180

    # 成本控制
    DAILY_COST_THRESHOLD_USD: float = 10.0
    MONTHLY_COST_THRESHOLD_USD: float = 300.0

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
```

#### database.py — 数据库连接

```python
# 文件：backend/app/core/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from contextlib import contextmanager
from typing import Generator

from app.core.config import get_settings

settings = get_settings()
DATABASE_URL = f"mysql+pymysql://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}?charset=utf8mb4"

engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    echo=settings.DEBUG
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """获取数据库 Session（依赖注入）"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

#### security.py — 安全认证

```python
# 文件：backend/app/core/security.py
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from passlib.context import CryptContext

from app.core.config import get_settings

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None

def create_access_token(user_id: int, role: str) -> str:
    return create_token(data={"sub": str(user_id), "role": role})
```

---

## 2. LLM 与向量处理模块

**目录位置**：`backend/app/core/`

| 文件 | 状态 | 职责 |
|------|------|------|
| `llm.py` | ✅ 已存在 | LLM 调用封装（通义千问） |
| `embedding.py` | ✅ 已存在 | Embedding 生成 |
| `vectorstore.py` | ✅ 已存在 | 向量存储管理（ChromaDB） |
| `semantic_chunker.py` | ✅ 已存在 | 语义切分 |
| `text_splitter.py` | ✅ 已存在 | 文本切分 |
| `document_parser.py` | ✅ 已存在 | 文档解析 |

### 关键代码片段

#### llm.py — LLM 调用

```python
# 文件：backend/app/core/llm.py
import httpx
from typing import Optional, List, Dict, Any, AsyncGenerator
from dataclasses import dataclass
import json
import time

from app.core.config import get_settings
from app.core.langsmith_tracker import track_llm_call

settings = get_settings()

@dataclass
class LLMResponse:
    content: str
    model: str
    tokens_in: int
    tokens_out: int
    latency_ms: int
    finish_reason: str


class LLMClient:
    """通义千问 LLM 客户端"""
    API_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"

    def __init__(self):
        self.api_key = settings.DASHSCOPE_API_KEY
        self.model = settings.LLM_MODEL
        self.fallback_model = "qwen-plus"
        self.temperature = settings.LLM_TEMPERATURE
        self.max_tokens = settings.LLM_MAX_TOKENS

    def chat(self, prompt: str, system_prompt: Optional[str] = None,
             temperature: Optional[float] = None, max_tokens: Optional[int] = None) -> LLMResponse:
        # 同步调用实现...
        pass

    async def chat_async(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        # 异步调用实现...
        pass

    async def chat_stream(self, prompt: str) -> AsyncGenerator[str, None]:
        # 流式输出实现...
        pass
```

#### vectorstore.py — 向量存储

```python
# 文件：backend/app/core/vectorstore.py
import chromadb
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from app.core.config import get_settings
from app.core.embedding import embedding_client

settings = get_settings()

@dataclass
class SearchResult:
    chunk_id: str
    text: str
    score: float
    metadata: Dict[str, Any]


class VectorStore:
    """向量存储管理"""
    def __init__(self):
        self.client = chromadb.HttpClient(
            host=settings.CHROMADB_HOST,
            port=settings.CHROMADB_PORT
        )
        self.collection = self.client.get_or_create_collection(
            name=settings.CHROMADB_COLLECTION,
            metadata={"hnsw:space": "cosine"}
        )

    def add_documents(self, chunks: List[Dict[str, Any]]) -> List[str]:
        texts = [c["text"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]
        embeddings = embedding_client.get_embeddings_batch(texts)
        ids = [f"chunk_{i}_{hash(t)[:8]}" for i, t in enumerate(texts)]
        self.collection.add(documents=texts, embeddings=embeddings, metadatas=metadatas, ids=ids)
        return ids

    def search(self, query: str, top_k: int = 10, where: Optional[Dict] = None) -> List[SearchResult]:
        # 向量检索实现...
        pass
```

---

## 3. Agent 智能体模块

**目录位置**：`backend/app/agent/`

| 文件 | 状态 | 职责 |
|------|------|------|
| `__init__.py` | 新增 | 模块初始化 |
| `state.py` | 新增 | Agent 状态定义（TypedDict） |
| `nodes.py` | 新增 | Agent 节点实现 |
| `graph.py` | 新增 | LangGraph 工作流构建 |
| `tools.py` | 新增 | Agent 工具集 |
| `hallucination_defense.py` | 新增 | 幻觉防御系统 |
| `citation_tracker.py` | 新增 | 引用追踪器 |
| `temporal_retriever.py` | 新增 | 时效感知检索 |
| `refusal_handler.py` | 新增 | 拒答处理 |
| `prompts/` | 新增 | Prompt 文件（router / generator / refusal / regenerator / moderation） |

### 关键代码片段

#### state.py — Agent 状态

```python
# 文件：backend/app/agent/state.py
from typing import Annotated, TypedDict, List, Dict, Any, Optional
from langgraph.graph.message import add_messages
from datetime import datetime


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    current_query: str
    search_results: List[Dict[str, Any]]
    citations: List[Dict[str, Any]]
    confidence: float
    query_risk_level: str
    tools_used: List[str]
    tool_outputs: Dict[str, Any]
    response: str
    route: str
    should_refuse: bool
    refusal_reason: str
    consistency_issues: List[Dict[str, Any]]
    fact_issues: List[Dict[str, Any]]
    version_info: Dict[str, Any]
    temporal_warnings: List[str]
    conversation_id: int
    user_id: int
    created_at: datetime
    # 死循环防护
    retry_attempt: int
    tool_call_count: int
    last_search_query: str
    regenerate_count: int
    forced_exit: bool
    is_low_confidence: bool
    skipped_consistency_check: bool


class CitationInfo(TypedDict):
    ref_id: str
    chunk_id: str
    doc_title: str
    text: str
    page_num: Optional[int]
    score: float
    valid_until: Optional[str]
    support_type: str
    support_confidence: float


class ConsistencyIssue(TypedDict):
    current_query: str
    previous_query: str
    current_answer: str
    previous_answer: str
    contradiction_type: str
    severity: str
```

---

## 4. 知识库管理模块

**目录位置**：`backend/app/services/` + `backend/app/routers/`

| 文件 | 状态 | 职责 |
|------|------|------|
| `services/knowledge_service.py` | ✅ 已存在 | 文档管理服务 |
| `services/index_service.py` | ✅ 已存在 | 索引构建服务 |
| `routers/documents.py` | ✅ 已存在 | 文档 API 路由 |
| `routers/faqs.py` | ✅ 已存在 | FAQ API 路由 |
| `routers/categories.py` | ✅ 已存在 | 分类 API 路由 |

### 关键代码片段

#### knowledge_service.py — 文档管理

```python
# 文件：backend/app/services/knowledge_service.py
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.models.knowledge import KbDocument, KbChunk
from app.core.semantic_chunker import semantic_chunker
from app.core.vectorstore import vector_store
from app.core.document_parser import DocumentParser


class KnowledgeService:
    """知识库管理服务"""
    def __init__(self, db: Session):
        self.db = db
        self.parser = DocumentParser()

    async def upload_document(self, file_path: str, title: str, category: str,
                              source: str, valid_from: Optional[datetime] = None,
                              valid_until: Optional[datetime] = None, user_id: int = None) -> KbDocument:
        # 1. 解析文档
        content = self.parser.parse(file_path)
        # 2. 计算文件哈希
        file_hash = self._calculate_hash(file_path)
        # 3. 创建文档记录
        document = KbDocument(title=title, category=category, source=source,
                              file_path=file_path, file_hash=file_hash,
                              valid_from=valid_from, valid_until=valid_until,
                              is_current=1, upload_by=user_id, status=1)
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        # 4. 语义切分
        chunks = semantic_chunker.chunk(content, metadata={"document_id": document.id, ...})
        # 5. 存储 chunk 到 MySQL
        chunk_records = [KbChunk(document_id=document.id, content=c["text"], chunk_index=i) for i, c in enumerate(chunks)]
        self.db.add_all(chunk_records)
        self.db.commit()
        # 6. 索引到向量库
        chunk_ids = vector_store.add_documents(chunks)
        # 7. 更新 chunk 的 vector_id
        for i, cr in enumerate(chunk_records):
            cr.vector_id = chunk_ids[i]
        self.db.commit()
        document.chunk_count = len(chunks)
        self.db.commit()
        return document
```

---

## 5. 问答服务模块

**目录位置**：`backend/app/services/` + `backend/app/routers/`

| 文件 | 状态 | 职责 |
|------|------|------|
| `services/qa_service.py` | ✅ 已存在 | 问答服务（已升级集成 Agent） |
| `services/rag_service.py` | ✅ 已存在 | RAG 检索服务 |
| `routers/qa.py` | ✅ 已存在 | 问答 API 路由（含 `/ask/agent`） |
| `routers/conversations.py` | ✅ 已存在 | 会话 API 路由 |
| `routers/messages.py` | ✅ 已存在 | 消息 API 路由 |

### 关键代码片段

#### qa_service.py — Agent 问答入口

```python
# 文件：backend/app/services/qa_service.py
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.models.qa import QaConversation, QaMessage, QaMessageReference
from app.agent.graph import agent_graph
from app.core.response import success_response, error_response


class QAService:
    """问答服务"""
    def __init__(self, db: Session):
        self.db = db
        self.agent = agent_graph

    async def agent_chat(self, db, user_id, query, conversation_id, client_ip) -> Dict[str, Any]:
        # 1. 创建/获取会话
        conversation = resolve_conversation(db, user_id, conversation_id, query)
        # 2. 执行 Agent 工作流
        result = await self.agent.compile().invoke({...})
        # 3. 保存用户消息 + AI 回答
        # 4. 保存引用
        # 5. 记录查询日志
        # 6. 返回 enriched result
        return {
            "conversation_id": conversation.id,
            "message_id": ai_message.id,
            "response": result["response"],
            "citations": result["citations"],
            "confidence": result["confidence"],
            "route": result["route"],
            "query_risk_level": result["query_risk_level"],
            "is_low_confidence": result["is_low_confidence"],
            "consistency_issues": result["consistency_issues"],
            "fact_issues": result["fact_issues"],
            "temporal_warnings": result["temporal_warnings"],
            "warnings": result["warnings"],
        }
```

---

## 6. 用户管理模块

**目录位置**：`backend/app/services/` + `backend/app/routers/`

| 文件 | 状态 | 职责 |
|------|------|------|
| `services/user_service.py` | ✅ 已存在 | 用户服务 |
| `routers/users.py` | ✅ 已存在 | 用户 API 路由 |
| `routers/auth.py` | ✅ 已存在 | 认证 API 路由 |
| `routers/roles.py` | ✅ 已存在 | 角色 API 路由 |
| `models/user.py` | ✅ 已存在 | 用户数据模型 |

---

## 7. 运维管理模块

**目录位置**：`backend/app/services/` + `backend/app/routers/`

| 文件 | 状态 | 职责 |
|------|------|------|
| `services/ops_service.py` | ✅ 已存在 | 运维服务 |
| `routers/sensitive_words.py` | ✅ 已存在 | 敏感词路由 |
| `routers/query_logs.py` | ✅ 已存在 | 查询日志路由 |
| `routers/stats.py` | ✅ 已存在 | 统计路由 |
| `routers/feedback.py` | ✅ 已存在 | 反馈路由 |

---

## 8. 监控告警模块

**目录位置**：`backend/app/monitor/`

| 文件 | 状态 | 职责 |
|------|------|------|
| `__init__.py` | 新增 | 模块初始化 |
| `health_monitor.py` | 新增 | 知识库健康监控 |
| `cost_monitor.py` | 新增 | LLM 成本监控 |
| `langsmith_tracker.py` | 新增 | LangSmith 追踪 |
| `citation_evaluator.py` | 新增 | 引用质量评估 |
| `consistency_checker.py` | 新增 | 一致性检查 |

### 关键代码片段

#### health_monitor.py — 知识库健康监控

```python
# 文件：backend/app/monitor/health_monitor.py
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Dict, Any

from app.models.knowledge import KbDocument
from app.models.monitor import KbHealthLog


class HealthMonitor:
    """知识库健康监控"""
    CONFIG = {
        "warning_days": 30,
        "freshness_half_life": 180,
        "min_health_score": 60
    }

    def __init__(self, db: Session):
        self.db = db

    async def run_daily_check(self) -> Dict[str, Any]:
        today = datetime.now()
        warning_docs = self._check_upcoming_expiry(today)
        expired_docs = self._check_expired_docs(today)
        health_score = self._calculate_health_score(today)
        report = {
            "check_date": today.strftime("%Y-%m-%d"),
            "health_score": health_score,
            "warning_count": len(warning_docs),
            "expired_count": len(expired_docs),
            "warning_docs": warning_docs,
            "expired_docs": expired_docs
        }
        log = KbHealthLog(check_date=today, total_docs=self._get_total_docs(),
                          current_docs=self._get_current_docs(),
                          warning_docs=len(warning_docs), expired_docs=len(expired_docs),
                          health_score=health_score)
        self.db.add(log)
        self.db.commit()
        return report

    def _check_upcoming_expiry(self, today: datetime) -> List[Dict]:
        warning_date = today + timedelta(days=self.CONFIG["warning_days"])
        docs = self.db.query(KbDocument).filter(
            KbDocument.valid_until.between(today, warning_date),
            KbDocument.is_current == 1, KbDocument.status == 1
        ).all()
        return [{"id": d.id, "title": d.title, "valid_until": d.valid_until.strftime("%Y-%m-%d"),
                 "days_until_expiry": (d.valid_until - today).days} for d in docs]
```

---

## 9. 数据模型模块

**目录位置**：`backend/app/models/`

| 文件 | 状态 | 职责 |
|------|------|------|
| `user.py` | ✅ 已存在 | 用户模型 |
| `knowledge.py` | ✅ 已存在 | 知识库模型 |
| `qa.py` | ✅ 已存在 | 问答模型 |
| `ops.py` | ✅ 已存在 | 运维模型 |
| `monitor.py` | 新增 | 监控模型（6 张表） |

### 监控模型（monitor.py）

| 模型 | 对应表 | 用途 |
|------|--------|------|
| `KbHealthLog` | `kb_health_log` | 知识库健康度日志（每日一条） |
| `LlmCostLog` | `llm_cost_log` | LLM 成本日志（按天 + 模型聚合） |
| `AgentRefusalLog` | `agent_refusal_log` | 拒答记录 |
| `CitationQualityLog` | `citation_quality_log` | 引用质量日志 |
| `ConsistencyIssueLog` | `consistency_issue_log` | 一致性问题日志 |
| `FactVerificationLog` | `fact_verification_log` | 事实核验日志 |

---

## 模块间依赖关系

```
                    ┌─────────────┐
                    │ 核心基础设施 │
                    │   (core)    │
                    └──────┬──────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
           ▼               ▼               ▼
    ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
    │ LLM与向量   │ │ 用户管理    │ │ 数据模型    │
    │  (core)    │ │ (services)  │ │  (models)   │
    └──────┬──────┘ └──────┬──────┘ └──────┬──────┘
           │               │               │
           │               │               │
           ▼               │               │
    ┌─────────────┐        │               │
    │ Agent智能体 │        │               │
    │  (agent)   │◄───────┼───────────────┘
    └──────┬──────┘        │
           │               │
           ▼               │
    ┌─────────────┐        │
    │ 知识库管理  │◄───────┘
    │ (services) │
    └──────┬──────┘
           │
           ▼
    ┌─────────────┐
    │ 问答服务    │
    │ (services) │
    └──────┬──────┘
           │
           ▼
    ┌─────────────┐
    │ 运维管理    │
    │ (services) │
    └──────┬──────┘
           │
           ▼
    ┌─────────────┐
    │ 监控告警    │
    │ (monitor)  │
    └─────────────┘
```
