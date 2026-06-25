# RAG + Agent 项目工程化框架

> 基于「高校智慧就业服务平台」真实开发过程抽象出的可复用工程框架
> 适用：以 FastAPI + LangGraph + 向量数据库 为核心的 AI 应用项目
> 版本：v1.0

---

## 一、项目全生命周期

```
需求分析 → 技术选型 → 架构设计 → 环境准备 → 核心开发 → 功能集成 → 测试部署 → 运营迭代
   │          │          │          │          │          │          │          │
   1.0       2.0       3.0       4.0       5.0       6.0       7.0       8.0
```

| 阶段 | 名称 | 核心产出 | 验收标准 |
|------|------|----------|----------|
| 1.0 | 需求分析 | PRD、功能清单、用户故事 | 需求确认签字 / 产品文档锁定 |
| 2.0 | 技术选型 | 技术栈文档、依赖清单、架构决策记录（ADR） | 架构师评审通过 |
| 3.0 | 架构设计 | 模块划分、分层图、接口定义、数据模型 | 技术方案评审通过 |
| 4.0 | 环境准备 | Docker Compose、数据库迁移、CI/CD 流水线 | `docker compose up` 一键启动 |
| 5.0 | 核心开发 | 基础设施层（config / db / security / core） | 单元测试覆盖率 ≥ 80% |
| 6.0 | 功能集成 | 业务服务 + Agent 工作流 + 监控 | 端到端流程跑通 |
| 7.0 | 测试部署 | 集成测试、灰度方案、生产镜像 | 测试报告 + 部署文档 |
| 8.0 | 运营迭代 | 监控看板、告警规则、文档 | 可观测性闭环 |

---

## 二、需求分析阶段

### 2.1 需求拆解模板

```
功能需求
├── 核心功能（MVP 必须有）
│   ├── 用户认证（注册/登录/权限）
│   ├── 知识库管理（上传/检索/管理）
│   └── 智能问答（RAG + Agent）
├── 增强功能（V1 应该有）
│   ├── 会话管理（多轮对话）
│   ├── 引用溯源（可验证的回答）
│   └── 监控告警（健康度/成本）
└── 规划功能（V2 可以考虑）
    ├── 多模态支持（图片/PDF）
    ├── 多租户隔离
    └── A/B 实验框架

非功能需求
├── 性能：接口响应 < 3s，并发 100 QPS
├── 可用性：服务可用性 99.5%
├── 安全性：JWT 认证、输入校验、SQL 防注入
└── 可观测性：日志、链路追踪、指标采集
```

### 2.2 需求 → 模块映射

| 需求 | 对应模块 | 优先级 |
|------|----------|--------|
| 用户登录/注册 | user | P0 |
| 知识库上传/管理 | knowledge | P0 |
| 智能问答 | qa + rag + agent | P0 |
| 会话历史 | qa | P1 |
| 引用溯源 | agent/citation_tracker | P1 |
| 幻觉防护 | agent/hallucination_defense | P1 |
| 监控告警 | monitor | P2 |
| 敏感词过滤 | ops | P2 |

---

## 三、技术选型决策

### 3.1 技术栈模板

| 层级 | 技术选型 | 选型依据 | 替代方案 |
|------|----------|----------|----------|
| **Web 框架** | FastAPI | 异步原生、自动文档、依赖注入 | Django REST、Flask |
| **Agent 框架** | LangGraph | 状态机 DAG、checkpoint、条件边 | 自研状态机、LlamaIndex |
| **LLM** | 通义千问（DashScope） | 国内合规、OpenAI 兼容 API | GPT-4、Claude、文心一言 |
| **向量数据库** | ChromaDB | 嵌入式、零运维、持久化 | Pinecone、Weaviate、Milvus |
| **关系数据库** | MySQL 8.x | 成熟稳定、事务支持 | PostgreSQL |
| **缓存** | Redis（可选） | 向量缓存、语义缓存 | Memcached |
| **监控追踪** | LangSmith | LangChain 生态原生支持 | Phoenix、Arize、自研 |
| **任务调度** | APScheduler | Python 原生、轻量 | Celery、Airflow |
| **迁移工具** | Alembic | SQLAlchemy 官方、版本管理 | Flyway、Liquibase |
| **前端** | Vue 3 + TypeScript | 与后端技术栈匹配 | React、Angular |

