# 多智能体架构设计文档

> **作用**：说明何时需要从单智能体升级到多智能体，以及 V4.0 的多智能体架构设计方案
> **前置阅读**：[Agent模块设计文档](../Agent模块设计文档.md) · [实施步骤总览](./implementation-steps.md) · [前端缺失页面待办清单](./missing-frontend-pages.md)

---

## 目录

- [当前架构回顾](#当前架构回顾)
- [单智能体 vs 多智能体决策矩阵](#单智能体-vs-多智能体决策矩阵)
- [单智能体可实现的全部功能（当前方案）](#单智能体可实现的全部功能当前方案)
- [需要多智能体的模块](#需要多智能体的模块)
- [V4.0 多智能体架构设计](#v40-多智能体架构设计)
- [实施路径建议](#实施路径建议)

---

## 当前架构回顾

### 现有单 Agent 工作流

```
route_query（意图分类）
    ├── kb_query      → search_knowledge → check_confidence → generate_response
    ├── job_query     → search_knowledge(check_confidence) → generate_with_hints
    └── web_query     → search_knowledge(no local) → bing_search → generate

统一防御层：
    ├── check_consistency（一致性检查）
    ├── verify_facts（事实核验）
    ├── content_moderation（内容审核）
    ├── generate_refusal / accept_with_warning（拒答/带警告接受）
    └── DynamicConfidenceThreshold（动态置信度阈值）
```

### 单 Agent 的能力边界

| 能力 | 当前实现 | 说明 |
|------|----------|------|
| 意图识别 | ✅ 3 类（kb_query / job_query / web_query） | `route_query` 节点 |
| 知识库检索 | ✅ ChromaDB + 时效过滤 | `search_knowledge` 节点 |
| 网页兜底 | ✅ Bing MCP + 站点白名单 | Phase 7 实现 |
| 引用溯源 | ✅ chunk 级引用 + 质量评估 | `citation_tracker.py` |
| 幻觉防御 | ✅ 5 层防御 | `hallucination_defense.py` |
| 拒答处理 | ✅ 6 个模板 | `refusal_handler.py` |
| 会话管理 | ✅ 多轮对话 + 历史传递 | `resolve_conversation()` |
| 监控告警 | ✅ 3 个监控器 + 4 个定时任务 | `monitor/` |

---

## 单智能体 vs 多智能体决策矩阵

| 判断维度 | 当前单 Agent | 多智能体 |
|----------|-------------|---------|
| **业务域重叠度** | 高：所有场景都是"检索+生成" | 需隔离的独立业务域才需要拆 |
| **工具共享** | 高：RAG、LLM、缓存全部共用 | 拆分会增加重复开发 |
| **状态隔离需求** | 低：扁平 AgentState 足够 | 需隔离的上下文才需要拆 |
| **Prompt 差异** | 小：通用提示词覆盖所有场景 | 需要完全不同提示词策略时再拆 |
| **执行流程差异** | 小：检索→生成→防御是通用流程 | 有独立子流程（如简历生成链）时拆 |
| **运维复杂度** | 低：单图调试简单 | 高：多图协调增加调试成本 |
| **团队规模** | 小型团队 | 多团队并行开发才需要拆 |

### 决策结论

| 需要多智能体的信号 | 当前是否触发 | 说明 |
|-------------------|-------------|------|
| 出现 3+ 个独立子流程 | ❌ 未触发 | 当前 12 节点是单流程 |
| Agent 间需要状态隔离 | ❌ 未触发 | 扁平结构足够 |
| 不同 Agent 需要不同模型 | ❌ 未触发 | 全部用 qwen 系列 |
| 工具数量 > 8 个 | ❌ 未触发 | 当前 3 个工具（search、bing、fetch） |
| 单 Prompt 超过 4k tokens | ❌ 未触发 | 当前提示词精简 |

---

## 单智能体可实现的全部功能（当前方案）

> 以下功能均可在**当前单 Agent + 工具扩展**的方案下实现，无需引入多智能体架构。

### 单 Agent 工具扩展清单

通过在 `agent/tools.py` 中新增工具函数，可以低成本扩展 Agent 能力：

| 新工具 | 对应前端页面 | 实现方式 | 复杂度 |
|--------|-------------|----------|--------|
| `generate_resume()` | 简历助手 | LLM 链式调用：生成 → 优化 → 排版 | 中 |
| `recommend_jobs()` | 职位推荐 | RAG + 向量匹配 + 规则过滤 | 中 |
| `add_calendar_event()` | 面试日程 | 调用日程 API，生成 ICS | 低 |
| `toggle_faq_status()` | FAQ 管理 | 直接调用后端 API | 低 |
| `batch_operation()` | 批量操作 | 封装批量 API 调用 | 低 |
| `fetch_announcement()` | 公告展示 | 读取公告表 | 低 |

### 意图分流扩展

`route_query` 的 3 类意图可以进一步细化：

| 当前意图 | 可扩展子意图 | 说明 |
|----------|-------------|------|
| `kb_query` | `policy_query` / `faq_query` / `document_query` | 知识库内部细分 |
| `job_query` | `resume_query` / `interview_query` / `salary_query` | 求职相关细分 |
| `web_query` | `news_query` / `policy_web_query` | 网页检索细分 |

### 渐进式扩展路径

```
Phase 7 完成（当前）
└── 单 Agent，3 个意图，3 个工具

V2 阶段（新增 3-5 个工具）
├── tools.py 新增：generate_resume / recommend_jobs / add_calendar_event
├── route_query 意图扩展为 6 类
├── AgentState 增加 resume_data / job_recommendations / calendar_events 字段
└── nodes.py 新增处理节点（如 render_resume / render_calendar）

V3 评估点（工具 > 8 个 或 Prompt > 4k）
└── 评估是否拆分为 subgraph
```

### 适用边界：什么时候单 Agent 就够了

```
✅ 单 Agent 够用的场景：
├── 业务逻辑是"检索+生成"的变体（问答、对话、检索、摘要）
├── 工具之间共享上下文（用户对话历史）
├── 防御逻辑统一（一致性、事实核验、拒答）
├── 响应格式相对一致（引用卡片 + 文本回答）
└── 团队规模 < 5 人

❌ 需要多 Agent 的场景：
├── 业务流程需要"等待外部事件"（如用户审批后才继续）
├── Agent 间需要严格的权限隔离（如求职 Agent 不能访问对话历史）
├── 不同 Agent 需要独立的记忆/状态管理
├── 执行流程差异极大（如简历生成是 5 步链式编排）
└── 需要多 Agent 协作解决复杂任务（如同时检索政策+职位+企业）
```

---

## 需要多智能体的模块

> 当前单 Agent 方案**不能低成本实现**以下功能，需要多智能体架构支持。

### 触发条件分析

对照 `docs/前端实施方案.md` 的 Phase 4 + Phase 5 模块：

| 模块 | 单 Agent 可行性 | 不适用原因 | 建议架构 |
|------|----------------|-----------|----------|
| 系统设置 | ✅ 可行 | 纯 CRUD，无需 Agent | 直接前端 + REST API |
| 我的收藏 | ✅ 可行 | 纯 CRUD，无需 Agent | 直接前端 + REST API |
| 公告管理 | ✅ 可行 | 纯 CRUD，无需 Agent | 直接前端 + REST API |
| 统计分析 | ✅ 可行 | 聚合查询，无需 Agent | 直接前端 + REST API |
| 智能问答配置 | ✅ 可行 | 配置读写，无需 Agent | 直接前端 + REST API |
| 学生管理 | ✅ 可行 | 纯 CRUD，无需 Agent | 直接前端 + REST API |
| **简历助手** | ⚠️ 边界 | 多步链式生成需要独立流程 | 见下方分析 |
| **就业数据** | ⚠️ 边界 | 复杂聚合 + 外部数据源 | 见下方分析 |
| 企业管理 | ✅ 可行 | 纯 CRUD | 直接前端 + REST API |
| 职位推荐 | ⚠️ 边界 | 推荐算法独立 | 见下方分析 |
| 招聘会管理 | ✅ 可行 | 报名/签到流程可工具化 | 直接前端 + REST API |
| 面试日程 | ✅ 可行 | 日历操作可工具化 | 直接前端 + REST API |
| 帮助中心 | ✅ 可行 | 复用 FAQ + 文档 | 直接前端 + REST API |

### 边界模块详细分析

#### 简历助手：单 Agent 可扩展，但 subgraph 更清晰

**单 Agent 方案**：
```
工具调用链：
generate_resume(context) → LLM 生成
optimize_resume(context) → LLM 优化
render_template(data, template) → 模板渲染
```
- 优点：复用同一个对话上下文，用户可以在生成过程中随时修改
- 缺点：`generate_response` 节点变复杂，的一次 `invoke` 中串行调用 3+ 次 LLM，超时风险增加

**多 Agent（subgraph）方案**：
```
Coordinator
    ↓ intent=resume
ResumeSubgraph
    ├── parse_user_profile（解析用户档案）
    ├── generate_content（生成简历内容）
    ├── optimize_content（优化措辞）
    ├── render_template（模板渲染）
    └── output_resume（输出结果）
```
- 优点：ResumeSubgraph 有独立的状态（生成进度、中间结果、模板选择），出错可单独重试
- 缺点：实现复杂度显著增加

**推荐**：先用单 Agent + 工具链跑通 MVP，如果一次生成耗时超过 15 秒或需要"生成-预览-修改"的多轮交互，再拆 subgraph。

#### 职位推荐：单 Agent 足够

- 职位推荐本质是"向量匹配 + 规则过滤"，和知识库检索是同构的
- 可以新增 `recommend_jobs` 工具：调用 RAG 检索 + 按薪资/地点/行业过滤 + 排序
- 不需要独立 Agent

#### 就业数据：不需要 Agent

- 就业数据是后台数据聚合 + 报表，不需要对话交互
- 后端直接做聚合查询，前端展示图表即可

---

## V4.0 多智能体架构设计

> **触发条件**：当进入 Phase 5（复杂业务域）且满足以下任一条件时启动：
> 1. 简历助手需要多轮"生成→预览→修改"独立流程
> 2. 系统需要同时支持"求职"和"问答"两个独立会话上下文
> 3. Agent 工具超过 8 个导致单 Prompt 超过 4k tokens

### 4.1 架构总览

```
┌─────────────────────────────────────────────────────────────┐
│                    LangGraph Supervisor                       │
│                    （协调智能体）                              │
│ 职责：意图分类 → 委派给对应 SubAgent → 合并结果 → 返回用户     │
└──────┬──────────────┬──────────────┬────────────────────────┘
       │              │              │
       ▼              ▼              ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ 问答 Subgraph│ │ 求职 Subgraph│ │ 运营 Subgraph│
│ (QAAgent)   │ │ (JobAgent)   │ │ (OpsAgent)   │
├─────────────┤ ├─────────────┤ ├─────────────┤
│ 12 节点     │ │ 简历生成流程  │ │ 工具调用流程  │
│ (沿用现有)   │ │ 职位匹配流程  │ │ (复用 QA)    │
│             │ │ 面试日程流程  │ │              │
└─────────────┘ └─────────────┘ └─────────────┘
```

### 4.2 各智能体职责

#### 问答智能体（QAAgent）— 沿用现有

| 项目 | 内容 |
|------|------|
| **节点数** | 12（现有 graph.py） |
| **状态** | `AgentState` 完整继承 |
| **工具** | `knowledge_search` / `bing_search` / `fetch_webpage` |
| **防御** | 完整五层防御 |
| **前端页面** | ChatView / 会话历史 / 纯检索 |

#### 求职智能体（JobAgent）— 新增

| 项目 | 内容 |
|------|------|
| **节点数** | 6-8 |
| **状态** | `JobAgentState`（继承 `AgentState`，增加 `resume_data` / `job_recommendations` / `interview_events`） |
| **工具** | `search_knowledge`（职位类）/ `recommend_jobs` / `generate_resume` / `add_calendar_event` |
| **防御** | 复用 `DynamicConfidenceThreshold` + 简化版 `content_moderation` |
| **前端页面** | 简历助手 / 职位推荐 / 面试日程 |

**JobAgent 工作流**：
```
route_intent
    ├── intent=resume → parse_profile → generate_resume → optimize → render → output
    ├── intent=job_recommend → search_jobs → match_profile → rank → output
    └── intent=interview → search_events → add_calendar → output
```

#### 运营智能体（OpsAgent）— 最简实现

| 项目 | 内容 |
|------|------|
| **定位** | 不是对话型 Agent，是工具的封装层 |
| **实现方式** | 直接用 FastAPI 路由 + 工具函数，不需要 LangGraph |
| **前端页面** | 文档管理 / 分类管理 / 公告管理 / 系统设置 / 学生管理 |

**推荐实现**：运营类功能直接用 RESTful API，不需要 Agent 工作流。Agent 架构只用于对话型场景。

### 4.3 Agent 间通信设计

| 数据 | 共享方式 | 说明 |
|------|----------|------|
| `user_id` | 通过 `config` 传递 | LangGraph `config["configurable"]["user_id"]` |
| 对话历史 | Supervisor 中转 | QAAgent 返回摘要 → JobAgent 可读取用户档案但不读取对话内容 |
| 用户档案 | 共享 `UserProfile` | `user_service.get_profile(user_id)` 各 Agent 可读取 |
| 会话隔离 | 不同的 `thread_id` | QAAgent 和 JobAgent 有独立的 checkpoint 命名空间 |

### 4.4 状态隔离策略

```python
# AgentState 基础字段（共享）
class BaseAgentState(TypedDict):
    user_id: str
    request_id: str
    current_query: str
    # ... 通用追踪字段

# QAAgent 扩展
class QAAgentState(BaseAgentState):
    search_results: list
    citations: list
    confidence: float
    # ... 问答相关

# JobAgent 扩展
class JobAgentState(BaseAgentState):
    resume_data: dict
    job_recommendations: list
    interview_events: list
    # ... 求职相关
```

### 4.5 前端路由映射

| URL | 对应 Agent | 说明 |
|-----|-----------|------|
| `/chat` | QAAgent | 现有 ChatView |
| `/chat/resume` | JobAgent | 简历助手 |
| `/jobs` | JobAgent | 职位推荐 |
| `/chat/interviews` | JobAgent | 面试日程 |
| `/admin/*` | OpsAgent（REST） | 管理端页面 |

前端通过 `/api/v1/agent/chat?agent_type=qa|job` 区分调用的 Agent 类型。

---

## 实施路径建议

### 路径 A：保持单 Agent（推荐，近期）

```
Phase 8：生产部署
    ├── 前端缺失页面补齐（missing-frontend-pages.md）
    ├── 单 Agent 工具扩展（新增 resume / recommend 工具）
    ├── route_query 意图扩展（6 类）
    └── 监控和性能优化

适用条件：团队 < 5 人，业务还在快速迭代中
```

### 路径 B：引入 subgraph（中期，简历助手上线前评估）

```
Phase 9：JobAgent Subgraph 引入
    ├── 将简历生成流程独立为 ResumeSubgraph
    ├── 将职位推荐流程独立为 RecommendationSubgraph
    ├── QAAgent 保持不变
    ├── Supervisor 路由到对应 Subgraph
    └── 共享 UserProfile 服务

触发条件：
    - 简历助手需要独立的"生成→预览→修改"流程
    - 单 Agent 超时（>30s）成为用户体验瓶颈
    - 求职功能的 Prompt 和防御逻辑与问答差异显著
```

### 路径 C：全多 Agent（远期，不考虑）

```
仅在以下全部满足时考虑：
    - 团队 > 10 人
    - 各业务域有独立的产品/技术负责人
    - 需要 7×24 运行且各 Agent 独立扩缩容
    - 不同 Agent 需要完全不同的模型/提示词策略
否则，路径 B 的 subgraph 方案已经是足够的抽象。
```

### 建议的决策检查点

| 检查点 | 时间 | 评估内容 | 决策 |
|--------|------|----------|------|
| **Checkpoint 1** | 补齐前端页面后 | 当前单 Agent 是否稳定？工具数 < 8？ | 继续单 Agent |
| **Checkpoint 2** | 做简历助手前 | 生成流程是否需要 3+ 步链式编排？ | 是 → 引入 ResumeSubgraph |
| **Checkpoint 3** | 做职位推荐前 | 推荐逻辑是否需要独立状态？ | 否 → 单 Agent + 工具 |
| **Checkpoint 4** | V4.0 设计评审 | 是否有需要隔离的上下文？ | 是 → 引入 Supervisor |

---

## 附录：单智能体工具扩展示例

### `generate_resume` 工具设计

```python
@tool("generate_resume", description="根据用户档案和目标岗位生成简历")
def generate_resume(
    user_id: str,
    target_job: str,
    template_id: str = "default",
) -> dict:
    """单 Agent 内通过工具链实现简历生成"""
    profile = get_user_profile(user_id)
    job_description = search_knowledge(f"职位要求 {target_job}")

    # 第一步：生成内容
    content_prompt = f"""根据以下用户档案和目标岗位要求，生成简历内容：
    用户档案：{profile}
    目标岗位：{job_description}
    要求：突出匹配 Skills 和经历"""
    resume_content = llm.chat(content_prompt)

    # 第二步：优化措辞
    optimized = llm.chat(f"优化以下简历措辞：{resume_content}")

    # 第三步：渲染模板
    rendered = render_resume_template(optimized, template_id)

    return {
        "resume_content": optimized,
        "rendered_html": rendered,
        "template_id": template_id,
    }
```

**这种方式的问题**：
- 三次 LLM 调用在一次 `invoke` 中串行执行，耗时长
- 中间结果不能中断
- 出错后整个 invocation 重试，浪费 token

**用 Subgraph 解决**：
- ResumeSubgraph 有自己的 checkpoint，生成中间结果可持久化
- 用户可以先预览 → 提出修改意见 → Subgraph 从中间状态继续
- 出错只重试当前节点，不需要重跑全部 12 节点

---

## 附录：LangGraph Subgraph 实现要点

如果后续需要引入 subgraph，核心实现模式如下：

```python
# 1. 定义子图的 State
from langgraph.graph import StateGraph

class ResumeState(AgentState):
    resume_content: str
    profile: dict
    template_id: str
    rendered_html: str

# 2. 构建子图
resume_builder = StateGraph(ResumeState)
resume_builder.add_node("parse_profile", parse_profile_node)
resume_builder.add_node("generate_content", generate_content_node)
resume_builder.add_node("optimize", optimize_node)
resume_builder.add_node("render", render_node)
resume_builder.add_edge("parse_profile", "generate_content")
resume_builder.add_edge("generate_content", "optimize")
resume_builder.add_edge("optimize", "render")
resume_graph = resume_builder.compile(checkpointer=SqliteSaver())

# 3. 在主图中作为节点调用
main_graph.add_node("resume_agent", resume_graph)
# 或使用 send() 动态委派
```

### LangGraph 版本要求

| 版本 | subgraph 支持 | 本项目的兼容性 |
|------|--------------|---------------|
| 1.2.x（当前） | ✅ 基本支持 | 兼容 |
| 1.3+ | ✅ `send()` API 改进 | 升级后使用 |
| 1.4+ | ✅ `interrupt()` 支持 | 用于用户审批节点 |

---

**阶段 10 评估结果（2026-06-27）**：5 项检查点全部未触发，当前阶段**无需引入** Supervisor + Subgraph，继续使用单 Agent 架构。详见 [阶段 10 评估报告](../progress/phase-10.md)。

---

## 目录
