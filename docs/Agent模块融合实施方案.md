# 高校智慧就业服务平台 — Agent 模块融合实施方案

> **文档版本**：v3.0 最终优化整合版
> **创建时间**：2026-06-23
> **更新时间**：2026-06-24
> **适用范围**：rag 项目接入 Agent 智能体模块的完整落地指南
> **前置文档**：[Agent模块设计文档](./Agent模块设计文档.md) · [功能模块实现文档](./功能模块实现文档.md) · [产品介绍文档](./产品介绍文档.md)
> **关联优化方案**：[架构优化方案-v3.0](./架构优化方案-v3.0.md)
> **优化点数量**：12 项（来自架构优化方案的9项 + Agent专属死循环防护3项）

---

## 一、现状 vs 设计目标

### 1.1 项目全景对比

| 维度 | 当前状态（已实现） | 目标状态（设计文档） | 差距 |
|------|--------------------|----------------------|------|
| 架构 | FastAPI + 基础 RAG | FastAPI + LangGraph Agent + 监控 | 缺少 Agent 层和监控层 |
| 问答 | 纯 RAG 检索生成 | Agent 工作流（路由→检索→生成→验证→拒答） | 核心：需要引入 LangGraph |
| 幻觉防护 | Prompt 提示 | **五重防护**（动态阈值 + 置信度过滤 + 引用强制 + 一致性检查 + 事实核验） | 新增 4 层 |
| 溯源 | Chunk 级别引用 | **句子级别引用 + 引用验证** | 需要 SentenceLevelCitationTracker |
| 时效管理 | 无 | **健康度监控 + 时效感知检索** | 新增 monitor 模块 |
| 可观测性 | 基础日志 | LangSmith 追踪 + 拒答分析 + 引用质量评估 | 新增可观测体系 |
| 成本控制 | 无 | **LLM 成本监控告警** | 新增 cost_monitor |

### 1.2 代码层面的差距

```
backend/app/
├── agent/           ❌ 不存在 → 【新增】LangGraph 工作流核心
│   ├── state.py     ❌
│   ├── nodes.py     ❌
│   ├── graph.py     ❌
│   ├── tools.py     ❌
│   ├── hallucination_defense.py  ❌ (文档中叫 hallucination_defense)
│   ├── citation_tracker.py       ❌
│   ├── temporal_retriever.py     ❌
│   └── refusal_handler.py        ❌
│
├── monitor/         ❌ 不存在 → 【新增】监控告警模块
│   ├── health_monitor.py         ❌
│   ├── cost_monitor.py           ❌
│   ├── langsmith_tracker.py      ❌
│   ├── citation_evaluator.py     ❌
│   └── consistency_checker.py    ❌
│
├── routers/
│   ├── agent.py     ❌ 不存在 → 【新增】Agent 对话路由
│   ├── refusal.py   ❌
│   ├── kb_health.py ❌
│   ├── llm_cost.py  ❌
│   └── ...
│
├── schemas/
│   ├── agent.py     ❌ 不存在
│   └── monitor.py   ❌
│
├── models/
│   ├── agent.py     ❌ 不存在
│   └── monitor.py   ❌
│
✅ 已存在的模块（保持）：
├── core/  (config, database, security, deps, response, llm, embedding, vectorstore, chunkers)
├── models/ (user, knowledge, qa, ops)
├── schemas/ (common, user, knowledge, qa, ops)
├── services/ (user, knowledge, index, qa, rag, ops)
└── routers/ (auth, users, roles, documents, faqs, qa, conversations, messages, etc.)
```

---

## 二、融合文档：统一实施指南

> 下面的内容将三个文档的核心有效内容融合为可执行的实施方案。
> **设计文档**中的"面试核心要点"部分属于面试辅导，**本实施方案中予以省略**，聚焦落地。

### 2.1 技术选型确认

| 技术 | 用途 | 状态 |
|------|------|------|
| **LangGraph** | Agent 状态机工作流 | 待引入 |
| **LangSmith** | LLM 调用追踪 + Prompt 管理 | 待引入 |
| **ChromaDB** | 向量存储（已有） | ✅ 已存在 |
| **通义千问** | LLM 推理（已有） | ✅ 已存在 |
| **MySQL** | 业务数据 | ✅ 已存在 |
| **Redis** | 缓存 + 向量库元数据 | 待验证 |
| **SQLAlchemy** | ORM | ✅ 已存在 |
| **FastAPI** | Web 框架 | ✅ 已存在 |

### 2.2 新增依赖确认

在 `backend/requirements.txt` 中确认新增以下依赖：

```txt
# Agent 核心
langgraph>=0.1.0
langgraph-checkpoint>=0.1.0

# LangSmith 追踪
langsmith>=0.1.0

# LlamaIndex（用于混合检索和 Rerank —— 当前版本暂用 ChromaDB 直连，后续升级）
# llama-index-core>=0.10.0
# llama-index-vector-stores-chroma>=0.1.0
# llama-index-postprocessor-cohere-rerank>=0.1.0

# 定时任务
apscheduler>=3.10.0
```

---

## 三、分阶段实施方案

### 阶段总览

```
阶段 0：环境准备           （半天）
阶段 1：Agent 核心构建     （2～3 天）← 最核心
阶段 2：幻觉防御集成       （1～2 天）← 产品差异化关键
阶段 3：监控告警模块       （1～2 天）← 工程化关键
阶段 4：问答服务升级       （1 天）     ← 连接前后端
阶段 5：路由 + Schema 补齐（半天）
阶段 6：前端对接           （1 天）
阶段 7：集成测试 + 灰度    （1 天）
```

---

### 阶段 0：环境准备

**目标**：确认依赖 + 数据库表就绪 + 配置项就绪。

**步骤 1**：更新 `requirements.txt`

在 `backend/requirements.txt` 中追加（见上方 2.2 节）。

**步骤 2**：执行数据库迁移

```bash
cd backend
python -c "from migrations.add_agent_tables import migrate; migrate()"
```

需要新增的表：
- `agent_refusal_log` — 拒答记录
- `citation_quality_log` — 引用质量日志
- `kb_health_log` — 知识库健康度日志
- `llm_cost_log` — LLM 成本日志
- `consistency_issue_log` — 一致性问题日志
- `fact_verification_log` — 事实核验日志

需要修改的表：
- `qa_message` — 新增字段：`confidence`、`query_risk_level`

> 迁移脚本见 `功能模块实现文档.md §12.3`。正式生产应使用 Alembic 管理迁移。

**步骤 3**：更新 `config.py` 配置项

在 `app/core/config.py` 的 `Settings` 类中新增：

```python
# ===== Agent 配置 =====
agent_max_iterations: int = 10           # 最大迭代步数
agent_timeout_seconds: int = 60          # 超时时间
agent_recursion_limit: int = 15          # 🔧【优化新增】LangGraph 递归限制（防死循环）

# ===== LangSmith 配置 =====
langsmith_tracing: bool = False          # 是否开启追踪
langsmith_api_key: str = ""              # API Key
langsmith_project: str = "aiqa-agent"    # 项目名
langsmith_endpoint: str = "https://api.smith.langchain.com"

# ===== 幻觉防御配置 =====
high_risk_threshold: float = 0.80        # 高风险阈值
medium_risk_threshold: float = 0.65      # 中风险阈值
low_risk_threshold: float = 0.40         # 低风险阈值

# ===== 时效性配置 =====
kb_warning_days: int = 30                # 知识库过期告警天数
kb_freshness_half_life: int = 180        # 新鲜度半衰期(天)

# ===== 成本控制配置 =====
daily_cost_threshold_usd: float = 10.0   # 日成本阈值
monthly_cost_threshold_usd: float = 300.0 # 月成本阈值
```

---

### 阶段 1：Agent 核心构建（最关键）

**目标**：建立 LangGraph 状态机 + 节点 + 工作流，让 Agent 能跑起来。

#### 1.1 新建 `backend/app/agent/state.py`

定义 `AgentState`（TypedDict），包含：
- `messages` — 对话历史（Annotated + add_messages）
- `current_query` — 当前用户查询
- `search_results` — 检索结果
- `citations` — 引用信息
- `confidence` — 综合置信度
- `query_risk_level` — 查询风险等级
- `tools_used` / `tool_outputs` — 工具使用记录
- `response` — 最终回答
- `route` — 路由决策
- `should_refuse` / `refusal_reason` — 拒答相关
- `consistency_issues` / `fact_issues` / `temporal_warnings` — 五重防护结果
- `conversation_id` / `user_id` / `created_at` — 业务关联

🔧 **【优化新增】会话记忆/跨轮次持久化（变化点7）**：
```python
# ===== 会话记忆字段 =====
history: list[dict]              # 历史对话摘要（最近N轮）
session_context: dict            # 会话级上下文（学生姓名、学院、专业等）
last_topic: str                  # 上一轮话题（用于"那个""它"指代理解）
```
> 💡 作用：用户问"那个政策……"时，Agent能理解指的是上一轮的话题。
> 实现：会话状态保存到Redis，24小时过期，刷新不丢失。

🔧 **【优化新增】可解释性/推理链（变化点17）**：
```python
# ===== 可解释性字段 =====
reasoning_chain: list[dict]      # 推理链，每步决策记录
explainability_log: str          # 可解释性日志
```
> 💡 作用：前端可展示"AI是怎么想的"折叠面板，提升用户信任感。
> 推理链示例：路由判断 → 知识检索 → 置信度检查 → 回答生成