### 3.2 架构决策记录（ADR）模板

```markdown
## ADR-00X: [决策标题]

**状态**: 已采纳 / 待定 / 已废弃
**日期**: YYYY-MM-DD
**决策者**: [负责人]

### 背景
[为什么需要做这个决策？当前面临什么问题？]

### 方案
| 方案 | 优点 | 缺点 | 风险 |
|------|------|------|------|
| A    | ...  | ...  | ...  |
| B    | ...  | ...  | ...  |

### 决策
选择了方案 A，原因：
1. [理由 1]
2. [理由 2]

### 后果
- 正面：[带来了什么好处]
- 负面：[有什么 trade-off]
- 后续：[需要跟进什么]
```

---

## 四、架构设计阶段

### 4.1 分层架构（标准模板）

```
┌─────────────────────────────────────────────────────────────┐
│  routers/            ← HTTP 接入层                            │
│  ├── 路由定义、参数校验、权限控制、响应格式化                    │
├─────────────────────────────────────────────────────────────┤
│  services/           ← 业务逻辑层                            │
│  ├── 事务边界、业务流程编排、跨模块调用                         │
├─────────────────────────────────────────────────────────────┤
│  agent/              ← AI 工作流层                            │
│  ├── LangGraph StateGraph、节点、工具、Prompt 模板              │
├─────────────────────────────────────────────────────────────┤
│  core/               ← 基础设施层                             │
│  ├── 配置、数据库、LLM、Embedding、向量库、缓存、安全            │
├─────────────────────────────────────────────────────────────┤
│  models/             ← 数据持久层                              │
│  ├── SQLAlchemy ORM、表关系、索引                              │
├─────────────────────────────────────────────────────────────┤
│  schemas/            ← 数据传输层                              │
│  ├── Pydantic DTOs、请求/响应模型                              │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 分层约束规则

| 层 | 允许依赖 | 禁止依赖 | 职责边界 |
|----|----------|----------|----------|
| routers | services, schemas, deps | models, core | 只做参数校验、权限、调用 service |
| services | agent, core, models, schemas | routers | 业务逻辑、事务管理 |
| agent | core, prompts | routers, models | 工作流编排、节点逻辑 |
| core | config（无环） | routers, services, agent | 纯基础设施，无业务逻辑 |
| models | core（仅 Base） | services, routers | 纯 ORM，无业务方法 |
| schemas | （无依赖） | 其他所有层 | 纯 DTO，无业务逻辑 |

### 4.3 模块划分模板

```
backend/app/
├── __init__.py              # 模块初始化
├── main.py                  # FastAPI 应用入口
│
├── routers/                 # 按业务域拆分路由
│   ├── __init__.py
│   ├── health.py            # 健康检查
│   ├── auth.py              # 认证相关
│   ├── users.py             # 用户管理
│   ├── knowledge.py         # 知识库管理
│   ├── qa.py                # 问答接口
│   ├── agent.py             # Agent 接口
│   └── monitor.py           # 监控接口
│
├── services/                # 按业务域拆分服务
│   ├── user_service.py
│   ├── knowledge_service.py
│   ├── qa_service.py
│   ├── rag_service.py       # RAG 核心检索
│   ├── agent_service.py     # Agent 编排
│   └── ops_service.py
│
├── agent/                   # LangGraph Agent（可选模块）
│   ├── __init__.py
│   ├── state.py             # AgentState
│   ├── graph.py             # StateGraph 构建
│   ├── nodes.py             # 节点实现
│   ├── tools.py             # 工具注册
│   ├── hallucination_defense.py
│   ├── citation_tracker.py
│   ├── temporal_retriever.py
│   ├── refusal_handler.py
│   └── prompts/             # Prompt 模板
│       ├── router.py
│       ├── generator.py
│       └── refusal.py
│
├── core/                    # 基础设施（框架无关）
│   ├── config.py            # 配置管理
│   ├── database.py          # 数据库连接
│   ├── llm.py               # LLM 客户端
│   ├── embedding.py         # Embedding 客户端
│   ├── vectorstore.py       # 向量存储
│   ├── redis_client.py      # Redis 客户端
│   ├── security.py          # 密码/JWT
│   ├── deps.py              # 依赖注入
│   ├── response.py          # 统一响应
│   └── logging_config.py    # 日志配置
│
├── models/                  # 数据模型
│   ├── base.py              # 基类
│   ├── user.py
│   ├── knowledge.py
│   ├── qa.py
│   ├── ops.py
│   └── monitor.py
│
├── schemas/                 # DTOs
│   ├── user.py
│   ├── knowledge.py
│   ├── qa.py
│   └── common.py            # 公共模型
│
├── monitor/                 # 监控模块（可选）
│   ├── scheduler.py
│   ├── health_monitor.py
│   ├── cost_monitor.py
│   └── citation_evaluator.py
│
└── tests/                   # 测试
    ├── test_services/
    ├── test_agent/
    └── test_integration/
```

---

## 五、环境准备阶段

### 5.1 检查清单

```
□ 依赖管理
  □ requirements.txt 锁定核心依赖版本
  □ 区分核心依赖 / 开发依赖 / 测试依赖
  □ 关键依赖有降级方案（如 Redis 不可用时）

□ 数据库
  □ 选择迁移工具（Alembic / Flyway）
  □ 基线迁移（stamp 现有表）
  □ 版本化迁移脚本
  □ 回滚脚本验证

□ 配置管理
  □ .env.example 模板
  □ 敏感信息不进 Git
  □ 环境区分（dev / test / prod）
  □ 启动时校验关键配置

□ 容器化
  □ Dockerfile 多阶段构建
  □ docker-compose.yml 一键启动
  □ 数据卷持久化（data / uploads / chroma_data）
  □ 健康检查端点

□ 可观测性
  □ 日志格式统一（开发 console / 生产 JSON）
  □ 链路追踪配置（LangSmith / OpenTelemetry）
  □ 指标采集端点
```

### 5.2 Docker Compose 模板

```yaml
services:
  db:
    image: mysql:8.4
    environment:
      MYSQL_ROOT_PASSWORD: ${DB_ROOT_PASSWORD}
      MYSQL_DATABASE: ${DB_NAME}
    volumes:
      - db_data:/var/lib/mysql
    healthcheck:
      test: ["CMD", "mysqladmin", "ping"]
      interval: 5s
      timeout: 3s

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru

  api:
    build: ./backend
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - DASHSCOPE_API_KEY=${DASHSCOPE_API_KEY}
      - AGENT_ENABLED=${AGENT_ENABLED:-false}
    volumes:
      - ./backend/data:/app/data
      - ./backend/uploads:/app/uploads
      - ./backend/chroma_data:/app/chroma_data
    ports:
      - "8000:8000"

volumes:
  db_data:
  redis_data:
```

---

## 六、核心开发阶段

### 6.1 开发顺序（依赖优先）

```
阶段 1：基础设施（不可跳过）
├── config.py         # 配置管理（所有模块依赖）
├── database.py       # 数据库连接（所有模块依赖）
├── security.py       # 安全认证（用户模块依赖）
├── deps.py           # 依赖注入（路由层依赖）
└── response.py       # 统一响应（路由层依赖）

阶段 2：数据层
├── models/           # ORM 模型
├── schemas/          # DTOs
└── 数据库迁移        # Alembic 版本脚本

阶段 3：核心服务
├── llm.py            # LLM 客户端
├── embedding.py      # Embedding 客户端
├── vectorstore.py    # 向量存储
├── redis_client.py   # Redis 客户端
└── rag_service.py    # RAG 核心检索

阶段 4：业务服务
├── user_service.py
├── knowledge_service.py
├── qa_service.py
└── ops_service.py

阶段 5：Agent 工作流（可选）
├── agent/state.py
├── agent/prompts/
├── agent/nodes.py
├── agent/tools.py
├── agent/graph.py
└── agent/hallucination_defense.py