🔧 **【优化新增】错误处理/幂等/回滚（变化点9）**：
```python
# ===== 错误处理字段 =====
partial_effects: list[dict]      # 已执行的副作用记录（用于回滚）
error: dict                      # 错误信息
request_id: str                  # 请求ID（幂等键）
```
> 💡 作用：LLM调用超时等异常时，回滚已写入的副作用，保证数据一致性。

🔧 **【优化新增】死循环防护相关字段**：
```python
# ===== 循环防护字段 =====
retry_attempt: int                    # 置信度重试次数（防条件判断循环）
tool_call_count: int                  # 工具调用总次数（防工具选择循环）
last_search_query: str                # 上次检索关键词（语义去重）
regenerate_count: int                 # 重生成次数（防结果验证循环）
high_severity_count: int              # 高严重度问题数
medium_severity_count: int            # 中严重度问题数
forced_exit: bool                     # 是否强制退出循环
is_low_confidence: bool               # 是否低置信度降级回答
skipped_consistency_check: bool       # 是否跳过一致性检查（降级）
```

> 参考：`功能模块实现文档.md §5.3`

#### 1.2 新建 `backend/app/agent/nodes.py`

实现以下节点：

| 节点 | 功能 | 优先级 |
|------|------|--------|
| `route_query` | 路由决策：search / tool_call / direct / refuse | P0 |
| `search_knowledge` | 时效感知向量检索 | P0 |
| `check_confidence` | 动态置信度判断（是否拒答） | P0 |
| `generate_response` | 带引用生成回答 | P0 |
| `check_consistency` | 自我一致性检查 | P1 |
| `verify_facts` | 事实核验（政策编号/日期/金额） | P1 |
| `generate_refusal` | 拒答回复生成 | P0 |
| `regenerate_with_hints` | 🔧【优化新增】带修正提示的重新生成 | P1 |
| `accept_with_warning` | 🔧【优化新增】接受回答但附加警告 | P1 |
| `content_moderation` | 🔧【优化新增】LLM输出内容审核（变化点5） | P1 |
| `error_handler` | 🔧【优化新增】统一错误处理/回滚（变化点9） | P0 |

`route_query` 节点逻辑（简化版）：

```python
# 关键词路由规则（从设计文档中提取）
HIGH_RISK_KEYWORDS  = ["落户", "补贴", "政策", "规定", "流程", "申请", "条件", "要求", "资格", "审批", "办理"]
TOOL_CALL_KEYWORDS  = ["查询", "预约", "生成", "提交", "我的", "档案"]
LOW_RISK_KEYWORDS   = ["你好", "谢谢", "再见", "辛苦", "在吗"]

# 路由决策
if any(k in query for k in HIGH_RISK_KEYWORDS):
    return "search", "high"
elif any(k in query for k in TOOL_CALL_KEYWORDS):
    return "tool_call", "medium"
elif any(k in query for k in LOW_RISK_KEYWORDS):
    return "direct", "low"
else:
    return "search", "medium"
```

🔧 **【优化新增】工具选择循环防护**（在 route_query 节点中）：
```python
def route_query(self, state: AgentState) -> dict:
    # 工具调用次数 >= 3 时强制生成，防止死循环
    if state.get("tool_call_count", 0) >= 3:
        return {"route": "generate", "forced_exit": True}
    # ... 正常路由逻辑
```

🔧 **【优化新增】检索去重**（在 search_knowledge 节点中）：
```python
def search_knowledge(self, state: AgentState) -> dict:
    query = state["current_query"]
    # 去重：相同查询不重复检索
    if query == state.get("last_search_query", ""):
        return {"route": "generate", "skip_search": True}
    
    result = self.temporal_retriever.retrieve(query, top_k=5)
    return {
        "search_results": result,
        "last_search_query": query,
        "tool_call_count": state.get("tool_call_count", 0) + 1,
    }
```

🔧 **【优化新增】条件判断循环防护**（在 check_confidence 节点中）：
- 动态降级阈值（每次重试降低 0.15，保底 0.30）
- 最大重试次数（3次）
- 重试耗尽 → 降级回答（带警告），不拒答

详见「阶段 2」hallucination_defense.py 中的动态阈值逻辑。

🔧 **【优化新增】结果验证循环防护**（在 check_consistency 节点中）：
- 严重度分级：只重试 high 严重度问题
- 最大重生成次数（2次）
- medium 严重度 → accept_with_warning（接受+警告）
- 超限 → refuse（拒答 + 人工审核标记）

详见「阶段 2」和「第八章 死循环防护」。

🔧 **【优化新增】LLM输出内容审核（变化点5）**（在 content_moderation 节点中）：

```python
def content_moderation(self, state: AgentState) -> Dict[str, Any]:
    """内容审核节点：检查LLM输出是否包含违规内容"""
    response = state.get("response", "")
    
    # 违规类型检测
    SENSITIVE_PATTERNS = {
        "politics": ["国家领导人", "主席", "总理", "反动", "颠覆"],
        "porn": ["色情", "赌博", "毒品", "裸聊"],
        "contact": [r"\d{3}-\d{8}", r"[a-zA-Z0-9._%+-]+@..."],
        "ad": ["加我微信", "私信", "代做", "枪手"],
    }
    
    is_safe = True
    violations = []
    
    # TODO: 调用内容审核API或正则匹配
    # 发现违规内容 → 拒答 + 记录
    
    if not is_safe:
        return {
            "should_refuse": True,
            "refusal_reason": "回答内容包含违规信息，已拦截",
            "content_violations": violations,
        }
    
    return {"content_safe": True}
```

> 💡 与敏感词过滤形成**双重防护**：敏感词过滤在输入侧，内容审核在输出侧。

🔧 **【优化新增】统一错误处理/幂等/回滚（变化点9）**（在 error_handler 节点中）：

```python
def error_handler(self, state: AgentState) -> Dict[str, Any]:
    """统一错误处理：记录错误，回滚副作用，返回友好提示"""
    
    error = state.get("error")
    if not error:
        return state
    
    # 1. 记录错误日志（脱敏后）
    log_error(
        error_type=error.get("type"),
        error_msg=error.get("message"),
        request_id=state.get("request_id"),
        user_id=state.get("user_id"),
    )
    
    # 2. 回滚已执行的副作用
    partial_effects = state.get("partial_effects", [])
    for effect in reversed(partial_effects):
        try:
            rollback_effect(effect)
        except Exception as e:
            log_rollback_failure(effect, e)
    
    # 3. 返回用户友好的错误提示
    return {
        "response": "抱歉，系统处理您的请求时遇到了问题，请稍后再试或联系就业中心老师。",
        "should_refuse": True,
        "is_error": True,
    }
```

> 💡 幂等保证：同一 request_id 重复调用，不会产生重复副作用。

#### 1.3 新建 `backend/app/agent/graph.py`

使用 `StateGraph` 构建工作流：

```
START → route → [search | direct | refuse]
                    ↓
              search → check_confidence
                    ↓
         [generate | regenerate | refuse]
                    ↓
         check_consistency → verify_facts
                    ↓
          🔧 content_moderation（内容审核）
                    ↓
              [accept | accept_with_warning | refuse]
                    ↓
              🔧 error_handler（兜底错误处理）
                    ↓
                     END
```

🔧 **【优化新增】完整工作流图（含死循环防护 + 内容审核 + 错误处理）**：

```python
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from app.core.config import settings

class AgentGraph:
    def __init__(self, nodes):
        self.nodes = nodes
        self.graph = None

    def build(self) -> StateGraph:
        graph = StateGraph(AgentState)

        graph.add_node("route",               self.nodes.route_query)
        graph.add_node("search",              self.nodes.search_knowledge)
        graph.add_node("check_confidence",    self.nodes.check_confidence)
        graph.add_node("generate",            self.nodes.generate_response)
        graph.add_node("regenerate",          self.nodes.regenerate_with_hints)
        graph.add_node("check_consistency",   self.nodes.check_consistency)
        graph.add_node("verify_facts",        self.nodes.verify_facts)
        graph.add_node("content_moderation",  self.nodes.content_moderation)   # 🔧 新增
        graph.add_node("accept_with_warning", self.nodes.accept_with_warning)
        graph.add_node("refuse",              self.nodes.generate_refusal)
        graph.add_node("error_handler",     self.nodes.error_handler)      # 🔧 新增

        graph.add_edge(START, "route")

        # route 分支
        graph.add_conditional_edges(
            "route", self._route_decision,
            {"search": "search", "direct": END, "refuse": "refuse"},
        )

        # search → check_confidence
        graph.add_edge("search", "check_confidence")

        # check_confidence 三分支
        graph.add_conditional_edges(
            "check_confidence", self._confidence_decision,
            {
                "accept":     "generate",
                "regenerate": "regenerate",  # 降级阈值后再检索
                "refuse":     "refuse",
            },
        )

        # regenerate → generate（后续加跳转回 search 的逻辑）
        graph.add_edge("regenerate", "generate")

        # generate → check_consistency → verify_facts → content_moderation（🔧 新增内容审核）
        graph.add_edge("generate", "check_consistency")
        graph.add_edge("check_consistency", "verify_facts")
        graph.add_edge("verify_facts", "content_moderation")

        # content_moderation → 最终决策（🔧 新增：内容审核后再决策）
        graph.add_conditional_edges(
            "content_moderation", self._post_moderation_decision,
            {
                "accept":              END,
                "accept_with_warning": "accept_with_warning",
                "refuse":              "refuse",
            },
        )

        graph.add_edge("accept_with_warning", "error_handler")   # 🔧 走错误处理兜底
        graph.add_edge("refuse", "error_handler")               # 🔧 走错误处理兜底
        graph.add_edge("error_handler", END)                     # 🔧 最终出口

        self.graph = graph
        return graph

    def compile(self):
        """编译工作流，配置Checkpoint和递归限制"""
        graph = self.build()
        memory = MemorySaver()
        return graph.compile(
            checkpointer=memory,
            # 🔧【优化新增】递归限制，防止死循环（硬兜底）
            recursion_limit=settings.agent_recursion_limit,
        )
```

关键：
- 使用 `MemorySaver` 做 Checkpoint，支持对话暂停/恢复
- 🔧 **【优化新增】** `recursion_limit` 硬限制递归步数（防死循环最后一道防线）

#### 1.4 新建 `backend/app/agent/tools.py`

工具集（当前阶段只需要检索工具，工具调用后续扩展）：

```python
# 当前只需要
TOOLS = {
    "knowledge_search": search_knowledge,  # 知识库检索
}

# 后续扩展
TOOLS_LATER = {
    "appointment_query": 查询预约空档,
    "resume_generator":  生成简历,
    "policy_lookup":     政策精确查询,
}
```

#### 1.5 新增路由 `backend/app/routers/agent.py`

```python
router = APIRouter(prefix="/agent", tags=["Agent对话"])

@router.post("/chat")       # 同步对话
@router.post("/chat/stream")# 流式对话（SSE）
async def agent_chat(...):
    # 1. 获取当前用户
    # 2. 调用 agent_graph.run()
    # 3. 记录消息到 MySQL
    # 4. 返回结果（含 citations / confidence / warnings）
```

#### 1.6 主入口注册

在 `backend/app/main.py` 中注册：

```python
from app.routers import agent
app.include_router(agent.router, prefix=settings.api_prefix)
```

---

### 阶段 2：幻觉防御集成

**目标**：让 Agent 的回答具备五重防护能力。

#### 2.1 新建 `backend/app/agent/hallucination_defense.py`

实现三个类：

| 类 | 职责 |
|----|------|
| `DynamicConfidenceThreshold` | 按查询风险等级（high/medium/low）使用不同阈值 |
| `SelfConsistencyChecker` | 检查同一对话中同类问题回答是否矛盾 |
| `FactVerificationPostProcessor` | 正则验证政策编号、日期、金额等 |

**动态阈值配置**（直接取自设计文档）：

```python
THRESHOLD_CONFIG = {
    "high":   {"min_confidence": 0.80, "min_results": 3, "require_citation": True},
    "medium": {"min_confidence": 0.65, "min_results": 2, "require_citation": True},
    "low":    {"min_confidence": 0.40, "min_results": 1, "require_citation": False},
}
```

🔧 **【优化新增】动态降级阈值（防条件判断循环）**：

```python
def should_accept_result(
    self,
    query: str,
    confidence: float,
    results_count: int,
    has_citation: bool,
    retry_attempt: int = 0,      # 新增：重试次数
) -> tuple[bool, str]:
    """判断是否接受检索结果，每次重试自动降低阈值"""
    risk_level = self.classify_query(query)
    base_config = self.THRESHOLD_CONFIG[risk_level]

    # 每次重试降低 0.15，保底不低于 0.30
    threshold = max(0.30, base_config["min_confidence"] - retry_attempt * 0.15)
    min_results = max(1, base_config["min_results"] - retry_attempt)

    reasons = []
    if confidence < threshold:
        reasons.append(f"置信度{confidence:.2f} < 当前阈值{threshold}")
    if results_count < min_results:
        reasons.append(f"检索结果数{results_count} < 最低要求{min_results}")
    if base_config["require_citation"] and not has_citation:
        reasons.append("该类查询必须有引用来源")
    return (len(reasons) == 0, "; ".join(reasons))
```

**动态阈值变化表**：

| 重试次数 | high 阈值 | medium 阈值 | low 阈值 | 最小结果数 |
|----------|-----------|-------------|----------|------------|
| 0（首次） | 0.80 | 0.65 | 0.40 | 3 / 2 / 1 |
| 1 | 0.65 | 0.50 | 0.30 | 2 / 2 / 1 |
| 2 | 0.50 | 0.35 | 0.30 | 2 / 1 / 1 |
| 3+ | 0.30 | 0.30 | 0.30 | 1 / 1 / 1 |

**事实核验正则规则**：

```python
FACT_RULES = {
    "policy_no": r"[一-龥]{2,4}〔\d{4}〕\d+号",  # 国办发〔2024〕5号
    "date":      r"\d{4}年\d{1,2}月\d{1,2}日",
    "money":     r"\d+(\.\d+)?(万|千|百)?元",
    "count":     r"\d+(个|项|种|类|份)",
}
```

#### 2.2 新建 `backend/app/agent/citation_tracker.py`

实现 `SentenceLevelCitationTracker`：

1. 将回答按 `。！？；` 切分为句子
2. 对每个句子，找到最相关的来源 chunk（Embedding 相似度）
3. 使用 LLM 验证引用支持度（direct / indirect / none）
4. 返回句子级别引用列表

#### 2.3 新建 `backend/app/agent/temporal_retriever.py`

实现 `TemporalAwareRetriever`：

1. 基础向量检索（取 top_k × 2 候选）
2. 计算时效性得分（指数衰减：`exp(-0.693 × days / half_life)`）
3. 综合得分 = 相似度 × 0.7 + 时效性 × 0.3
4. 过期文档降权 × 0.1
5. 按综合得分排序取 top_k

参数：
```python
CONFIG = {
    "half_life_days": 180,
    "similarity_weight": 0.7,
    "temporal_weight": 0.3,
    "expired_penalty": 0.1,
}
```

#### 2.4 新建 `backend/app/agent/refusal_handler.py`

拒答回复模板（直接取自设计文档）：

```python
REFUSAL_TEMPLATE = """抱歉，关于"{question}"这个问题：

{reason}

建议您：
1. 联系学校就业中心老师咨询
2. 查看相关政府部门的官方网站
3. 拨打官方咨询热线

如果您还有其他就业相关问题，我很乐意帮助您。"""
```

---

### 阶段 3：监控告警模块

**目标**：建立知识库健康度监控 + LLM 成本监控 + 引用质量评估。

#### 3.1 新建 `backend/app/monitor/health_monitor.py`

`KnowledgeBaseHealthMonitor` 每日检查：

| 检查项 | 逻辑 | 告警级别 |
|--------|------|----------|
| 即将过期文档 | 30 天内过期 | ⚠️ warning |
| 已过期文档 | valid_until < today | 🔴 critical |
| 健康度评分 | Σ(文档新鲜度 × 权重) / 总数 | < 60 分告警 |

新鲜度公式：
```
freshness = exp(-0.693 × days_since_valid / 180)
# expired 文档 × 0.1 惩罚
```

#### 3.2 新建 `backend/app/monitor/cost_monitor.py`

```python
DAILY_COST_THRESHOLD   = 10.0  # USD
MONTHLY_COST_THRESHOLD = 300.0 # USD
```

从 LangSmith 或自建日志中统计每日/每月 LLM 消耗，超阈值触发告警。

🔧 **【优化新增】告警阈值与告警通道**：

```python
# 告警级别配置
ALERT_LEVELS = {
    "info":     {"threshold_pct": 70,  "channels": ["email"]},
    "warning":  {"threshold_pct": 85,  "channels": ["email", "feishu"]},
    "critical": {"threshold_pct": 100, "channels": ["email", "feishu", "sms"]},
}

# 告警通道
ALERT_CHANNELS = {
    "email":    "告警邮件（运维组）",
    "feishu":   "飞书群机器人（技术群）",
    "dingtalk": "钉钉群机器人（可选）",
    "sms":      "短信告警（仅critical级别）",
}

# 告警抑制规则
# 同一告警5分钟内只发1次，防止轰炸
ALERT_SUPPRESSION_WINDOW = 300  # 秒
```

**多级告警策略**：
| 级别 | 触发条件 | 通知方式 | 处理要求 |
|------|----------|----------|----------|
| INFO | 日成本 > 70%阈值 | 邮件 | 留意即可 |
| WARNING | 日成本 > 85%阈值 | 邮件 + 飞书 | 当天排查 |
| CRITICAL | 日成本 > 100%阈值 | 邮件 + 飞书 + 短信 | 立即处理，必要时降级 |

#### 3.3 新建 `backend/app/monitor/citation_evaluator.py`

`CitationQualityEvaluator`：

```python
quality_score = (direct_count × 1.0 + indirect_count × 0.5 + none_count × 0.0) / total
```

#### 3.4 定时任务

使用 APScheduler（或 FastAPI 的 `BackgroundTasks`）：

```python
# 每日凌晨 2 点 → 知识库健康检查
# 每月 1 号 → LLM 成本月报
```

---

### 阶段 4：问答服务升级

**目标**：将现有 `qa_service.py` 从纯 RAG 升级为集成 Agent 工作流。

#### 4.1 升级 `backend/app/services/qa_service.py`

当前 `qa_service.py` 只管理会话和消息的 CRUD。需要：

1. **新增 `AgentQAService` 类**（或直接在现有类中新增方法）
2. **chat 方法改造**：

```python
async def chat(self, query: str, user_id: int, conversation_id: int = None):
    # 1. 创建/获取会话（复用现有逻辑）
    # 2. 调用 Agent 工作流
    result = await agent_graph.run(query, conversation_id, user_id)
    # 3. 记录用户消息 + AI 消息（复用现有逻辑，新增字段）
    # 4. 记录引用（SentenceLevelCitationTracker 结果）
    # 5. 更新会话
    return result
```

🔧 **【优化新增】稳定性保障（限流 + 超时 + 熔断）**：