阶段 6：接入层
├── routers/          # 按模块逐个实现
└── main.py           # 注册路由、中间件
```

### 6.2 配置管理模板

```python
# core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # === 应用基础 ===
    APP_NAME: str = "My App"
    APP_ENV: str = "development"  # development / staging / production
    DEBUG: bool = True
    API_PREFIX: str = "/api/v1"

    # === 数据库 ===
    DATABASE_URL: Optional[str] = None

    @property
    def db_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # === 安全 ===
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # === LLM ===
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    LLM_MODEL: str = "qwen-turbo"
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 2000

    # === 向量 ===
    EMBEDDING_MODEL: str = "text-embedding-v3"
    EMBEDDING_DIMENSION: int = 1024
    CHROMA_PERSIST_DIR: str = "./chroma_data"

    # === Agent（可选）===
    AGENT_ENABLED: bool = False
    AGENT_MAX_ITERATIONS: int = 10
    AGENT_TIMEOUT_SECONDS: int = 60
    AGENT_RECURSION_LIMIT: int = 15

    # === 缓存（可选）===
    REDIS_URL: Optional[str] = None
    REDIS_ENABLED: bool = False

    # === 监控 ===
    LANGSMITH_API_KEY: str = ""
    LANGSMITH_PROJECT: str = "myproject"
    LANGSMITH_TRACING: bool = False

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

### 6.3 统一响应模板

```python
# core/response.py
from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

class ApiResponse(BaseModel, Generic[T]):
    code: int = 200
    message: str = "success"
    data: Optional[T] = None

def success(data: Any = None, message: str = "success") -> dict:
    return {"code": 200, "message": message, "data": data}

def error(code: int, message: str, data: Any = None) -> dict:
    return {"code": code, "message": message, "data": data}

# 全局异常处理
async def global_exception_handler(request: Request, exc: Exception):
    # 5xx 不暴露详情，4xx 暴露用户错误
    if isinstance(exc, HTTPException):
        return JSONResponse(status_code=exc.status_code, content=error(exc.status_code, exc.detail))
    return JSONResponse(status_code=500, content=error(500, "服务器内部错误"))
```

---

## 七、Agent 工作流集成（可选模块）

### 7.1 LangGraph 标准模式

```python
# agent/state.py
from typing import Annotated, TypedDict, List, Dict, Any, Optional
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    current_query: str
    search_results: List[Dict]
    citations: List[Dict]
    confidence: float
    route: str
    response: str
    # 死循环防护
    retry_attempt: int
    tool_call_count: int
    regenerate_count: int
    forced_exit: bool
```

```python
# agent/graph.py
from langgraph.graph import StateGraph, END

def build_agent_graph(state_cls, nodes: dict, edges: dict) -> CompiledGraph:
    """标准 LangGraph 构建流程"""
    g = StateGraph(state_cls)

    # 1. 注册节点
    for name, fn in nodes.items():
        g.add_node(name, fn)

    # 2. 设置入口
    g.set_entry_point("route")

    # 3. 添加条件边
    for src, (condition, targets) in edges.items():
        g.add_conditional_edges(src, condition, targets)

    # 4. 设置出口
    g.add_edge("accept", END)
    g.add_edge("refuse", END)

    return g.compile(checkpointer=checkpointer)
```

### 7.2 死循环防护清单

| 防护类型 | 机制 | 触发条件 | 兜底行为 |
|----------|------|----------|----------|
| 工具选择循环 | tool_call_count 计数 | ≥ 3 次工具调用 | 强制生成回答 |
| 检索去重 | last_search_query 比对 | 相同查询 + retry==0 | 跳过检索直接生成 |
| 条件判断循环 | 动态阈值衰减 | 每次重试降 0.15 | 保底 0.30，仍不通过则拒答 |
| 结果验证循环 | regenerate_count 计数 | ≥ 2 次重生成 | accept_with_warning |
| 递归深度 | LangGraph recursion_limit | 达到上限 | 抛出 RecursionError |
| 超时 | asyncio.wait_for | 超过 60s | 取消任务，返回超时错误 |