```python
# 限流配置（与全局限流配合，Agent单独限流）
AGENT_RATE_LIMIT = {
    "per_user": {"limit": 10, "window": 60},      # 每用户：10次/分钟
    "global":  {"limit": 100, "window": 60},      # 全局：100次/分钟
}

# 超时配置
AGENT_TIMEOUT_CONFIG = {
    "total": 60,           # 总超时 60秒
    "llm_call": 30,        # 单次LLM调用超时 30秒
    "search": 10,          # 检索超时 10秒
}

# 熔断配置（🔧 优化新增）
CIRCUIT_BREAKER_CONFIG = {
    "failure_threshold": 5,     # 连续5次失败触发熔断
    "recovery_timeout": 30,     # 30秒后进入半开状态
    "half_open_limit": 3,       # 半开状态最多放行3个请求
    "failure_statuses": [500, 502, 503, 504, 429],
}
```

**降级策略**：
| 场景 | 降级方式 | 用户感知 |
|------|----------|----------|
| 熔断开启 | 回退到基础 RAG | 功能降级，无 Agent 多步推理 |
| LLM 超时 | 返回缓存答案 + 提示 | "当前咨询量较大，为您返回参考解答" |
| 向量库不可用 | 走 FAQ 匹配 + 拒答 | 仅回答常见问题 |
| 限流触发 | 返回排队提示 | "当前咨询量较大，请稍候再试" |

🔧 **【优化新增】会话状态一致性（多设备同步）（变化点8）**：

```python
# qa_service.py 中集成会话管理器
class SessionManager:
    """会话管理器：保证跨设备/跨实例的会话一致性"""
    
    # Redis 数据结构：
    # session:user:{user_id}:active → 当前活跃会话ID
    # session:conv:{conv_id}:context → 全局上下文（所有设备共享）
    # session:conv:{conv_id}:device:{device_id} → 设备特有上下文
    
    async def get_or_create_session(self, user_id, device_id, conversation_id=None):
        """获取或创建会话，保证多设备状态一致"""
        # 1. 查找用户当前活跃会话
        # 2. 获取全局上下文（共享）
        # 3. 获取设备特有上下文（独立）
        pass
    
    async def sync_across_devices(self, conversation_id, update, device_id=None):
        """全局上下文同步到所有设备"""
        pass
```

> 💡 作用：用户在Web和手机同时登录时，会话状态不会串乱；支持多副本横向扩展。

🔧 **【优化新增】语义缓存（变化点16）**：

```python
# 新增：app/core/semantic_cache.py
class SemanticCache:
    """语义缓存：相似问题直接返回缓存答案，降低LLM成本"""
    
    def __init__(self, similarity_threshold=0.92):
        self.threshold = similarity_threshold
        self.redis = get_redis()
    
    async def get(self, query: str) -> dict | None:
        """查询缓存：找到语义相似的问题则返回"""
        # 1. 计算query的embedding
        # 2. 在Redis中查找相似问题
        # 3. 相似度 > 0.92 → 命中缓存
        pass
    
    async def set(self, query: str, response: dict):
        """缓存答案，24小时过期"""
        pass
```

**调用位置**：在调用 Agent 工作流之前，先查语义缓存。

> 💡 效果：FAQ类问题 LLM 成本降低 30%-50%，响应速度从 2-5s 降到 <100ms。

#### 4.2 升级 `backend/app/models/qa.py` — 新增字段

对 `QaMessage` 表新增字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `confidence` | DECIMAL(5,4) | 综合置信度 |
| `query_risk_level` | VARCHAR(20) | 查询风险等级 |
| `consistency_issues` | TEXT (JSON) | 一致性问题列表 |
| `fact_issues` | TEXT (JSON) | 事实核验问题列表 |
| `temporal_warnings` | TEXT (JSON) | 时效性警告 |
| `llm_tokens_in` | INTEGER | Prompt Token 数（已有 prompt_tokens） |
| `llm_tokens_out` | INTEGER | 生成 Token 数（已有 completion_tokens） |

> 表中已有 `prompt_tokens` / `completion_tokens` / `latency_ms`，可直接复用。

---

### 阶段 5：路由 + Schema 补齐

#### 5.1 新建 `backend/app/schemas/agent.py`

```python
class AgentChatRequest(BaseModel):
    query: str
    conversation_id: int | None = None

class AgentChatResponse(BaseModel):
    conversation_id: int
    message_id: int
    response: str
    confidence: float
    is_no_answer: bool
    route: str
    citations: list[dict]
    consistency_issues: list[dict] | None
    fact_issues: list[dict] | None
    temporal_warnings: list[str] | None
```

#### 5.2 新建 `backend/app/schemas/monitor.py`

健康度报告、成本日志等 Schema。

#### 5.3 注册新路由

在 `main.py` 中追加：

```python
from app.routers import agent, refusal, kb_health, llm_cost

app.include_router(agent.router,      prefix=settings.api_prefix)
app.include_router(refusal.router,    prefix=settings.api_prefix)
app.include_router(kb_health.router,  prefix=settings.api_prefix)
app.include_router(llm_cost.router,   prefix=settings.api_prefix)
```

---

### 阶段 6：前端对接

**目标**：前端支持 Agent 对话界面的 enriched response 展示。

#### 6.1 需要改动的文件

| 文件 | 改动 |
|------|------|
| `frontend/src/types/chat.ts` | 新增 `AgentMessage` 类型（含 `citations` / `confidence` / `temporal_warnings`） |
| `frontend/src/api/chat.ts` | 新增 `/api/v1/agent/chat` 接口 |
| `frontend/src/composables/useStreamChat.ts` | 接入流式 Agent 响应 |
| `frontend/src/stores/chat.ts` | 扩充 state 以存储引用、置信度等 Agent 输出字段 |
| `frontend/src/views/ChatView.vue` | 渲染引用卡片、时效性提示、置信度标签 |

#### 6.2 新增前端 UI 组件

```
frontend/src/components/agent/
├── CitationCard.vue      # 引用卡片：展示来源文档 + 匹配度 + 时效状态
├── ConfidenceBadge.vue   # 置信度标签：高/中/低 颜色区分
├── TemporalWarning.vue   # 时效性警告横幅
├── RefusalMessage.vue    # 拒答提示 + 建议操作
└── ConsistencyAlert.vue  # 一致性冲突提示
```

#### 6.3 前端对接要点

```typescript
// useStreamChat.ts — Agent 模式
const response = await fetch('/api/v1/agent/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ query, conversation_id }),
})
const data = await response.json()
// data = { response, confidence, citations, temporal_warnings, ... }
```

---

### 阶段 7：集成测试 + 灰度

#### 7.1 测试检查清单

| 测试项 | 方法 | 通过标准 |
|--------|------|----------|
| 路由正确性 | 问政策问题 → 应走 search | route = "search" |
| 拒答正确性 | 问无关问题 → 应拒答 | is_no_answer = true |
| 引用追踪 | 问具体政策 → 每条回答有 [1][2] 标注 | citations 非空 |
| 置信度过滤 | 检索结果 < 阈值 → 拒答 | confidence < threshold → refuse |
| 时效降权 | 检索结果含过期文档 → 降权 | expired 文档排序降低 |
| 一致性检查 | 同一对话问同类问题 → 回答自洽 | consistency_issues 为空 |

🔧 **【优化新增】死循环防护专项测试**：

| 测试项 | 测试方法 | 通过标准 |
|--------|----------|----------|
| 工具选择循环防护 | 构造工具调用计数器=3的状态 | route_query返回"generate"，forced_exit=True |
| 检索去重防护 | 连续两次相同查询 | 第二次跳过检索，skip_search=True |
| 条件判断循环防护 | 低置信度连续重试 | 第3次后阈值降至0.30，最终接受或降级 |
| 结果验证循环防护 | 构造高严重度问题+regenerate_count=2 | 第3次后返回拒答 |
| 递归限制兜底 | 构造永远循环的状态 | recursion_limit触发RecursionError，有兜底回答 |
| 动态阈值验证 | 同一问题，不同retry_attempt | 阈值逐步降低，最低不低于0.30 |

#### 7.2 灰度策略

1. **第一阶段（1天）**：仅对内部用户（admin / teacher）开放 Agent 入口，旧 RAG 入口保留
2. **第二阶段（2天）**：对 10% 学生用户启用，对比 Agent 和旧 RAG 的回答质量
3. **第三阶段（3天）**：全量上线，旧 RAG 入口降级为 fallback

🔧 **【优化新增】灰度期间的回滚机制**：
- 灰度开关在配置中心（或数据库配置表），1分钟内可切回
- 保留旧 RAG 完整链路，随时可 100% 回滚
- 灰度期间双写日志，便于对比分析
- 设置自动回滚阈值：错误率 > 5% 自动降级

---

## 四、关键文件路径速查

### 后端新增文件清单

| 文件路径 | 对应设计文档章节 | 阶段 |
|----------|------------------|------|
| `agent/__init__.py` | — | 1 |
| `agent/state.py` | §5.3 | 1 |
| `agent/nodes.py` | §5.4 | 1 |
| `agent/graph.py` | §5.5 | 1 |
| `agent/tools.py` | §5.6 | 1 |
| `agent/hallucination_defense.py` | §5.6 | 2 |
| `agent/citation_tracker.py` | §5.7 | 2 |
| `agent/temporal_retriever.py` | §5.8 | 2 |
| `agent/refusal_handler.py` | §5.4(refuse节点) | 2 |
| `monitor/__init__.py` | — | 3 |
| `monitor/health_monitor.py` | §10.3 | 3 |
| `monitor/cost_monitor.py` | §10.3 | 3 |
| `monitor/citation_evaluator.py` | §10.3 | 3 |
| `monitor/consistency_checker.py` | §10.3 | 3 |
| `monitor/langsmith_tracker.py` | §10.3 | 3 |
| `routers/agent.py` | — | 5 |
| `routers/refusal.py` | — | 5 |
| `routers/kb_health.py` | — | 5 |
| `routers/llm_cost.py` | — | 5 |
| `schemas/agent.py` | — | 5 |
| `schemas/monitor.py` | — | 5 |
| `models/agent.py` | — | 5 |
| `models/monitor.py` | — | 5 |

### 需要修改的现有文件

| 文件路径 | 改动 |
|----------|------|
| `main.py` | 注册新路由 |
| `services/qa_service.py` | 接入 Agent 工作流 |
| `models/qa.py` | QaMessage 新增字段 |
| `requirements.txt` | 新增 langgraph / langsmith / apscheduler |

---

## 五、风险与注意事项

| 风险 | 说明 | 缓解措施 |
|------|------|----------|
| **LangGraph API 变化** | LangGraph 仍是较新的库，API 可能变 | 固定版本号，关注 changelog |
| **LLM 成本突增** | Agent 工作流多节点 = 更多 LLM 调用 | 阶段 3 的成本监控必须在 Agent 上线前就位 |
| **端到端延迟** | 5 重防护 → 增加 ~2-5 秒延迟 | 异步执行一致性/事实核验；流式返回 |
| **语义切分性能** | 每篇文档需要多次 Embedding 调用 | 对短文档(< 500字) 跳过语义切分，用固定切分 |
| **前端状态管理复杂度** | Agent 返回字段远多于旧 RAG | 前端用 union type 兼容新旧两种响应格式 |

---

## 六、推荐开发顺序（简化版）

```
Day 1：
  ├─ 阶段 0：环境准备 + 数据库迁移
  │   └─ 🔧 优化：config.py 新增 Agent/LangSmith/幻觉防御 配置项
  └─ 阶段 1.1：state.py + nodes.py（只实现 route / search / generate / refuse）
      └─ 🔧 优化：state.py 加会话记忆 + 推理链 + 错误回滚 + 死循环防护字段

Day 2：
  └─ 阶段 1.2 ~ 1.3：graph.py + tools.py + agent router + main.py 注册
      └─ 🔧 优化：graph.py 加内容审核节点 + 错误处理节点 + recursion_limit硬限制

Day 3：
  ├─ 阶段 2.1：hallucination_defense.py（集成到 check_confidence 节点）
  │   └─ 🔧 优化：动态降级阈值（每次-0.15，保底0.30）
  ├─ 阶段 2.2：citation_tracker.py（集成到 generate 节点）
  └─ 阶段 2.3：temporal_retriever.py（替换 vectorstore.search）

Day 4：
  ├─ 阶段 3：monitor 模块（health + cost）
  │   └─ 🔧 优化：多级告警阈值 + 飞书/钉钉/邮件告警通道
  ├─ 阶段 4：qa_service.py 升级
  │   └─ 🔧 优化：限流 + 超时 + 熔断 + 会话一致性 + 语义缓存
  └─ 阶段 5：Schema + 路由补齐

Day 5：
  ├─ 阶段 6：前端对接
  └─ 阶段 7：集成测试 + 灰度
      └─ 🔧 优化：死循环防护专项测试（6项） + 灰度回滚机制
```

---

## 八、Agent 死循环防护（三种典型循环及解法）

> Agent 工作流在运行时可能陷入无限循环，这是 LangGraph 项目中最常见的生产事故。
> 本节提前写入实施方案，在编码阶段直接落实，避免事后补丁。

### 8.1 三种典型死循环总览

| 循环类型 | 场景示例 | 危险程度 |
|----------|----------|----------|
| **工具选择循环** | Tool A 返回结果 → LLM 认为不够 → 再选 Tool A → 无限循环 | ⭐⭐⭐⭐⭐ 极高 |
| **条件判断循环** | 置信度 0.69 → 低于 0.7 → 重新检索 → 再次得到 0.69 → 无限循环 | ⭐⭐⭐⭐ 高 |
| **结果验证循环** | 生成回答 → 检查一致性 → 发现问题 → 重新生成 → 再次发现问题 → 无限循环 | ⭐⭐⭐ 中 |

### 8.2 工具选择循环 — 解法：双重限界

**核心问题**：Agent 在"继续调工具"这一步上永远做 YES 的判断，没有退出机制。

**解法 A：LangGraph 内置递归限制（硬上限，必须配）**

```python
# agent/graph.py
app = graph.compile(
    checkpointer=MemorySaver(),
    recursion_limit=15,   # ← 最大执行步数，超出抛 RecursionError
)
```

**解法 B：状态中的工具调用计数器**

```python
# agent/state.py — AgentState 新增
tool_call_count: int    # 工具调用总次数
last_search_query: str  # 上次检索关键词（去重用）

# agent/nodes.py — search_knowledge 节点
def search_knowledge(self, state: AgentState) -> dict:
    query = state["current_query"]
    # 去重：参数没变就不重复检索
    if query == state.get("last_search_query", ""):
        return {"route": "generate", "skip_search": True}
    result = self.temporal_retriever.retrieve(query, top_k=5)
    return {
        "search_results": result,
        "last_search_query": query,
        "tool_call_count": state.get("tool_call_count", 0) + 1,
    }
```

**解法 C：路由节点强制退出**

```python
# agent/nodes.py — route_query 节点
def route_query(self, state: AgentState) -> dict:
    if state.get("tool_call_count", 0) >= 3:
        return {"route": "generate", "forced_exit": True}
    # ... 正常路由逻辑
```

**推荐组合**：解法 A（硬上限）+ 解法 B（语义去重），覆盖 99% 场景。

### 8.3 条件判断循环 — 解法：阈值松弛 + 最大重试

**核心问题**：`置信度 < 阈值 → 重新检索 → 还是不够 → 再检索`，阈值静态且循环条件不收敛。

**解法 A：动态降级阈值（最关键）**

```python
# agent/hallucination_defense.py
def should_accept_result(
    self,
    query: str,
    confidence: float,
    results_count: int,
    has_citation: bool,
    retry_attempt: int = 0,      # ← 新增参数
) -> tuple[bool, str]:
    risk_level = self.classify_query(query)
    base_config = self.THRESHOLD_CONFIG[risk_level]

    # 每次重试降低 0.15，保底不低于 0.30
    threshold = max(0.30, base_config["min_confidence"] - retry_attempt * 0.15)
    min_results = max(1, base_config["min_results"] - retry_attempt)

    reasons = []
    if confidence < threshold:
        reasons.append(f"置信度{confidence:.2f} < 当前阈值{threshold}")
    if results_count < min_results:
        reasons.append(f"检索结果数{results_count} < 最低要求{min_results}")
    if base_config["require_citation"] and not has_citation:
        reasons.append("该类查询必须有引用来源")
    return (len(reasons) == 0, "; ".join(reasons))
```

**动态阈值变化表**：

| 重试次数 | high 阈值 | medium 阈值 | low 阈值 | 最小结果数 |
|----------|-----------|-------------|----------|------------|
| 0（首次） | 0.80 | 0.65 | 0.40 | 3 / 2 / 1 |
| 1 | 0.65 | 0.50 | 0.30 | 2 / 2 / 1 |
| 2 | 0.50 | 0.35 | 0.30 | 2 / 1 / 1 |
| 3+ | 0.30 | 0.30 | 0.30 | 1 / 1 / 1 |

**解法 B：最大重试次数 + 兜底降级回答**

```python
# agent/nodes.py — check_confidence 节点
MAX_RETRY = 3

def check_confidence(self, state: AgentState) -> dict:
    retry = state.get("retry_attempt", 0)
    accepted, reason = threshold_checker.should_accept_result(
        query=state["current_query"],
        confidence=state["confidence"],
        results_count=len(state["search_results"]),
        has_citation=bool(state["citations"]),
        retry_attempt=retry,
    )
    if not accepted:
        if retry >= self.MAX_RETRY:
            # 重试耗尽 → 降级回答（带警告），不拒答
            return {
                "should_refuse": False,
                "is_low_confidence": True,
                "retry_attempt": retry + 1,
            }
        return {
            "should_refuse": False,
            "should_retry": True,
            "retry_attempt": retry + 1,
        }
    return {"should_refuse": False, "should_retry": False}
```

**解法 C：重试时改写查询（扩大召回）**

```python
# 第二次检索时，用更宽泛的关键词
def search_knowledge(self, state: AgentState) -> dict:
    query = state["current_query"]
    retry = state.get("retry_attempt", 0)
    if retry > 0:
        # 去掉具体限定词，扩大检索范围
        query = self._broaden_query(query)
    # ... 检索逻辑
```

### 8.4 结果验证循环 — 解法：严重度分级 + 最大重生成

**核心问题**：`生成 → 发现一致性问题 → 重新生成 → 又有问题 → ...`，验证器永远发现问题。

**解法 A：严重度分级处理**

```python
# agent/nodes.py — check_consistency 节点只做标记
def check_consistency(self, state: AgentState) -> dict:
    is_consistent, issues = self.consistency_checker.check(...)
    high_issues = [i for i in issues if i.get("severity") == "high"]
    medium_issues = [i for i in issues if i.get("severity") == "medium"]
    return {
        "is_consistent": is_consistent,
        "consistency_issues": issues,
        "high_severity_count": len(high_issues),
        "medium_severity_count": len(medium_issues),
        # 只标记，路由节点决定策略
    }
```