### 7.3 Agent 渐进接入模式

```python
# routers/qa.py
if settings.AGENT_ENABLED:
    result = await agent_graph.ainvoke(state)
else:
    result = await rag_service.ask(query)  # 降级到传统 RAG
```

---

## 八、监控与可观测性

### 8.1 监控模块结构

```
monitor/
├── scheduler.py           # APScheduler 定时任务
│   ├── kb_health_check    # 每日 02:00
│   ├── citation_quality   # 每日 02:15
│   ├── llm_cost_check     # 每日 02:30
│   └── consistency_check  # 每日 02:45
├── health_monitor.py      # 知识库健康度
├── cost_monitor.py        # LLM 成本监控
└── citation_evaluator.py  # 引用质量评估
```

### 8.2 日志规范

| 日志级别 | 使用场景 | 必须包含 |
|----------|----------|----------|
| ERROR | 异常、失败 | 请求 ID、错误栈、上下文 |
| WARNING | 降级、阈值超限 | 影响范围、建议操作 |
| INFO | 关键操作 | 操作人、耗时、结果状态 |
| DEBUG | 开发调试 | 详细参数、中间结果 |

---

## 九、测试策略

### 9.1 测试金字塔

```
        ┌─────────┐
        │   E2E   │  少量：端到端流程验证
        ├─────────┤
        │集成测试 │  适量：模块间接口验证
        ├─────────┤
        │ 单元测试│  大量：函数/类级别
        └─────────┘
```

### 9.2 测试分类

| 类型 | 工具 | 覆盖率目标 | 运行时机 |
|------|------|------------|----------|
| 单元测试 | pytest | ≥ 80% | 每次提交 |
| 集成测试 | pytest + TestClient | 核心流程 | 每次提交 |
| Agent 节点测试 | 直接调用节点函数 | 100% 节点 | 每次提交 |
| 自测脚本 | standalone .py | 阶段验证 | 每阶段结束 |
| 性能测试 | locust | 响应时间 | 上线前 |

### 9.3 Agent 节点测试模板

```python
# tests/test_agent_nodes.py
def test_route_query_high_risk():
    state = {"current_query": "上海落户政策是什么"}
    result = route_query(state)
    assert result["route"] == "search"
    assert result["query_risk_level"] == "high"

def test_search_dedup():
    state = {"current_query": "test", "last_search_query": "test", "retry_attempt": 0}
    result = search_knowledge(state)
    assert result.get("skip_search") == True

def test_dynamic_threshold_decay():
    checker = DynamicConfidenceThreshold()
    assert checker.get_threshold("high", retry=0) == 0.80
    assert checker.get_threshold("high", retry=1) == 0.65
    assert checker.get_threshold("high", retry=5) == 0.30  # 保底
```

---

## 十、部署与运维

### 10.1 部署架构

```
                    ┌──────────┐
                    │  Nginx   │  (反向代理 / SSL / 静态资源)
                    └────┬─────┘
                         │
              ┌──────────┴──────────┐
              │                     │
        ┌─────▼─────┐         ┌─────▼─────┐
        │  API 容器  │         │  API 容器  │  (uvicorn --workers 2)
        └─────┬─────┘         └─────┬─────┘
              │                     │
         ┌────┴────┐           ┌────┴────┐
         │         │           │         │
      ┌──▼──┐   ┌──▼──┐    ┌──▼──┐   ┌──▼──┐
      │ MySQL│   │Redis│    │MySQL│   │Redis│  (主从 / 集群)
      └─────┘   └─────┘    └─────┘   └─────┘
```

### 10.2 灰度发布策略

```
阶段 1：agent_enabled = false（默认）
        → 所有请求走传统 RAG
        → 验证基础功能正常

阶段 2：agent_enabled = true（测试环境）
        → 测试账号走 Agent
        → 对比 RAG vs Agent 效果

阶段 3：agent_enabled = true（生产 10% 流量）
        → 按用户 ID hash 分流
        → 监控错误率、延迟、成本

阶段 4：agent_enabled = true（生产 100%）
        → 全量上线
        → 保留快速回滚开关
```