**路由决策**：

```python
# graph.py — 条件边决策
MAX_REGENERATE = 2

def _post_generation_decision(self, state: AgentState) -> str:
    """生成后的条件分支：根据验证结果决定下一步"""
    regenerate_count = state.get("regenerate_count", 0)

    if state.get("high_severity_count", 0) > 0:
        if regenerate_count < self.MAX_REGENERATE:
            return "regenerate"   # 还有重试机会
        return "refuse"           # 重试耗尽 → 拒答 + 人工审核标记

    if state.get("medium_severity_count", 0) > 0:
        return "accept_with_warning"  # 接受，附加警告

    return "accept"                   # 没问题，直接通过
```

**解法 B：生成时注入修正信息**

```python
# agent/nodes.py — regenerate_with_hints 节点
def regenerate_with_hints(self, state: AgentState) -> dict:
    """带修正提示的重新生成"""
    query = state["current_query"]
    context = state["search_results"]

    # 构造修正提示
    hints = []
    for issue in state.get("consistency_issues", []):
        if issue.get("severity") == "high":
            hints.append(
                f"- 注意：关于'{issue['contradiction_type']}'，"
                f"之前回答与此矛盾，请修正。"
            )

    prompt = build_prompt(query, context)
    if hints:
        prompt += f"\n\n【修正提示】\n" + "\n".join(hints)

    response = llm_client.chat(prompt, system_prompt=SYSTEM_PROMPT)
    return {
        "response": response.content,
        "regenerate_count": state.get("regenerate_count", 0) + 1,
        "route": "regenerated",
    }
```

**解法 C：验证器降级（工程兜底）**

```python
# 当 LLM 不可用时，验证器不应阻塞流程
def check_consistency(self, state: AgentState) -> dict:
    try:
        is_consistent, issues = self.consistency_checker.check(...)
    except LLMTimeoutError:
        # 异步补检：非阻塞
        async_review_after_response(state["message_id"])
        return {"consistency_issues": [], "skipped": True}
    return {"consistency_issues": issues}
```

### 8.5 统一治理：在 graph.py 层面全部兜住

三种循环最干净的解决方式是在工作流图的**环路上统一加判断**，而不是分散在各个节点里。

**更新后的工作流图**：

```
START → route → [search | direct | refuse]
                    ↓
              search → check_confidence
                    ↓
         [generate | regenerate | refuse]
                    ↓
         check_consistency → verify_facts
                    ↓
              [accept | accept_with_warning | refuse]
                    ↓
                     END
```

```python
# agent/graph.py
def build(self) -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("route",               self.nodes.route_query)
    graph.add_node("search",              self.nodes.search_knowledge)
    graph.add_node("check_confidence",    self.nodes.check_confidence)
    graph.add_node("generate",            self.nodes.generate_response)
    graph.add_node("regenerate",          self.nodes.regenerate_with_hints)  # ← 新增
    graph.add_node("check_consistency",   self.nodes.check_consistency)
    graph.add_node("verify_facts",        self.nodes.verify_facts)
    graph.add_node("accept_with_warning", self.nodes.accept_with_warning)   # ← 新增
    graph.add_node("refuse",              self.nodes.generate_refusal)

    graph.add_edge(START, "route")

    # route 分支
    graph.add_conditional_edges(
        "route", self._route_decision,
        {"search": "search", "direct": END, "refuse": "refuse"},
    )

    # search → check_confidence
    graph.add_edge("search", "check_confidence")

    # check_confidence 三分支
    graph.add_conditional_edges(
        "check_confidence", self._confidence_decision,
        {
            "accept":     "generate",
            "regenerate": "regenerate",  # 降级阈值后再检索
            "refuse":     "refuse",
        },
    )

    # regenerate → generate（后续加跳转回 search 的逻辑）
    graph.add_edge("regenerate", "generate")

    # generate → check_consistency
    graph.add_edge("generate", "check_consistency")
    graph.add_edge("check_consistency", "verify_facts")

    # verify_facts → 最终决策
    graph.add_conditional_edges(
        "verify_facts", self._post_generation_decision,
        {
            "accept":              END,
            "accept_with_warning": "accept_with_warning",
            "refuse":              "refuse",
        },
    )

    graph.add_edge("accept_with_warning", END)
    graph.add_edge("refuse", END)

    self.graph = graph
    return graph
```

### 8.6 完整防护矩阵

| 循环类型 | 第一道防线 | 第二道防线 | 第三道防线 | 兜底 |
|----------|-----------|-----------|-----------|------|
| **工具选择循环** | 语义去重（相同查询不重复调用） | 工具调用计数器（≥3 强制退出） | LangGraph `recursion_limit=15` | 超限 → 兜底生成 + 标记 |
| **条件判断循环** | 动态放低阈值（每次 -0.15） | 最大重试次数（3 次） | 降级回答 + 低置信度警告 | 超限 → 拒答 + 建议联系老师 |
| **结果验证循环** | 严重度分级（只重试 high） | 最大重生成次数（2 次） | 注入修正提示 | 超限 → 拒答 + 标记人工审核 |

### 8.7 编码阶段落地检查清单

在实现各阶段时，对照以下清单确保死循环防护到位：

- [ ] `graph.py` 中 `compile()` 设置了 `recursion_limit`
- [ ] `state.py` 中 `AgentState` 含 `retry_attempt`、`tool_call_count`、`last_search_query`、`regenerate_count`
- [ ] `nodes.py` 中 `route_query` 在 `tool_call_count >= 3` 时强制生成
- [ ] `nodes.py` 中 `search_knowledge` 对相同查询做去重
- [ ] `hallucination_defense.py` 中 `should_accept_result` 接收 `retry_attempt` 并动态降级阈值
- [ ] `graph.py` 中条件分支支持 `regenerate` 路径
- [ ] `nodes.py` 中新增 `regenerate_with_hints` 和 `accept_with_warning` 节点
- [ ] 全链路测试通过（见下方 8.8）

### 8.8 死循环防护测试用例

```python
# 测试 1：工具选择循环防护
def test_tool_loop_protection():
    state = {"current_query": "落户政策", "tool_call_count": 3, ...}
    result = agent_nodes.route_query(state)
    assert result["route"] == "generate"        # 强制退出
    assert result["forced_exit"] is True

# 测试 2：条件判断循环防护
def test_confidence_loop_protection():
    for retry in range(4):
        accepted, _ = threshold_checker.should_accept_result(
            query="落户", confidence=0.69, results_count=2,
            has_citation=True, retry_attempt=retry,
        )
    assert accepted is True                      # 第 3 次后阈值降至 0.30，应当接受
    # 或：retry >= 3 时进入降级回答

# 测试 3：结果验证循环防护
def test_validation_loop_protection():
    state = {"regenerate_count": 2, "high_severity_count": 1, ...}
    decision = graph._post_generation_decision(state)
    assert decision == "refuse"                 # 重试耗尽 → 拒答

# 测试 4：recursion_limit 兜底
def test_recursion_limit():
    with pytest.raises(RecursionError):
        app = graph.compile(checkpointer=MemorySaver(), recursion_limit=5)
        app.invoke(broken_state)               # 永远循环的状态
```

---

## 八、Agent 死循环防护（三种典型循环及解法）

> Agent 工作流在运行时可能陷入无限循环，这是 LangGraph 项目中最常见的生产事故。
> 本节提前写入实施方案，在编码阶段直接落实，避免事后补丁。

### 8.1 三种典型死循环总览

| 循环类型 | 场景示例 | 危险程度 |
|----------|----------|----------|
| **工具选择循环** | Tool A 返回结果 → LLM 认为不够 → 再选 Tool A → 无限循环 | ⭐⭐⭐⭐⭐ 极高 |
| **条件判断循环** | 置信度 0.69 → 低于 0.7 → 重新检索 → 再次得到 0.69 → 无限循环 | ⭐⭐⭐⭐ 高 |
| **结果验证循环** | 生成回答 → 检查一致性 → 发现问题 → 重新生成 → 再次发现问题 → 无限循环 | ⭐⭐⭐ 中 |

### 8.2 工具选择循环 — 解法：双重限界

**核心问题**：Agent 在"继续调工具"这一步上永远做 YES 的判断，没有退出机制。

**解法 A：LangGraph 内置递归限制（硬上限，必须配）**

```python
# agent/graph.py
app = graph.compile(
    checkpointer=MemorySaver(),
    recursion_limit=15,   # ← 最大执行步数，超出抛 RecursionError
)
```

**解法 B：状态中的工具调用计数器**

```python
# agent/state.py — AgentState 新增
tool_call_count: int    # 工具调用总次数
last_search_query: str  # 上次检索关键词（去重用）

# agent/nodes.py — search_knowledge 节点
def search_knowledge(self, state: AgentState) -> dict:
    query = state["current_query"]
    # 去重：参数没变就不重复检索
    if query == state.get("last_search_query", ""):
        return {"route": "generate", "skip_search": True}
    result = self.temporal_retriever.retrieve(query, top_k=5)
    return {
        "search_results": result,
        "last_search_query": query,
        "tool_call_count": state.get("tool_call_count", 0) + 1,
    }
```

**解法 C：路由节点强制退出**

```python
# agent/nodes.py — route_query 节点
def route_query(self, state: AgentState) -> dict:
    if state.get("tool_call_count", 0) >= 3:
        return {"route": "generate", "forced_exit": True}
    # ... 正常路由逻辑
```

**推荐组合**：解法 A（硬上限）+ 解法 B（语义去重），覆盖 99% 场景。

### 8.3 条件判断循环 — 解法：阈值松弛 + 最大重试

**核心问题**：`置信度 < 阈值 → 重新检索 → 还是不够 → 再检索`，阈值静态且循环条件不收敛。

**解法 A：动态降级阈值（最关键）**

```python
# agent/hallucination_defense.py
def should_accept_result(
    self,
    query: str,
    confidence: float,
    results_count: int,
    has_citation: bool,
    retry_attempt: int = 0,      # ← 新增参数
) -> tuple[bool, str]:
    risk_level = self.classify_query(query)
    base_config = self.THRESHOLD_CONFIG[risk_level]

    # 每次重试降低 0.15，保底不低于 0.30
    threshold = max(0.30, base_config["min_confidence"] - retry_attempt * 0.15)
    min_results = max(1, base_config["min_results"] - retry_attempt)

    reasons = []
    if confidence < threshold:
        reasons.append(f"置信度{confidence:.2f} < 当前阈值{threshold}")
    if results_count < min_results:
        reasons.append(f"检索结果数{results_count} < 最低要求{min_results}")
    if base_config["require_citation"] and not has_citation:
        reasons.append("该类查询必须有引用来源")
    return (len(reasons) == 0, "; ".join(reasons))
```

**动态阈值变化表**：

| 重试次数 | high 阈值 | medium 阈值 | low 阈值 | 最小结果数 |
|----------|-----------|-------------|----------|------------|
| 0（首次） | 0.80 | 0.65 | 0.40 | 3 / 2 / 1 |
| 1 | 0.65 | 0.50 | 0.30 | 2 / 2 / 1 |
| 2 | 0.50 | 0.35 | 0.30 | 2 / 1 / 1 |
| 3+ | 0.30 | 0.30 | 0.30 | 1 / 1 / 1 |

**解法 B：最大重试次数 + 兜底降级回答**

```python
# agent/nodes.py — check_confidence 节点
MAX_RETRY = 3

def check_confidence(self, state: AgentState) -> dict:
    retry = state.get("retry_attempt", 0)
    accepted, reason = threshold_checker.should_accept_result(
        query=state["current_query"],
        confidence=state["confidence"],
        results_count=len(state["search_results"]),
        has_citation=bool(state["citations"]),
        retry_attempt=retry,
    )
    if not accepted:
        if retry >= self.MAX_RETRY:
            # 重试耗尽 → 降级回答（带警告），不拒答
            return {
                "should_refuse": False,
                "is_low_confidence": True,
                "retry_attempt": retry + 1,
            }
        return {
            "should_refuse": False,
            "should_retry": True,
            "retry_attempt": retry + 1,
        }
    return {"should_refuse": False, "should_retry": False}
```

**解法 C：重试时改写查询（扩大召回）**

```python
# 第二次检索时，用更宽泛的关键词
def search_knowledge(self, state: AgentState) -> dict:
    query = state["current_query"]
    retry = state.get("retry_attempt", 0)
    if retry > 0:
        # 去掉具体限定词，扩大检索范围
        query = self._broaden_query(query)
    # ... 检索逻辑
```

### 8.4 结果验证循环 — 解法：严重度分级 + 最大重生成

**核心问题**：`生成 → 发现一致性问题 → 重新生成 → 又有问题 → ...`，验证器永远发现问题。

**解法 A：严重度分级处理**

```python
# agent/nodes.py — check_consistency 节点只做标记
def check_consistency(self, state: AgentState) -> dict:
    is_consistent, issues = self.consistency_checker.check(...)
    high_issues = [i for i in issues if i.get("severity") == "high"]
    medium_issues = [i for i in issues if i.get("severity") == "medium"]
    return {
        "is_consistent": is_consistent,
        "consistency_issues": issues,
        "high_severity_count": len(high_issues),
        "medium_severity_count": len(medium_issues),
        # 只标记，路由节点决定策略
    }
```

**路由决策**：

```python
# graph.py — 条件边决策
MAX_REGENERATE = 2

def _post_generation_decision(self, state: AgentState) -> str:
    """生成后的条件分支：根据验证结果决定下一步"""
    regenerate_count = state.get("regenerate_count", 0)

    if state.get("high_severity_count", 0) > 0:
        if regenerate_count < self.MAX_REGENERATE:
            return "regenerate"   # 还有重试机会
        return "refuse"           # 重试耗尽 → 拒答 + 人工审核标记

    if state.get("medium_severity_count", 0) > 0:
        return "accept_with_warning"  # 接受，附加警告

    return "accept"                   # 没问题，直接通过
```

**解法 B：生成时注入修正信息**

```python
# agent/nodes.py — regenerate_with_hints 节点
def regenerate_with_hints(self, state: AgentState) -> dict:
    """带修正提示的重新生成"""
    query = state["current_query"]
    context = state["search_results"]

    # 构造修正提示
    hints = []
    for issue in state.get("consistency_issues", []):
        if issue.get("severity") == "high":
            hints.append(
                f"- 注意：关于'{issue['contradiction_type']}'，"
                f"之前回答与此矛盾，请修正。"
            )

    prompt = build_prompt(query, context)
    if hints:
        prompt += f"\n\n【修正提示】\n" + "\n".join(hints)

    response = llm_client.chat(prompt, system_prompt=SYSTEM_PROMPT)
    return {
        "response": response.content,
        "regenerate_count": state.get("regenerate_count", 0) + 1,
        "route": "regenerated",
    }
```

**解法 C：验证器降级（工程兜底）**

```python
# 当 LLM 不可用时，验证器不应阻塞流程
def check_consistency(self, state: AgentState) -> dict:
    try:
        is_consistent, issues = self.consistency_checker.check(...)
    except LLMTimeoutError:
        # 异步补检：非阻塞
        async_review_after_response(state["message_id"])
        return {"consistency_issues": [], "skipped": True}
    return {"consistency_issues": issues}
```

### 8.5 统一治理：在 graph.py 层面全部兜住

三种循环最干净的解决方式是在工作流图的**环路上统一加判断**，而不是分散在各个节点里。

**更新后的工作流图**：

```
START → route → [search | direct | refuse]
                    ↓
              search → check_confidence
                    ↓
         [generate | regenerate | refuse]
                    ↓
         check_consistency → verify_facts
                    ↓
              [accept | accept_with_warning | refuse]
                    ↓
                     END
```

```python
# agent/graph.py
def build(self) -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("route",               self.nodes.route_query)
    graph.add_node("search",              self.nodes.search_knowledge)
    graph.add_node("check_confidence",    self.nodes.check_confidence)
    graph.add_node("generate",            self.nodes.generate_response)
    graph.add_node("regenerate",          self.nodes.regenerate_with_hints)  # ← 新增
    graph.add_node("check_consistency",   self.nodes.check_consistency)
    graph.add_node("verify_facts",        self.nodes.verify_facts)
    graph.add_node("accept_with_warning", self.nodes.accept_with_warning)   # ← 新增
    graph.add_node("refuse",              self.nodes.generate_refusal)

    graph.add_edge(START, "route")

    # route 分支
    graph.add_conditional_edges(
        "route", self._route_decision,
        {"search": "search", "direct": END, "refuse": "refuse"},
    )

    # search → check_confidence
    graph.add_edge("search", "check_confidence")

    # check_confidence 三分支
    graph.add_conditional_edges(
        "check_confidence", self._confidence_decision,
        {
            "accept":     "generate",
            "regenerate": "regenerate",  # 降级阈值后再检索
            "refuse":     "refuse",
        },
    )

    # regenerate → generate（后续加跳转回 search 的逻辑）
    graph.add_edge("regenerate", "generate")

    # generate → check_consistency
    graph.add_edge("generate", "check_consistency")
    graph.add_edge("check_consistency", "verify_facts")

    # verify_facts → 最终决策
    graph.add_conditional_edges(
        "verify_facts", self._post_generation_decision,
        {
            "accept":              END,
            "accept_with_warning": "accept_with_warning",
            "refuse":              "refuse",
        },
    )

    graph.add_edge("accept_with_warning", END)
    graph.add_edge("refuse", END)

    self.graph = graph
    return graph
```

### 8.6 完整防护矩阵

| 循环类型 | 第一道防线 | 第二道防线 | 第三道防线 | 兜底 |
|----------|-----------|-----------|-----------|------|
| **工具选择循环** | 语义去重（相同查询不重复调用） | 工具调用计数器（≥3 强制退出） | LangGraph `recursion_limit=15` | 超限 → 兜底生成 + 标记 |
| **条件判断循环** | 动态放低阈值（每次 -0.15） | 最大重试次数（3 次） | 降级回答 + 低置信度警告 | 超限 → 拒答 + 建议联系老师 |
| **结果验证循环** | 严重度分级（只重试 high） | 最大重生成次数（2 次） | 注入修正提示 | 超限 → 拒答 + 标记人工审核 |

### 8.7 编码阶段落地检查清单

在实现各阶段时，对照以下清单确保死循环防护到位：

- [ ] `graph.py` 中 `compile()` 设置了 `recursion_limit`
- [ ] `state.py` 中 `AgentState` 含 `retry_attempt`、`tool_call_count`、`last_search_query`、`regenerate_count`
- [ ] `nodes.py` 中 `route_query` 在 `tool_call_count >= 3` 时强制生成
- [ ] `nodes.py` 中 `search_knowledge` 对相同查询做去重
- [ ] `hallucination_defense.py` 中 `should_accept_result` 接收 `retry_attempt` 并动态降级阈值
- [ ] `graph.py` 中条件分支支持 `regenerate` 路径
- [ ] `nodes.py` 中新增 `regenerate_with_hints` 和 `accept_with_warning` 节点
- [ ] 全链路测试通过（见下方 8.8）