---

## 十一、文档规范

### 11.1 文档体系

```
docs/
├── README.md                    # 总索引
├── architecture.md               # 架构设计文档
├── api-spec.md                   # API 规范
├── deployment.md                 # 部署指南
├── implementation/               # 实施指南
│   ├── README.md                 # 实施总览
│   ├── module-reference.md       # 模块速查
│   └── migration.md              # 数据库迁移
├── progress/                     # 进度追踪
│   ├── README.md                 # 阶段总览
│   ├── phase-0-environment.md
│   ├── phase-1-xxx.md
│   └── ...
└── adr/                          # 架构决策记录
    ├── ADR-001-xxx.md
    └── ADR-002-xxx.md
```

### 11.2 进度追踪模板

```markdown
## 阶段 N：阶段名称

| 字段 | 内容 |
|------|------|
| **时间** | YYYY-MM-DD |
| **状态** | ✅ 完成 / ⏸️ 进行中 / ❌ 阻塞 |
| **目标** | [一句话描述] |

### 操作记录

| 操作 | 修改文件 | 说明 |
|------|----------|------|
| 操作 1 | file.py | 添加 xxx |
| 操作 2 | file.py | 修改 xxx |

### 验收清单

- [x] 单元测试通过
- [x] 集成测试通过
- [x] 代码 Review 通过
- [x] 文档已更新

### 遗留问题

| 问题 | 严重程度 | 计划解决时间 |
|------|----------|--------------|
| ...  | P1       | YYYY-MM-DD   |
```

---

## 十二、关键工程原则

### 12.1 渐进式开发

```
V1 简化标记
├── 所有简化处加注释：`# V1 简化：xxx`
├── 明确标注 V2 升级计划
└── 保持核心路径可运行，不追求一步到位

渐进式接入
├── 新功能默认关闭（feature flag）
├── 先跑通，再优化，最后全量
└── 保留回滚路径
```

### 12.2 容错与降级

| 组件 | 降级策略 |
|------|----------|
| Redis | 不可用时降级到内存缓存，功能不受影响 |
| LLM | 超时后返回兜底回答，不阻塞请求 |
| 向量库 | 不可用时返回空结果，不抛异常 |
| 监控 | 独立运行，失败不影响主流程 |

### 12.3 代码质量

| 检查项 | 工具/方法 |
|--------|-----------|
| 代码格式 | ruff / black / eslint |
| 类型检查 | mypy / TypeScript strict |
| 依赖安全 | pip-audit / npm audit |
| 代码 Review | Pull Request + 检查清单 |
| 测试覆盖率 | pytest-cov（后端） / vitest（前端） |

---

## 十三、项目启动 Checklist

```
启动新项目时，按此 checklist 逐项确认：

□ 1. 需求文档已确认（PRD / 用户故事）
□ 2. 技术栈已确定（记录 ADR）
□ 3. 目录结构已搭建（使用本框架模板）
□ 4. 配置管理已就绪（config.py + .env.example）
□ 5. 数据库设计已完成（ER 图 + 迁移脚本）
□ 6. Docker Compose 可一键启动
□ 7. 统一响应格式已定义
□ 8. 日志规范已统一
□ 9. 错误处理策略已确定
□ 10. 监控方案已规划（日志 / 链路 / 指标）
□ 11. 测试策略已制定（单元 / 集成 / E2E）
□ 12. 部署方案已设计（灰度 / 回滚）
□ 13. 文档体系已建立（README 总索引）
```

---

## 十四、参考资源

| 资源 | 链接 | 说明 |
|------|------|------|
| FastAPI 最佳实践 | https://fastapi.tiangolo.com | 官方文档 |
| LangGraph 指南 | https://langchain-ai.github.io/langgraph/ | 工作流模式 |
| 12-Factor App | https://12factor.net | 云原生应用规范 |
| 语义缓存论文 | — | Redis + Embedding 相似度匹配 |
| 渐进式发布 | 特性开关 + 流量切分 | 降低上线风险 |