### 8.8 死循环防护测试用例

```python
# 测试 1：工具选择循环防护
def test_tool_loop_protection():
    state = {"current_query": "落户政策", "tool_call_count": 3, ...}
    result = agent_nodes.route_query(state)
    assert result["route"] == "generate"        # 强制退出
    assert result["forced_exit"] is True

# 测试 2：条件判断循环防护
def test_confidence_loop_protection():
    for retry in range(4):
        accepted, _ = threshold_checker.should_accept_result(
            query="落户", confidence=0.69, results_count=2,
            has_citation=True, retry_attempt=retry,
        )
    assert accepted is True                      # 第 3 次后阈值降至 0.30，应当接受
    # 或：retry >= 3 时进入降级回答

# 测试 3：结果验证循环防护
def test_validation_loop_protection():
    state = {"regenerate_count": 2, "high_severity_count": 1, ...}
    decision = graph._post_generation_decision(state)
    assert decision == "refuse"                 # 重试耗尽 → 拒答

# 测试 4：recursion_limit 兜底
def test_recursion_limit():
    with pytest.raises(RecursionError):
        app = graph.compile(checkpointer=MemorySaver(), recursion_limit=5)
        app.invoke(broken_state)               # 永远循环的状态
```

---

## 九、回到设计文档的索引

以下场景请回到原始设计文档查阅详细代码：

| 需要查阅的场景 | 原始文档 | 章节 |
|---------------|----------|------|
| 动态置信度阈值规则 | Agent模块设计文档.md | §3.4 第四重 |
| 拒答机制模板 | Agent模块设计文档.md | §3.1 第三重 |
| 语义切分完整实现 | Agent模块设计文档.md | §3.5 |
| 健康度监控完整实现 | Agent模块设计文档.md | §3.6 |
| config.py 完整配置 | 功能模块实现文档.md | §3.3 |
| database.py 完整实现 | 功能模块实现文档.md | §3.4 |
| 迁移脚本 | 功能模块实现文档.md | §12.3 |
| 产品功能说明 | 产品介绍文档.md | 全文 |

---

## 十、优化点评审结论（2026-06-24）

> 本节对文档中全部优化点进行评审，给出「保留/简化/删除/后移」结论及原因。
> 评审依据：当前代码库实际状态（`rag_service.py` / `llm.py` / `config.py` / `qa.py` 等）。

### 10.1 保留的优化项

| 优化点 | 保留理由 | 实现注意 |
|--------|----------|----------|
| 死循环防护全套（计数器 + 动态阈值 + recursion_limit） | LangGraph 无防护必然卡死服务，P0 优先级 | 三循环都要写测试用例 |
| 动态降级阈值（每次 -0.15，保底 0.30） | 防条件判断循环的核心机制 |  |
| 检索去重（相同查询跳过） | 两行代码解决一个问题 |  |
| 内容审核节点（输出侧） | 与输入侧敏感词过滤形成双重防护 | 输出侧只做生成内容合规，不做手机号/邮箱匹配（那是输入侧的事） |
| Prompt 工程化（抽成独立文件） | 多节点 Prompt 硬编码在 nodes.py 会失控 | 见下方缺失项 3 |
| 语义缓存（Redis，相似度 0.92） | FAQ 类问题零 LLM 调用，成本降 30-50% | 复用现有 Redis，不引入新依赖 |
| 渐进式迁移（Agent 故障切回旧 RAG） | 旧 RAG 已稳定运行，Agent 上线初期必有 bug | 配置项开关 + 保留 `rag_service.ask()` 完整链路 |
| llm.py 加 HTTP 超时 | 当前无超时会 hang 住整个请求 | `timeout=30`，见下方缺失项 2 |

### 10.2 需要简化的优化项

| 优化点 | 简化方式 | 原因 |
|--------|----------|------|
| 可解释性 / 推理链 | V1 只记录 `route` / `confidence` / `tool_used` 三个核心字段 | 完整推理链是 V2 体验优化，不是 V1 功能性需求 |
| 统一错误处理节点 | 保留兜底返回友好提示 + 记录错误，**删除回滚逻辑** | 当前 RAG 场景无不可逆副作用，`partial_effects` 回滚是过度设计 |
| `accept_with_warning` 独立节点 | 合并进 `generate` 节点，用 `is_low_confidence` 标记 | 节点越少，图越简单，越不容易出 bug |
| 多通道告警 | V1 只做：写 `llm_cost_log` + 控制台告警 + 管理端可查 | 邮件/飞书/钉钉/短信需要运维体系支撑，V1 没有 |

### 10.3 建议删除的优化项

| 优化点 | 删除理由 |
|--------|----------|
| `partial_effects` 回滚机制 | 当前场景无不可逆副作用（无扣库存/转账等操作），过度设计 |
| 多设备会话同步 | 当前项目无多端 App，Web 端也无"同时登录多设备"需求，V2 再评估 |

### 10.4 文档中缺失但必须补充的优化项

#### 缺失项 1：Agent 路由层复用现有鉴权 + Agent 专属限流

新 `routers/agent.py` 必须复用 `get_current_user`，不能另写鉴权。Agent 工作流的 LLM 调用成本远高于普通 RAG，需在路由层加专属限流：

```python
# routers/agent.py 限流依赖示例
from fastapi import Depends, HTTPException, Request

async def agent_rate_limit(request: Request):
    """Agent 专属限流：每用户 10 次/分钟，全局 100 次/分钟"""
    user_id = request.state.user.id
    # 用 Redis 或内存计数器实现
    ...
```

#### 缺失项 2：llm.py 必须加 HTTP 超时

当前 `llm.py` 无超时配置，DashScope 超时会 hang 住整个请求：

```python
# 修改 llm.py 的 chat() 和 chat_stream()
def chat(messages: list[dict], temperature: float = 0.3) -> str:
    resp = _client().chat.completions.create(
        model=settings.llm_model,
        messages=messages,
        temperature=temperature,
        timeout=30,  # ← 必须加
    )
    return resp.choices[0].message.content or ""

def chat_stream(messages: list[dict], temperature: float = 0.3) -> Iterator[str]:
    stream = _client().chat.completions.create(
        model=settings.llm_model,
        messages=messages,
        temperature=temperature,
        stream=True,
        timeout=30,  # ← 必须加
    )
```

#### 缺失项 3：Prompt 工程化 — 抽成独立文件

多节点 Prompt 硬编码在 `nodes.py` 会失控，建议结构：

```
backend/app/agent/prompts/
  __init__.py
  router.py       # 路由决策 prompt
  generator.py    # 回答生成 prompt
  regenerator.py  # 带修正提示的重新生成 prompt
  refusal.py      # 拒答生成 prompt
```

#### 缺失项 4：SentenceLevelCitationTracker 的工程现实

文档要求"每句话做 Embedding + LLM 验证"，一个回答 5-8 句话意味着 10+ 次额外 LLM 调用，响应时间翻倍。

**V1 简化方案**：只对"置信度在边界附近"的回答做引用验证，或者只做"整段回答是否被引用支持"的一元判断。

#### 缺失项 5：LangGraph Checkpoint 必须持久化

文档中使用 `MemorySaver()`，服务重启后对话上下文全部丢失。必须替换为持久化存储：

```python
# agent/graph.py — 使用 SqliteSaver 或 PostgresSaver
from langgraph.checkpoint.sqlite import SqliteSaver
# 或
from langgraph.checkpoint.postgres import PostgresSaver

memory = SqliteSaver("./agent_checkpoints.db")
# 或复用现有 MySQL
# memory = PostgresSaver(settings.database_url)
```

#### 缺失项 6：流式响应的兼容性问题

当前 `rag_service.py` 的 `ask_stream()` 是逐 token 产出 SSE。Agent 工作流是**非流式的状态机**，多个节点串行调用 LLM，天然不适合直接套进 SSE。

**V1 方案**：Agent 对话走**同步接口**，等全流程跑完一次性返回。前端用 loading 动画。V2 再做流式桥接。

文档中的 `/chat/stream` 路由建议标注为「V2 支持」。

#### 缺失项 7：渐进式迁移路径

新 Agent 工作流不应直接替换旧 RAG，而应做渐进式切换：

```
ask() 入口加一层判断：
  if agent_enabled and not circuit_breaker.is_open():
      return agent_workflow.run()    # 新 Agent
  else:
      return legacy_rag.ask()        # 旧 RAG（已稳定运行）
```

实现方式：`config.py` 加 `agent_enabled: bool = False`（V1 默认关闭，灰度时开启）。

### 10.5 最终优先级建议

| 优先级 | 内容 | 说明 |
|--------|------|------|
| **P0** | 死循环防护全套 | 不做跑不起来 |
| **P0** | 基础 LangGraph 工作流 | route → search → generate → refuse |
| **P0** | llm.py 加 HTTP 超时 | 不然后端会 hang |
| **P0** | 渐进式迁移开关 | 旧 RAG 作为兜底 |
| **P1** | 动态置信度阈值 | 防条件循环核心 |
| **P1** | Prompt 工程化 | 多节点 Prompt 管理 |
| **P1** | Checkpoint 持久化 | 不要用 MemorySaver |
| **P1** | 限流 + 简单熔断 | Agent 专属限流 |
| **P1** | 语义缓存 | 高 ROI |
| **V2** | 完整推理链展示 | 前端体验优化 |
| **V2** | 流式 Agent 响应 | 工程复杂度高 |
| **V2** | 句子级引用验证 | 成本高，V1 简化 |
| **V2** | 多设备会话同步 | 当前无需求 |

---

**文档结束**
