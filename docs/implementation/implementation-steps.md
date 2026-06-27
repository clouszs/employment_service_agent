# 实施步骤总览

> **作用**：将各阶段实施文档中的操作步骤，按模块化、工程化思维整理为结构化实施清单
> **前置阅读**：[Agent模块设计文档](../Agent模块设计文档.md) · [实施指南总览](./README.md)

---

## 目录

- [模块架构全景](#模块架构全景)
- [阶段 0：基础设施层](#阶段-0基础设施层)
- [阶段 1：Agent 核心层](#阶段-1agent-核心层)
- [阶段 2：幻觉防御层](#阶段-2幻觉防御层)
- [阶段 3：监控告警层](#阶段-3监控告警层)
- [阶段 4：服务接入层](#阶段-4服务接入层)
- [阶段 5：接口规范层](#阶段-5接口规范层)
- [阶段 6：前端展示层](#阶段-6前端展示层)
- [阶段 7：外部扩展层](#阶段-7外部扩展层)
- [模块依赖关系图](#模块依赖关系图)
- [增量优化项](#增量优化项)
- [单智能体扩展能力说明](#单智能体扩展能力说明)
- [何时需要升级为多智能体](#何时需要升级为多智能体)
- [单智能体扩展能力说明](#单智能体扩展能力说明)

---

## 模块架构全景

```
┌─────────────────────────────────────────────────────────┐
│                    前端展示层 (Phase 6)                    │
│          Vue 3 SPA · 三栏布局 · Agent 组件              │
├─────────────────────────────────────────────────────────┤
│              外部扩展层 (Phase 7)                          │
│           Bing MCP Fallback · 站点白名单路由               │
├─────────────────────────────────────────────────────────┤
│              接口规范层 (Phase 5)                          │
│     schemas · routers(kb_health/llm_cost/refusal)        │
├─────────────────────────────────────────────────────────┤
│              服务接入层 (Phase 4)                          │
│     qa_service.agent_chat() · /ask/agent 端点            │
├─────────────────────────────────────────────────────────┤
│              监控告警层 (Phase 3)                         │
│     KB 健康度 · LLM 成本 · 引用质量评估 · APScheduler    │
├─────────────────────────────────────────────────────────┤
│              幻觉防御层 (Phase 2)                         │
│     动态阈值 · 一致性 · 事实核验 · 拒答模板 · 引用追踪    │
├─────────────────────────────────────────────────────────┤
│              Agent 核心层 (Phase 1)                       │
│     LangGraph 状态机 · 12 节点 · SqliteSaver · 语义缓存   │
├─────────────────────────────────────────────────────────┤
│              基础设施层 (Phase 0)                         │
│     24 表 · Embedding 三级缓存 · LangSmith · Docker      │
└─────────────────────────────────────────────────────────┘
```

| 层级 | 阶段 | 核心产出 | 依赖下层 |
|------|------|----------|----------|
| 基础设施层 | Phase 0 | 24 张数据库表 / 三级缓存 / LangSmith / Docker | — |
| Agent 核心层 | Phase 1 | LangGraph 12 节点工作流 / SqliteSaver / 语义缓存 | 基础设施层 |
| 幻觉防御层 | Phase 2 | 五层防御机制 / 拒答模板 / 引用追踪 / 时效检索 | Agent 核心层 |
| 监控告警层 | Phase 3 | KB 健康度 / LLM 成本 / 引用质量 / 定时任务 | 幻觉防御层 + 模型层 |
| 服务接入层 | Phase 4 | `agent_chat()` 集成 / `/ask/agent` 端点 | Agent 核心层 |
| 接口规范层 | Phase 5 | Schema 抽离 / 3 个监控路由 / 响应对齐 | 监控告警层 |
| 前端展示层 | Phase 6 | Vue 3 SPA / 三栏布局 / Agent 组件 / 监控中心 | 服务接入层 + 接口规范层 |
| 外部扩展层 | Phase 7 | Bing MCP Fallback / 站点白名单 / web 引用卡片 | Agent 核心层 + 前端展示层 |
## 阶段 11：复杂业务域开发（2026-06-27 启动）

> **目标**：补齐 P2 前端页面 + P3 新领域模型，完成"高校智慧就业服务平台"的核心业务闭环
> **前置条件**：阶段 9-10 完成（单智能体扩展 + 多智能体评估）
> **架构决策**：单 Agent + REST API 层，不引入多智能体

### 11.1 Batch A：我的收藏 + 公告管理 ✅ 已完成

| 模块 | 后端文件 | 前端文件 | 路由 | 提交 |
|------|----------|----------|------|------|
| UserFavorite | `models/user_favorite.py`, `routers/user_favorite.py`, `services/user_favorite_service.py`, `schemas/user_favorite.py` | `api/favorites.ts`, `views/chat/FavoritesView.vue`, `types/favorites.ts` | `/chat/favorites` (requireAuth) | `ea020dd` |
| Announcement | `models/announcement.py`, `routers/announcements.py`, `services/announcement_service.py`, `schemas/announcement.py` | `api/announcements.ts`, `views/admin/AnnouncementsView.vue`, `types/announcements.ts` | `/admin/announcements` (requireAdmin) | `ea020dd` |
| AppConfig | `models/app_config.py`, `routers/app_config.py`, `services/app_config_service.py`, `schemas/app_config.py` | — | — | `ea020dd` |

**功能实现：**

| 页面 | 核心功能 |
|------|----------|
| 我的收藏 | 分页列表 + 消息摘要反查 + 跳转原会话 + 备注弹窗(加/编辑) + 删除 |
| 公告 Banner | ChatView 折叠展示 + 优先级色标(高🔴/中🟡/低⚪) + 静默降级(接口异常不影响主功能) |
| 公告管理 | 完整 CRUD + 搜索过滤(标题/状态) + 优先级色标 + 发布/撤下/草稿状态 + 分页 |

**Router 注册：** `backend/app/main.py` 已挂载 `app_config`、`user_favorite`、`announcements` 三个 router。

### 11.2 Batch B：系统设置（Day 1 完成）+ 智能问答配置（Day 2 完成）+ 对话管理 🔄 进行中

| 页面 | 路由 | 后端 API | 工作量 | 状态 |
|------|------|----------|--------|------|
| 系统设置 | `/admin/settings` | AppConfig CRUD ✅（复用 `/app-configs`） | ~1 天 | ✅ Day 1 完成 |
| 智能问答配置 | `/admin/qa-config` | 复用 AppConfig（qa_ 前缀）✅ | ~1 天 | ✅ Day 2 完成 |
| 对话管理 | `/admin/conversations` | 需后端扩展 | ~2-4 天 | ⏸️ 待后端就绪 |

**系统设置页（Day 1）实现说明：**

| 功能 | 实现 |
|------|------|
| 分组 Tab | 4 个预设分组（系统基础 / 智能问答 / 检索参数 / 其他） |
| 行内编辑 | 双击非敏感配置项进入编辑模式，Enter / 失焦提交 |
| 敏感配置 | 掩码展示（`******`）+ 锁图标，禁止编辑 |
| 统一保存 | "保存全部修改"按钮，收集 dirty 行逐个 PUT /app-configs/{id} |
| 放弃修改 | "放弃修改"按钮，回滚到加载时快照 |
| 操作提示 | 未保存项数量提示（dirtyCount） |

**前端文件清单：**

| 文件 | 说明 |
|------|------|
| `frontend/src/api/app-configs.ts` | AppConfig API 模块（list / update / toggle） |
| `frontend/src/types/app-configs.ts` | `AppConfigItem` + `ConfigGroup` + `ConfigEditRow` |
| `frontend/src/views/admin/SettingsView.vue` | 分组 Tab + 行内编辑 + 统一保存 |
| `frontend/src/router/index.ts` | 注册 `/admin/settings` 路由 |
| `frontend/src/views/admin/AdminLayout.vue` | 侧边栏新增「系统设置」菜单 |

**智能问答配置页（Day 2）实现说明：**

| 功能 | 实现 |
|------|------|
| 数据过滤 | 前端只展示 `config_key` 以 `qa_` 前缀开头的配置项 |
| 分组 Tab | 4 个 QA 专属分组：问答策略 / 检索参数 / 模型配置 / 其他 |
| 行内编辑 | 同系统设置页，双击非敏感配置项进入编辑模式 |
| 统一保存 | 同系统设置页，收集 dirty 行逐个 PUT /app-configs/{id} |
| 空状态提示 | 无 qa_ 配置时展示引导文字 |

**Day 2 新增前端文件：**

| 文件 | 说明 |
|------|------|
| `frontend/src/views/admin/QaConfigView.vue` | QA 专属设置页，复用 SettingsView 交互模式 |
| `frontend/src/router/index.ts` | 补充注册 `/admin/qa-config` 路由 |
| `frontend/src/views/admin/AdminLayout.vue` | 侧边栏新增「智能问答配置」菜单 |

**后端待扩展：**

| 端点 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 管理端会话列表 | GET | `/api/v1/admin/conversations` | 跨用户查询 + 分页 + 筛选 |
| 管理端强制删除 | DELETE | `/api/v1/admin/conversations/{id}` | 管理员强制删除任意会话 |

### 11.3 Batch C：新领域模型 ⏸️ 待规划

| 模块 | 复杂度 | 说明 |
|------|--------|------|
| 企业管理 + 职位推荐 | 高 | 需新建 companies + job_postings 表 |
| 招聘会管理 | 高 | 需新建 job_fairs + registrations 表 |
| 简历助手 | 高 | 需新建 resumes 表 + AI 生成逻辑 |
| 面试日程 | 中 | 需新建 interview_events 表 + 日历视图 |
| 就业数据 | 中 | 数据聚合 + 报表 |

---

## 阶段 8：单智能体稳固期

> **目标**：修复已知 bug、清理技术债务、建立测试基础，让单智能体达到生产可用状态
> **预估时间**：1-2 周
> **前置条件**：阶段 0-7 全部完成

### 8.1 P0 修复（必须立即执行）

| 序号 | 修复项 | 文件 | 说明 |
|------|--------|------|------|
| 8-1 | 修复 `temporal_warnings` 未填充 | `backend/app/agent/nodes.py` | `search_knowledge` 节点调用 `apply_temporal_adjustment` 后，补充 `state["temporal_warnings"]` 字段，前端才能显示时效性警告 |
| 8-2 | 修复 `qa_service.agent_chat()` 无超时 | `backend/app/services/qa_service.py` | `app.invoke()` 增加 `asyncio.wait_for` 或 LangGraph timeout 配置，防止单个请求阻塞 worker |
| 8-3 | 删除死代码 | `backend/app/agent/prompts/moderation.py` 等 | 删除 `prompts/router.py`、`prompts/refusal.py`、`prompts/moderation.py` 3 个未使用的 prompt 文件 |
| 8-4 | 缓存 compiled graph | `backend/app/agent/graph.py` | `get_agent_graph()` 改为单例模式，避免每次调用都重新 `build + compile` |
| 8-5 | 删除文档重复章节 | `docs/Agent模块融合实施方案.md` | 第 8 章出现两遍完全重复，清理为一遍 |

### 8.2 P1 改进（推荐执行）

| 序号 | 改进项 | 文件 | 说明 |
|------|--------|------|------|
| 8-6 | 建立单元测试框架 | `backend/tests/` | 新建 `tests/` 目录，配置 pytest，为核心节点和工具函数编写测试 |
| 8-7 | 标准化 AgentState | `backend/app/agent/state.py` | 当前 `AgentState(Annotated[dict, ...])` 不是合法 TypedDict，改为标准 TypedDict 定义 |
| 8-8 | 合并两个 Agent 端点 | `backend/app/routers/agent.py` + `backend/app/routers/qa.py` | 合并 `/api/v1/agent/chat` 和 `/api/v1/qa/ask/agent` 为统一端点，消除重复的消息保存和图编译逻辑 |
| 8-9 | 增加 `verify_facts` 基础验证 | `backend/app/agent/hallucination_defense.py` | 当前只做 regex 提取，增加"事实是否被引用内容支持"的简单校验（用引用片段的文本重叠度判断） |

### 阶段 8 验收清单

- [ ] `temporal_warnings` 前端可见
- [ ] `agent_chat()` 超时保护生效
- [ ] 死代码文件已删除
- [ ] Graph 编译仅执行 1 次
- [ ] 单元测试通过率 ≥ 80%
- [ ] `AgentState` 为合法 TypedDict
- [ ] 两个 Agent 端点已合并

---

## 阶段 9：单智能体扩展期

> **目标**：在不改变单智能体架构的前提下，通过新增工具扩展能力，为后续业务模块提供支持
> **预估时间**：2-3 周
> **前置条件**：阶段 8 完成
> **架构原则**：始终保持单智能体架构，所有新工具通过 `agent/tools.py` 统一注册，LangGraph 12 节点不变

### 9.1 新增 Agent 工具

| 工具 | 用途 | 实现方式 | 预估 |
|------|------|----------|------|
| `generate_resume()` | 简历生成 | LLM 链式调用：生成 → 优化 → 排版 | 3 天 |
| `recommend_jobs()` | 职位推荐 | RAG + 向量匹配 + 规则过滤 | 2 天 |
| `add_calendar_event()` | 面试日程 | 调用日程 API，生成 ICS | 1 天 |
| `toggle_faq_status()` | FAQ 管理 | 直接调用后端 API | 0.5 天 |
| `fetch_announcement()` | 公告展示 | 读取公告表 | 0.5 天 |

**实现要点**：
- 所有工具在 `backend/app/agent/tools.py` 中使用 `@tool` 装饰器统一注册
- 工具通过 `generate_response` 或 `direct_response` 节点调度
- 工具返回标准化格式（`dict` + `metadata`），与现有 `knowledge_search` / `bing_search` 保持一致

### 9.2 意图分类扩展

| 当前意图 | 扩展为 | 说明 |
|----------|--------|------|
| `kb_query` | `policy_query` / `faq_query` / `document_query` | 知识库内部细分 |
| `job_query` | `resume_query` / `interview_query` / `salary_query` | 求职相关细分 |
| `web_query` | `news_query` / `policy_web_query` | 网页检索细分 |

**实现要点**：
- `route_query` 节点扩展为 6 类意图分类
- 新增关键词常量和 `backend/app/agent/constants.py` 中管理
- 不同意图可路由到不同的工具链

### 9.3 AgentState 扩展字段

| 字段 | 类型 | 用途 |
|------|------|------|
| `resume_data` | `dict` | 简历生成中间数据 |
| `job_recommendations` | `list` | 职位推荐结果 |
| `calendar_events` | `list` | 面试日程数据 |
| `announcements` | `list` | 公告列表 |

**实现要点**：
- 在 `backend/app/agent/state.py` 中新增字段，保持向后兼容
- 字段可选（`Annotated[Optional[...], ...]`），不影响现有流程

### 9.4 前端传历史优化

| 优化项 | 说明 |
|--------|------|
| 最近 6 轮 → 最近 10 轮 | 已实现基础版，扩展为可配置 |
| 历史消息结构化 | 增加 role / timestamp / confidence 等元信息 |

### 阶段 9 验收清单

- [ ] 5 个新工具全部注册并可调用
- [ ] 意图分类扩展为 6 类，准确率 ≥ 85%
- [ ] AgentState 新增字段不影响现有流程
- [ ] 前端传历史可配置轮数
- [ ] 工具调用记录在 `reasoning_chain` 中可见

---

## 阶段 10：多智能体触发评估

> **目标**：根据阶段 9 的实际运行数据，评估是否需要从单智能体升级为多智能体架构
> **触发时机**：阶段 9 完成后
> **决策依据**：以下触发条件检查表

### 触发条件检查表

| 检查点 | 评估内容 | 触发则引入 | 不触发则继续单智能体 |
|--------|---------|-----------|-------------------|
| **Checkpoint 1** | 工具数量 > 8？单次 Prompt > 4k tokens？ | 引入 Supervisor 路由 | 继续单智能体 + 工具扩展 |
| **Checkpoint 2** | 简历助手是否需要独立"生成→预览→修改"流程？单次生成是否 > 15s？ | 引入 ResumeSubgraph | 保持单智能体 + 工具链 |
| **Checkpoint 3** | 职位推荐是否需要独立状态管理？推荐逻辑是否与问答差异显著？ | 独立 RecommendationSubgraph | 单智能体 + recommend_jobs 工具 |
| **Checkpoint 4** | 求职/问答是否需要上下文隔离？ | 独立 JobAgent | 保持单智能体，共享历史 |

### 路径 A：继续单智能体（推荐）

```
阶段 11：复杂业务域开发
    ├── 前端缺失页面补齐
    ├── 继续新增工具
    ├── 意图分类持续扩展
    └── 监控和性能优化
```

### 路径 B：引入 Subgraph（中期）

```
阶段 11.5：JobAgent Subgraph 引入
    ├── QAAgent 保持不变（沿用现有 12 节点）
    ├── 新增 ResumeSubgraph（简历生成独立流程）
    ├── 新增 RecommendationSubgraph（职位推荐独立流程）
    ├── LangGraph Supervisor 路由到对应 Subgraph
    ├── 共享 UserProfile 服务
    └── 前端通过 `/api/v1/agent/chat?agent_type=qa|job` 区分
```

### 路径 C：全多智能体（远期，不考虑）

> 仅在以下全部满足时考虑：团队 > 10 人、各业务域有独立产品/技术负责人、需要 7×24 独立扩缩容、不同 Agent 需要完全不同的模型/提示词策略。
>
> 否则路径 B 的 subgraph 方案已经是足够的抽象。

### V4.0 多智能体架构设计（如需引入）

> 本方案在触发条件满足时启用，否则保持单智能体架构。

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

#### 各智能体职责

| 智能体 | 节点数 | 状态 | 工具 | 防御 |
|--------|--------|------|------|------|
| **QAAgent** | 12 | `AgentState` 完整继承 | knowledge_search / bing_search / fetch_webpage | 完整五层防御 |
| **JobAgent** | 6-8 | `JobAgentState`（继承 `AgentState`） | search_knowledge / recommend_jobs / generate_resume / add_calendar_event | 复用动态阈值 + 简化版内容审核 |
| **OpsAgent** | — | 不需要 LangGraph | 直接 FastAPI 路由 + 工具函数 | 无 |

#### 状态隔离策略

```python
# 基础字段（共享）
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

#### 前端路由映射

| URL | 对应 Agent | 说明 |
|-----|-----------|------|
| `/chat` | QAAgent | 现有 ChatView |
| `/chat/resume` | JobAgent | 简历助手 |
| `/jobs` | JobAgent | 职位推荐 |
| `/chat/interviews` | JobAgent | 面试日程 |
| `/admin/*` | OpsAgent（REST） | 管理端页面 |

前端通过 `/api/v1/agent/chat?agent_type=qa|job` 区分调用的 Agent 类型。

---

## 阶段 11：复杂业务域开发

> **目标**：补齐前端缺失页面 + 开发新业务模块
> **预估时间**：4-8 周（按批次）
> **前置条件**：阶段 9 完成，工具扩展就绪

### 批次计划

| 批次 | 页面/模块 | 预估 | 前置依赖 |
|------|----------|------|---------|
| **Batch 1** | 统计分析页 + 学生管理页 | 3-5 天 | 后端接口就绪 |
| **Batch 2** | 系统设置 + 我的收藏 + 公告管理 | 1-2 周 | 无 |
| **Batch 3** | 智能问答配置 + 对话管理 | 1 周 | Batch 2 |
| **Batch 4** | 企业管理 + 职位推荐 | 2 周 | Batch 2 |
| **Batch 5** | 招聘会 + 简历助手 | 2 周 | Batch 4 |
| **Batch 6** | 面试日程 + 就业数据 | 2 周 | Batch 5 |
| **Batch 7** | 帮助中心 | 3-5 天 | 无 |

### 详细需求

详见 [missing-frontend-pages.md](./missing-frontend-pages.md) 和各页面实施文档。

---

## 阶段总览（更新）

```
阶段 0：环境准备           （半天）          ✅ 完成
阶段 1：Agent 核心构建     （2～3 天）      ✅ 完成
阶段 2：幻觉防御集成       （2 天）         ✅ 完成
阶段 3：监控告警模块       （2 天）         ✅ 完成
阶段 4：问答服务升级       （1 天）         ✅ 完成
阶段 5：路由 + Schema      （1 天）         ✅ 完成
阶段 6：前端对接           （2 天）         ✅ 完成
阶段 7：外部检索兜底       （1-2 天）       ✅ 完成
─────────────────────────────────────────────────────
阶段 8：单智能体稳固期     （1-2 周）       🔄 待启动（推荐优先级）
阶段 9：单智能体扩展期     （2-3 周）       ⏸️ 待阶段 8 完成后启动
阶段 10：多智能体触发评估  （决策点）        ⏸️ 待阶段 9 完成后评估
阶段 11：复杂业务域开发    （4-8 周）       ⏸️ 待阶段 9 完成后启动
```

---

## 模块依赖关系图（更新）

```
阶段 0：基础设施层
    ├── 24 张数据库表
    ├── Embedding 三级缓存
    ├── LangSmith 全局追踪
    └── Docker 部署

阶段 1：Agent 核心层（依赖阶段 0）
    ├── LangGraph 12 节点工作流
    ├── SqliteSaver 持久化
    └── 语义缓存

阶段 2：幻觉防御层（依赖阶段 1）
    ├── 五层防御机制
    ├── 拒答模板
    ├── 引用追踪
    └── 时效感知检索

阶段 3：监控告警层（依赖阶段 2 + 模型层）
    ├── KB 健康度监控
    ├── LLM 成本监控
    ├── 引用质量评估
    └── APScheduler 定时任务

阶段 4：服务接入层（依赖阶段 1）
    ├── qa_service.agent_chat()
    └── /ask/agent 端点

阶段 5：接口规范层（依赖阶段 3）
    ├── Schema 抽离
    ├── 3 个监控路由
    └── qa.py 响应对齐

阶段 6：前端展示层（依赖阶段 4 + 阶段 5）
    ├── Vue 3 SPA
    ├── 三栏布局
    ├── Agent 组件
    └── 监控中心

阶段 7：外部扩展层（依赖阶段 1 + 阶段 6）
    ├── Bing MCP Fallback
    ├── 站点白名单路由
    └── Web 引用卡片

阶段 8：单智能体稳固期（依赖阶段 0-7）
    ├── Bug 修复
    ├── 技术债务清理
    └── 测试框架建立

阶段 9：单智能体扩展期（依赖阶段 8）
    ├── 新增 5 个工具
    ├── 意图分类扩展为 6 类
    ├── AgentState 字段扩展
    └── 前端传历史优化

阶段 10：多智能体触发评估（依赖阶段 9）
    └── 评估是否引入 Supervisor + Subgraph

阶段 11：复杂业务域开发（依赖阶段 9）
    ├── 前端缺失页面补齐
    ├── 新业务模块开发
    └── 系统设置 / 收藏 / 公告 / 统计 / 企业 / 职位 / 招聘会 / 简历 / 面试 / 就业数据
```

---

## 单智能体扩展能力说明

> 在保持单智能体架构的前提下，可通过以下方式无限扩展能力，无需引入多智能体。

### 工具扩展（低成本）

通过在 `agent/tools.py` 中新增工具函数扩展能力：

| 新工具 | 对应前端页面 | 实现方式 | 复杂度 |
|--------|-------------|----------|--------|
| `generate_resume()` | 简历助手 | LLM 链式调用 | 中 |
| `recommend_jobs()` | 职位推荐 | RAG + 向量匹配 + 规则过滤 | 中 |
| `add_calendar_event()` | 面试日程 | 调用日程 API | 低 |
| `toggle_faq_status()` | FAQ 管理 | 直接调用后端 API | 低 |
| `batch_operation()` | 批量操作 | 封装批量 API | 低 |
| `fetch_announcement()` | 公告展示 | 读取公告表 | 低 |

### 意图分流扩展（低成本）

`route_query` 的 3 类意图可以进一步细分为 6 类：

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

## 何时需要升级为多智能体

### 触发条件分析

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
| **职位推荐** | ⚠️ 边界 | 推荐算法独立 | 见下方分析 |
| 招聘会管理 | ✅ 可行 | 报名/签到流程可工具化 | 直接前端 + REST API |
| 面试日程 | ✅ 可行 | 日历操作可工具化 | 直接前端 + REST API |
| 帮助中心 | ✅ 可行 | 复用 FAQ + 文档 | 直接前端 + REST API |

### 边界模块详细分析

#### 简历助手：单 Agent 可扩展，但 subgraph 更清晰

**单 Agent 方案**：
- 优点：复用同一个对话上下文，用户可以在生成过程中随时修改
- 缺点：`generate_response` 节点变复杂，一次 `invoke` 中串行调用 3+ 次 LLM，超时风险增加

**多 Agent（subgraph）方案**：
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

### 决策检查点

| 检查点 | 时间 | 评估内容 | 决策 |
|--------|------|----------|------|
| **Checkpoint 1** | 补齐前端页面后 | 当前单 Agent 是否稳定？工具数 < 8？ | 继续单 Agent |
| **Checkpoint 2** | 做简历助手前 | 生成流程是否需要 3+ 步链式编排？ | 是 → 引入 ResumeSubgraph |
| **Checkpoint 3** | 做职位推荐前 | 推荐逻辑是否需要独立状态？ | 否 → 单 Agent + 工具 |
| **Checkpoint 4** | V4.0 设计评审 | 是否有需要隔离的上下文？ | 是 → 引入 Supervisor |

---

## 增量优化项

（已完成的增量优化记录，保持单智能体架构不变）

| 优化项 | 说明 | 状态 |
|--------|------|------|
| Bing 分级 fallback 接入 | `search_knowledge` 按 intent 选择站点白名单，top 1-2 条同步抓取正文 | ✅ 已完成 |
| 前端传历史消息 | `sendAgent()` 传最近 6 轮历史，`check_consistency` 跨轮矛盾检测生效 | ✅ 已完成 |
| 前端展示 fact_issues | `MessageItem.vue` 增加事实核验提示区，标红未找到依据的事实 | ✅ 已完成 |
| Graph 编译缓存 | `AgentGraph.compile()` 缓存 compiled graph，避免重复构建 | ✅ 已完成 |
| ChatInput 终止按钮 | 请求进行中显示红色"终止"按钮，Enter 在 sending 时触发 cancel | ✅ 已完成 |
| ChatStore AbortController | `sendAgent()` 创建 AbortController，`cancelSend()` 中断 pending 请求 | ✅ 已完成 |
| SearchBox 纯检索模式 | 点击"纯检索"调用 `POST /search`，将命中片段以助手消息展示 | ✅ 已完成 |
| MonitorView 扩展 | 月度成本选择器 + 手动健康检查按钮 | ✅ 已完成 |

---

## 阶段 0：基础设施层

> **目标**：搭建可运行的后端基础环境，包含数据库、缓存、追踪、容器化

### 0.1 依赖安装

| 操作 | 文件 | 说明 |
|------|------|------|
| 追加依赖 | `backend/requirements.txt` | 新增 `langgraph>=0.1.0` `langsmith` `apscheduler>=3.10.0` `alembic` `redis` |

**验证**：`python -c "import langgraph,langsmith,apscheduler,alembic,redis; print('OK')"`

---

### 0.2 数据库迁移环境搭建

| 操作 | 文件 | 说明 |
|------|------|------|
| 新建 | `backend/alembic/env.py` | 动态注入连接串，绑定 `Base.metadata` |
| 新建 | `backend/alembic/script.py.mako` | 迁移脚本模板 |
| 修改 | `backend/alembic.ini` | 仅保留英文（避免 Windows GBK 编码问题） |
| 新建 | `backend/migrations/` | 版本脚本输出目录 |

**注意**：`alembic.ini` 禁止写入中文说明，中文注释移至 `env.py`。

---

### 0.3 数据库迁移（3 个版本）

| 版本 | 内容 | 文件 |
|------|------|------|
| `83dc52f295f1` | 基线空迁移（标记现有 17 表为起点） | `migrations/83dc52f295f1_*.py` |
| `be1122c3c9a7` | 6 张监控表 + `qa_message` 加 5 字段 | `migrations/be1122c3c9a7_*.py` |
| `65a7e09c9884` | `embedding_cache` 表（LONGTEXT 存储 embedding） | `migrations/65a7e09c9884_*.py` |

**新增 7 张表**：

| 表名 | 用途 | 关键字段 |
|------|------|----------|
| `agent_refusal_log` | 拒答记录 | `query`, `refusal_reason`, `confidence`, `created_at` |
| `citation_quality_log` | 引用质量评估 | `message_id`, `quality_score`, `direct_count`, `indirect_count`, `none_count` |
| `kb_health_log` | 知识库健康度 | `check_date`, `health_score`, `warning_docs`, `expired_docs` |
| `llm_cost_log` | LLM 成本消耗 | `check_date`, `daily_cost`, `monthly_cost`, `token_count` |
| `consistency_issue_log` | 一致性问题 | `message_id`, `issue_type`, `severity`, `description` |
| `fact_verification_log` | 事实核验 | `message_id`, `fact_type`, `extracted_value`, `validation_result` |
| `embedding_cache` | Embedding L3 缓存 | `key`(SHA256), `embedding`(LONGTEXT), `model`, `created_at`, `expires_at` |

**`qa_message` 新增 5 字段**：`confidence`(DECIMAL5,4)、`query_risk_level`(VARCHAR20)、`consistency_issues`(JSON)、`fact_issues`(JSON)、`temporal_warnings`(JSON)。

**验证**：
```bash
cd backend && .venv/Scripts/python.exe -m alembic upgrade head
# 确认 24 张表
# DESC qa_message 确认 5 个新字段
```

---

### 0.4 Embedding 三级缓存

| 操作 | 文件 | 说明 |
|------|------|------|
| 新建 | `backend/app/core/redis_client.py` | Redis 懒连接 + 30s 冷却熔断降级 |
| 新建 | `backend/app/core/embedding_cache.py` | 三级缓存 `get`/`put`，key=SHA256(text\|model\|dim) |
| 修改 | `backend/app/core/embedding.py` | `embed_query` 接入缓存；全零兜底向量不缓存 |
| 修改 | `backend/app/core/config.py` | Redis + 缓存配置项 |

**缓存链路**：`L1 内存LRU → L2 Redis(24h) → L3 MySQL(embedding_cache) → DashScope API`

**关键设计**：
- 仅缓存 `embed_query`（查询/FAQ 高复用），`embed_texts` 建索引不缓存
- `embedding` 列用 **LONGTEXT**（非 JSON），避免 double 归一化的 1-ULP 偏差
- 任意层不可用时透传降级，不阻塞业务

**验证**：无 Redis 时，4 步自测全为 True。

---

### 0.5 LangSmith 全局追踪

| 操作 | 文件 | 说明 |
|------|------|------|
| 新建 | `backend/app/core/langsmith_setup.py` | `setup_langsmith()` 导出环境变量 |
| 修改 | `backend/app/main.py` | 启动时调用 |
| 修改 | `backend/app/core/config.py` | `LANGSMITH_ENABLED/PROJECT/ENDPOINT` |

**验证**：凭证校验通过（`list_projects` 成功），阶段 1 的 `@traceable` 节点自动上报。

---

### 0.6 Docker 部署文件

| 操作 | 文件 | 说明 |
|------|------|------|
| 新建 | `backend/Dockerfile` | 多阶段构建（builder + runtime），非 root `appuser`，健康检查 `/health/live` |
| 新建 | `docker-compose.yml`（项目根） | 服务：`db`(MySQL 8.4)、`redis`(7-alpine)、`api` |
| 新建 | `.dockerignore` | 排除 `.venv` `__pycache__` `.git` `chroma_data` `uploads` `tests` `docs` `*.log` |
| 新建 | `.env`（项目根） | Docker Compose 环境变量 |

**验证**：`docker compose up -d --build` → `curl http://localhost:8000/health/live` 返回 200。

---

### 阶段 0 验收清单

- [x] 依赖安装成功
- [x] Alembic 就绪，迁移到 `65a7e09c9884`（24 表）
- [x] `qa_message` 5 个新字段
- [x] 三级缓存可用，无 Redis 正确降级，精确往返
- [x] LangSmith 全局生效
- [x] `app.main:app` 构建无报错
- [x] Docker Compose 启动成功

---

## 阶段 1：Agent 核心层

> **目标**：构建 LangGraph 状态机工作流，实现 Agent 核心骨架、持久化、语义缓存
> **产出**：12 节点工作流 / SqliteSaver 持久化 / 语义缓存 / 16 个配置项 / Docker 部署

### 1.1 核心配置

| 操作 | 文件 | 说明 |
|------|------|------|
| 修改 | `backend/app/core/llm.py` | `chat()` / `chat_stream()` 增加 `timeout=30` |
| 修改 | `backend/app/core/config.py` | 新增 16 个 Agent 配置项（详见下表） |

**16 个 Agent 配置项**：

| 配置项 | 默认值 | 用途 |
|--------|--------|------|
| `AGENT_ENABLED` | `False` | 灰度开关：False 时走传统 RAG |
| `AGENT_MAX_ITERATIONS` | `3` | 最大重试次数 |
| `AGENT_TIMEOUT_SECONDS` | `30` | Agent 调用超时 |
| `AGENT_RECURSION_LIMIT` | `15` | 死循环保护硬上限 |
| `AGENT_RATE_LIMIT_PER_USER` | `10` | 单用户每分钟请求数 |
| `AGENT_RATE_LIMIT_GLOBAL` | `100` | 全局每分钟请求数 |
| `HIGH_RISK_THRESHOLD` | `0.90` | 高风险查询置信度阈值 |
| `MEDIUM_RISK_THRESHOLD` | `0.70` | 中风险查询置信度阈值 |
| `LOW_RISK_THRESHOLD` | `0.50` | 低风险查询置信度阈值 |
| `KB_WARNING_DAYS` | `30` | 知识库即将过期提醒天数 |
| `KB_FRESHNESS_HALF_LIFE` | `90` | 知识库新鲜度半衰期（天） |
| `DAILY_COST_THRESHOLD_USD` | `10.0` | 每日成本告警阈值 |
| `MONTHLY_COST_THRESHOLD_USD` | `300.0` | 每月成本告警阈值 |
| `SEMANTIC_CACHE_ENABLED` | `True` | 语义缓存开关 |
| `SEMANTIC_CACHE_SIMILARITY_THRESHOLD` | `0.92` | 语义匹配阈值 |
| `SEMANTIC_CACHE_TTL` | `86400` | 缓存过期时间（秒） |

---

### 1.2 Agent 模块骨架（P0）

| 操作 | 文件 | 说明 |
|------|------|------|
| 新建 | `backend/app/agent/__init__.py` | 模块初始化 |
| 新建 | `backend/app/agent/state.py` | `AgentState` 状态定义（25+ 字段 + 死循环保护字段） |
| 新建 | `backend/app/agent/nodes.py` | 12 个节点函数 |
| 新建 | `backend/app/agent/tools.py` | `knowledge_search()` 工具 + `ToolCallTracker` |
| 新建 | `backend/app/agent/graph.py` | LangGraph 工作流构建 + `recursion_limit=15` |
| 新建 | `backend/app/agent/hallucination_defense.py` | 三层防御类 |
| 新建 | `backend/app/agent/citation_tracker.py` | 引用追踪 V1 |
| 新建 | `backend/app/agent/temporal_retriever.py` | 时效感知检索 V1 |
| 新建 | `backend/app/agent/refusal_handler.py` | 拒答模板 V1 |
| 新建 | `backend/app/agent/constants.py` | 6 个常量提取 |
| 新建 | `backend/app/routers/agent.py` | `POST /api/v1/agent/chat` 端点 |
| 修改 | `backend/app/main.py` | 注册 `/api/v1/agent` 路由 |
| 修改 | `backend/app/models/qa.py` | 新增 5 个 Agent 字段 |

#### 1.2.1 AgentState 字段清单

| 字段 | 类型 | 用途 |
|------|------|------|
| `messages` | `list` | 对话消息历史 |
| `current_query` | `str` | 当前用户查询 |
| `search_results` | `list` | 检索结果 |
| `citations` | `list` | 引用列表 |
| `confidence` | `float` | 综合置信度 |
| `query_risk_level` | `str` | 查询风险等级 (high/medium/low) |
| `route` | `str` | 路由决策 |
| `should_refuse` | `bool` | 是否拒答 |
| `refusal_reason` | `str` | 拒答原因 |
| `consistency_issues` | `list` | 一致性问题 |
| `fact_issues` | `list` | 事实问题 |
| `temporal_warnings` | `list` | 时效警告 |
| `history` | `list` | 历史对话 |
| `reasoning_chain` | `list` | 推理链 |
| `error` | `str` | 错误信息 |
| `is_error` | `bool` | 是否错误 |
| **死循环保护字段** | | |
| `retry_attempt` | `int` | 重试次数 |
| `tool_call_count` | `int` | 工具调用次数 |
| `last_search_query` | `str` | 上次检索词 |
| `regenerate_count` | `int` | 重新生成次数 |
| `forced_exit` | `bool` | 强制退出标记 |
| `is_low_confidence` | `bool` | 低置信度标记 |
| `skipped_consistency_check` | `bool` | 跳过一致性检查标记 |
| **追踪字段** | | |
| `request_id` | `str` | 请求 ID |
| `llm_tokens_in` | `int` | 输入 Token 数 |
| `llm_tokens_out` | `int` | 输出 Token 数 |
| `created_at` | `str` | 创建时间 |

#### 1.2.2 12 个节点函数

| 节点 | 职责 |
|------|------|
| `route_query` | 意图分类（kb_query / job_query / web_query） |
| `search_knowledge` | 知识库检索 + 时效过滤 |
| `check_confidence` | 动态置信度阈值检查 |
| `generate_response` | 生成回答 |
| `regenerate_with_hints` | 带提示重新生成 |
| `check_consistency` | 一致性检查 |
| `verify_facts` | 事实核验 |
| `content_moderation` | 内容审核 |
| `generate_refusal` | 生成拒答 |
| `accept_with_warning` | 带警告接受 |
| `direct_response` | 直接回复（无需检索） |
| `error_handler` | 错误处理 |

---

### 1.3 持久化与语义缓存（P1）

| 操作 | 文件 | 说明 |
|------|------|------|
| 新建 | `backend/app/agent/sqlite_checkpoint.py` | 自实现 `SqliteSaver`（LangGraph 1.2.x 无内置），WAL 模式，JSON 主序列化 + pickle-hex 降级 |
| 新建 | `backend/app/core/semantic_cache.py` | 精确匹配 + 余弦相似度匹配(>0.92)，Redis 存储，1000 条上限，24h TTL |
| 新建 | `backend/app/core/logging_config.py` | 结构化日志（dev 控制台可读 / prod JSON） |
| 修改 | `backend/app/core/database.py` | `pool_timeout=30` |
| 修改 | `backend/app/main.py` | 注册日志 + 优雅关闭 |

**验证**：
- 全量导入验证：`from app.agent.state import AgentState; from app.agent.graph import get_agent_graph; ...`
- 单元测试：`tests/test_agent_workflow.py`（6 个测试场景）
- Checkpoint 持久化：`tests/test_checkpoint_persistence.py`（6 步集成测试）

---

### 1.4 代码质量优化（Ops 1-21 ~ 1-50）

| 序号 | 操作 | 说明 |
|------|------|------|
| 1-21 | 修复 asyncio 误用 | `routers/agent.py` `_run_agent` → `async def` |
| 1-22 | 修复 `app_debug` 默认值 | `True` → `False` |
| 1-23 | 增加启动密钥校验 | `config.py` 增加 `model_validator(mode="after")` |
| 1-24 | 修复内容审核正则 | 匹配逻辑修正 |
| 1-25 | Token 估算中文适配 | 中文 1.5 字符/token，英文 4 字符/token |
| 1-26 | 增加优雅关闭 | `@app.on_event("shutdown")` → `engine.dispose()` |
| 1-27 | 修复 `QaMessage` 字段 | 补充 5 个新字段 |
| 1-28 | 增加 `direct_response` 节点 | 处理无需检索的简单对话 |
| 1-29 | 抽取 `resolve_conversation` | 移至 `app/utils/conversation.py` 复用 |
| 1-31 | 修复数据库连接池 | `pool_timeout=30` |
| 1-32 | 增加结构化日志 | `app/core/logging_config.py` |
| 1-40 | 修复函数名不一致 | `_resolve_conversation` → `resolve_conversation` |
| 1-41 | 清理死代码 | 删除 unused imports in `nodes.py`, `graph.py`, `routers/agent.py` |
| 1-42 | 提取 Magic Number | 创建 `agent/constants.py`（6 个常量） |
| 1-43 | 收紧生产 CORS | 生产环境 origins 默认空列表 |

---

### 1.5 Docker 部署

| 操作 | 文件 | 说明 |
|------|------|------|
| 新建 | `backend/Dockerfile` | 多阶段构建，非 root `appuser`，healthcheck |
| 新建 | docker-compose.yml | 服务：`db`(MySQL 8.4) / `redis`(7-alpine) / `api` |
| 新建 | `.dockerignore` | 排除非必要目录和文件 |
| 新建 | `.env` | 环境变量配置 |

---

### 阶段 1 验收清单

- [x] `AgentState` 25+ 字段定义完整
- [x] 12 节点工作流编译通过，`recursion_limit=15`
- [x] `SqliteSaver` checkpoint 持久化正常
- [x] 语义缓存正常命中/回源
- [x] 16 个配置项均可读取
- [x] 单元测试全部通过
- [x] Docker Compose 启动成功

---

## 阶段 2：幻觉防御层

> **目标**：在 Agent 工作流中集成五层幻觉防御机制
> **产出**：动态阈值·一致性检查·事实核验·拒答模板·引用追踪·时效检索

### 2.1 五层防御组件

| 操作 | 文件 | 说明 |
|------|------|------|
| 确认 | `backend/app/agent/hallucination_defense.py` | 3 个类已集成到节点 |
| 新建 | `backend/app/agent/refusal_handler.py` | 6 个拒答模板 |
| 新建 | `backend/app/agent/citation_tracker.py` | 引用追踪 V1 |
| 新建 | `backend/app/agent/temporal_retriever.py` | 时效感知检索 V1 |

#### 2.1.1 防御机制清单

| 机制 | 类/模块 | 策略 |
|------|---------|------|
| 动态置信度阈值 | `DynamicConfidenceThreshold` | 每重试 -0.15，最低 0.30，最多 3 次重试 |
| 自一致性检查 | `SelfConsistencyChecker` | V1：单响应内关键词矛盾检测 |
| 事实核验 | `FactVerificationPostProcessor` | V1：正则提取政策号/日期/金额，标记"待跨源校验" |
| 拒答模板 | `refusal_handler.py`（6 模板） | V1 直接返回模板，不调用 LLM（节省成本） |
| 引用追踪 | `build_citations(hits)` | 块级引用，评估 direct/indirect/none 比例 |

#### 2.1.2 6 个拒答模板

| 模板 | 触发条件 |
|------|----------|
| `REFUSAL_TEMPLATE` | 通用拒答 |
| `NO_RESULT_REFUSAL` | 知识库无结果 |
| `LOW_CONFIDENCE_REFUSAL` | 置信度过低 |
| `BLOCKED_REFUSAL` | 内容审核拦截 |
| `CONSISTENCY_REFUSAL` | 一致性检查失败 |
| `FACT_VERIFICATION_REFUSAL` | 事实核验失败 |

#### 2.1.3 时效感知检索 V1

| 函数 | 职责 |
|------|------|
| `filter_expired_docs(db, doc_ids)` | 过滤已过期文档 ID |
| `get_expiring_soon_docs(db, warning_days=30)` | 获取即将过期文档（供监控使用） |
| `apply_temporal_adjustment(hits, expired_ids)` | V1 仅标记 `is_expired`，不修改排序分数 |

**V2 规划**：排序分数 = 相似度 × 0.7 + 时效分数 × 0.3。

---

### 2.2 节点工作流集成

| 操作 | 文件 | 说明 |
|------|------|------|
| 修改 | `backend/app/agent/nodes.py` | `search_knowledge` 调用时效过滤 + 读取引用；`generate_refusal` 调用拒答模板 |

**集成点**：
- `search_knowledge` → `filter_expired_docs` + `apply_temporal_adjustment` + `build_citations(citation_tracker)`
- `generate_refusal` → `get_refusal_response(refusal_handler)`

---

### 2.3 引用追踪 V1 输出结构

```
{
  "rank": 1,
  "document_id": "...",
  "document_title": "...",
  "chunk_id": "...",
  "score": 0.85,
  "page_no": 3,
  "snippet": "...（截取 200 字符）"
}
```

**质量评估输出**：
```
{
  "quality_score": 0.75,
  "direct_count": 3,     // ≥0.75 直接匹配
  "indirect_count": 1,   // 0.40-0.75 间接匹配
  "none_count": 1         // <0.40 无匹配
}
```

---

### 阶段 2 验收清单

- [x] 5 层防御机制均已集成到节点工作流
- [x] 6 个拒答模板可用
- [x] 引用追踪 chunk 级正常输出
- [x] 时效检索正常过滤过期文档
- [x] 集成测试通过（42 个测试，0 失败）

---

## 阶段 3：监控告警层

> **目标**：建立知识库健康度、LLM 成本、引用质量的全链路监控体系
> **产出**：6 张监控表 / 3 个监控器 / 4 个定时任务

### 3.1 监控数据模型

| 操作 | 文件 | 说明 |
|------|------|------|
| 新建 | `backend/app/models/monitor.py` | 6 张 ORM 模型 |
| 修改 | `backend/app/models/__init__.py` | 导入监控模型 |

**6 张监控表**（已在 Phase 0 迁移中创建）：

| 表名 | 对应模型 | 用途 |
|------|----------|------|
| `kb_health_log` | `KbHealthLog` | 知识库健康度日志 |
| `llm_cost_log` | `LlmCostLog` | LLM 成本消耗日志 |
| `agent_refusal_log` | `AgentRefusalLog` | 拒答记录（V1 接口预留，V2 写入） |
| `citation_quality_log` | `CitationQualityLog` | 引用质量评估日志 |
| `consistency_issue_log` | `ConsistencyIssueLog` | 一致性问题日志 |
| `fact_verification_log` | `FactVerificationLog` | 事实核验日志 |

**设计决策**：写多读少场景存 MySQL 而非 MongoDB。

---

### 3.2 监控器实现

| 操作 | 文件 | 说明 |
|------|------|------|
| 新建 | `backend/app/monitor/__init__.py` | 模块初始化 |
| 新建 | `backend/app/monitor/health_monitor.py` | `KnowledgeBaseHealthMonitor` |
| 新建 | `backend/app/monitor/cost_monitor.py` | `LlmCostMonitor` |
| 新建 | `backend/app/monitor/citation_evaluator.py` | `CitationQualityEvaluator` |
| 新建 | `backend/app/monitor/scheduler.py` | APScheduler 配置 |

#### 3.2.1 KB 健康度监控

| 方法 | 职责 |
|------|------|
| `run_daily_check()` | 执行日检，返回 `health_score` + 文档列表 |
| `_calculate_health_score()` | `freshness = exp(-0.693 × days / half_life)`，过期文档 ×0.1 |
| `get_expiring_soon_docs()` | 获取即将过期文档 |

**输出字段**：`check_date`, `health_score`(0-100), `warning_count`, `expired_count`, `warning_docs`, `expired_docs`

#### 3.2.2 LLM 成本监控

| 方法 | 职责 |
|------|------|
| `check_daily_cost()` | 统计当日 token 消耗，估算成本 |
| `check_monthly_cost()` | 统计当月累计成本 |

**参考单价**（$/1k tokens）：

| 模型 | Input | Output |
|------|-------|--------|
| `qwen-max` / `qwen-plus` | 0.002 | 0.006 |
| `qwen-turbo` | 0.0003 | 0.0006 |
| `text-embedding-v4` | 0.0001 | 0.0 |

**V1 数据源**：从 `QaMessage.prompt_tokens` / `completion_tokens` 聚合，不调用 LangSmith API。

#### 3.2.3 引用质量评估

| 方法 | 职责 |
|------|------|
| `evaluate_and_log(db, message_id, citations)` | 复用 `citation_tracker.evaluate_citation_quality()`，写入 DB |

---

### 3.3 定时任务（APScheduler）

| 操作 | 文件 | 说明 |
|------|------|------|
| 新建 | `backend/app/monitor/scheduler.py` | 4 个定时任务 |
| 修改 | `backend/app/main.py` | `setup_scheduler()` / `shutdown_scheduler()` 生命周期管理 |

**4 个定时任务**：

| Job | 执行时间 | 职责 |
|------|----------|------|
| `kb_health_check` | 每日 02:00 | 知识库健康度检查 |
| `citation_quality_check` | 每日 02:15 | 引用质量批量评估 |
| `llm_cost_check` | 每日 02:30 | LLM 成本统计 |
| `consistency_check` | 每日 02:45 | 一致性问题扫描 |

**调度器**：`AsyncIOScheduler`，生命周期绑定 FastAPI lifespan。

---

### 阶段 3 验收清单

- [x] 6 张监控表模型与迁移脚本对齐
- [x] 健康度评估公式正确（exp 衰减）
- [x] 成本参考单价配置正确
- [x] 4 个 APScheduler job 注册成功
- [x] 单元测试通过（26 个，1 个 skipped）

---

## 阶段 4：服务接入层

> **目标**：将 Agent 工作流集成到问答服务，暴露 `/ask/agent` 端点
> **产出**：`agent_chat()` 方法 / Agent 端点 / 渐进式迁移

### 4.1 Agent 服务方法

| 操作 | 文件 | 说明 |
|------|------|------|
| 修改 | `backend/app/services/qa_service.py` | 新增 `agent_chat()` 方法 |

**`agent_chat()` 执行流程**：

```
resolve_conversation()          ← 创建/获取会话
  → build AgentState dict       ← 组装 30+ 字段初始状态
  → get_agent_graph().invoke()  ← 执行工作流（ThreadPoolExecutor + 超时保护）
  → save messages + references  ← 持久化用户消息 + AI 回答 + 引用
  → log OpQueryLog              ← 查询日志
  → return enriched_result      ← 17 字段返回
```

**17 个返回字段**：`conversation_id`, `message_id`, `response`, `is_no_answer`, `blocked`, `from_faq`, `references`, `citations`, `confidence`, `route`, `query_risk_level`, `is_low_confidence`, `consistency_issues`, `fact_issues`, `temporal_warnings`, `warnings`, `request_id`, `llm_tokens_in`, `llm_tokens_out`

**超时保护**：`ThreadPoolExecutor` + `future.result(timeout=settings.agent_timeout_seconds)`，超时返回 `is_error=True` 降级响应。

---

### 4.2 Agent 端点

| 操作 | 文件 | 说明 |
|------|------|------|
| 修改 | `backend/app/routers/qa.py` | 新增 `POST /api/v1/ask/agent` |

**渐进式迁移策略**：
- `agent_enabled=False` → 自动降级到传统 `rag_service.ask()`
- 旧 `/ask` 和 `/ask/stream` 端点保持不变
- 前端可显式调用 `/api/v1/ask/agent`

**Bug 修复**：
- Fix 3：`/ask/agent` 最初忽略 `agent_enabled` → 增加降级守卫
- Fix 4：`agent_timeout_seconds` 配置未生效 → 增加 ThreadPoolExecutor 超时保护

---

### 阶段 4 验收清单

- [x] `agent_chat()` 正常执行完整工作流
- [x] 超时时返回降级响应（`is_error=True`）
- [x] `/ask/agent` 端点返回 200
- [x] `agent_enabled=False` 时正常降级
- [x] 单元测试通过（13 个，0 失败）

---

## 阶段 5：接口规范层

> **目标**：统一 Schema 定义，补全监控路由，对齐响应格式
> **产出**：`schemas/agent.py` / `schemas/monitor.py` / 3 个监控路由

### 5.1 Schema 抽离

| 操作 | 文件 | 说明 |
|------|------|------|
| 新建 | `backend/app/schemas/agent.py` | `AgentChatRequest`（`query`, `conversation_id`）+ `AgentChatResponse`（17 字段） |
| 新建 | `backend/app/schemas/monitor.py` | 6 个 `*Read` ORM 模型 + 4 个 DTO |
| 修改 | `backend/app/schemas/__init__.py` | 补充模块说明 |

#### 5.1.1 schemas/monitor.py 清单

| Schema | 类型 | 用途 |
|--------|------|------|
| `KbHealthLogRead` | ORMModel | 健康度日志读取 |
| `LlmCostLogRead` | ORMModel | 成本日志读取 |
| `AgentRefusalLogRead` | ORMModel | 拒答日志读取 |
| `CitationQualityLogRead` | ORMModel | 引用质量读取 |
| `ConsistencyIssueLogRead` | ORMModel | 一致性问题读取 |
| `FactVerificationLogRead` | ORMModel | 事实核验读取 |
| `KbHealthLatest` | DTO | 健康度最新聚合 |
| `LlmCostDailyRead` | DTO | 每日成本聚合 |
| `LlmCostMonthlyRead` | DTO | 每月成本聚合 |
| `RefusalStats` | DTO | 拒答统计聚合 |

---

### 5.2 监控路由（3 组）

| 操作 | 文件 | 说明 |
|------|------|------|
| 新建 | `backend/app/routers/kb_health.py` | 3 个端点 |
| 新建 | `backend/app/routers/llm_cost.py` | 3 个端点 |
| 新建 | `backend/app/routers/refusal.py` | 2 个端点 |
| 修改 | `backend/app/main.py` | 注册 3 个新路由 |
| 修改 | `backend/app/routers/qa.py` | 对齐 `AgentChatResponse` 响应 |
| 修改 | `backend/app/services/qa_service.py` | 返回 dict 补充 `citations`, `is_error`, `request_id`, `llm_tokens_in/out` |

#### 5.2.1 路由端点清单

**`routers/kb_health.py`**：

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| GET | `/api/v1/kb-health/latest` | admin/editor | 最新健康度 |
| GET | `/api/v1/kb-health/history` | admin/editor | 历史记录（日期过滤 + 分页） |
| POST | `/api/v1/kb-health/run` | admin | 手动触发健康检查 |

**`routers/llm_cost.py`**：

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| GET | `/api/v1/llm-cost/daily` | admin/editor | 当日成本（无数据自动生成） |
| GET | `/api/v1/llm-cost/monthly` | admin/editor | 当月成本 |
| GET | `/api/v1/llm-cost/history` | admin/editor | 历史记录（模型/日期过滤 + 分页） |

**`routers/refusal.py`**：

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| GET | `/api/v1/refusal/list` | admin/editor | 拒答列表（风险等级/原因/日期过滤） |
| GET | `/api/v1/refusal/stats` | admin/editor | 拒答统计 |

---

### 阶段 5 验收清单

- [x] `AgentChatResponse` 17 字段与 `qa_service` 返回对齐
- [x] 3 个监控路由共 8 个端点正常注册
- [x] 总计 75+ API 端点可用
- [x] Schema 定义与 ORM 模型一致

---

## 阶段 6：前端展示层

> **目标**：Vue 3 SPA 对接后端 75+ 端点，实现 Agent 增强的三栏布局和监控中心
> **产出**：三栏聊天界面 / Agent 增强组件 / 监控中心 / 纯检索模式

### 6.1 类型与 API 层

| 操作 | 文件 | 说明 |
|------|------|------|
| 修改 | `frontend/src/types/chat.ts` | 新增 `AgentAskResult`（17 字段），扩展 `ChatMessage` |
| 新建 | `frontend/src/types/monitor.ts` | 监控类型定义 |
| 修改 | `frontend/src/api/chat.ts` | 新增 `askAgent()`, `getMessageReferences()` |
| 新建 | `frontend/src/api/monitor.ts` | 8 个监控 API 函数 |

#### 6.1.1 AgentAskResult 字段

与后端 `AgentChatResponse` 17 字段一一对应，前端增加 `isError`, `references` 增强字段。

---

### 6.2 状态管理

| 操作 | 文件 | 说明 |
|------|------|------|
| 修改 | `frontend/src/stores/chat.ts` | 新增 `sendAgent()`, 映射 `AgentAskResult` → `ChatMessage`, `AbortController` 取消 |
| 新建 | `frontend/src/stores/monitor.ts` | 3 个响应式状态 + `refreshDashboardCards()` |

---

### 6.3 聊天组件

| 操作 | 文件 | 说明 |
|------|------|------|
| 新建 | `frontend/src/components/chat/SearchBox.vue` | AI/纯检索切换 + 磨砂玻璃搜索框 |
| 新建 | `frontend/src/components/chat/ConfidenceBadge.vue` | 高/中/低置信度彩色徽章 |
| 新建 | `frontend/src/components/chat/TemporalWarning.vue` | 文档过期警告横幅 |
| 新建 | `frontend/src/components/chat/RefusalMessage.vue` | 拒答提示 + 建议操作 |
| 修改 | `frontend/src/components/chat/MessageItem.vue` | 渲染 ConfidenceBadge / TemporalWarning / RefusalMessage / 引用区 / 事实核验红标 |
| 修改 | `frontend/src/components/chat/ChatInput.vue` | 增加取消按钮（发送中显示红色"终止"） |
| 修改 | `frontend/src/components/chat/ChatInput.vue` | Enter 在 sending 状态触发取消 |

---

### 6.4 仪表盘组件

| 操作 | 文件 | 说明 |
|------|------|------|
| 新建 | `frontend/src/components/dashboard/StatsOverview.vue` | 统计概览 |
| 新建 | `frontend/src/components/dashboard/HotQuestions.vue` | 热门问题 |
| 新建 | `frontend/src/components/dashboard/KbHealthCard.vue` | KB 健康度卡片 |
| 新建 | `frontend/src/components/dashboard/LlmCostCard.vue` | LLM 成本卡片 |
| 新建 | `frontend/src/components/dashboard/RefusalStatsCard.vue` | 拒答统计卡片 |
| 新建 | `frontend/src/components/dashboard/DashboardPanels.vue` | 左侧面板容器 |

---

### 6.5 主视图重构

| 操作 | 文件 | 说明 |
|------|------|------|
| 修改 | `frontend/src/views/ChatView.vue` | **大幅重构**：三栏布局 |
| 修改 | `frontend/src/views/admin/AdminLayout.vue` | 增加 Monitor 菜单项 |
| 新建 | `frontend/src/views/admin/MonitorView.vue` | 监控中心（3 tab：KB 健康度 / LLM 成本 / 拒答记录） |
| 修改 | `frontend/src/router/index.ts` | 注册 `/admin/monitor` 路由 |

#### 6.5.1 三栏布局

```
┌──────────┬───────────────────────┬──────────┐
│  左侧     │      中间             │  右侧     │
│  300px    │      (自适应)          │  340px   │
│          │                       │          │
│ 会话列表   │   SearchBox           │ 热门问题   │
│ Dashboard │   MessageList         │          │
│ 面板      │   ChatInput           │          │
│          │                       │          │
│ (仅 admin │   深空蓝渐变背景        │ (仅 admin │
│  /editor  │   磨砂玻璃搜索框        │  /editor  │
│  可见)    │   霓虹光效             │  可见)    │
└──────────┴───────────────────────┴──────────┘
```

**视觉设计**：深空蓝渐变（`#0a0e27` → `#1a1f3a`），磨砂玻璃搜索框，霓虹光效。

---

### 6.6 增量优化

| 优化项 | 操作 | 说明 |
|--------|------|------|
| 纯检索模式 | `SearchBox.vue`  emits `{text, mode}` | 点击"纯检索"调用 `POST /search`，结果以助手消息展示 |
| 终止生成 | `ChatStore` + `ChatInput` | `AbortController` 中断请求，"已终止生成"提示 |
| 历史消息传递 | `sendAgent()` 传最近 6 轮 | 激活 `check_consistency` 跨轮矛盾检测 |
| 事实核验红标 | `MessageItem.vue` | `fact_issues.unsupported_values` 红色高亮 |
| 双色引用卡 | `ReferenceCard.vue` | 蓝色=本地来源，黄色=网页来源 + "查看原文"链接 |
| 监控中心扩展 | `MonitorView.vue` | 手动健康检查按钮 + 月度成本年月选择器 + 响应式布局 |

---

### 阶段 6 验收清单

- [x] `vue-tsc` 类型检查通过
- [x] `vite build` 构建通过
- [x] 全量导入验证通过
- [x] 三栏布局渲染正常
- [x] `askAgent` 端到端调用正常
- [x] 监控中心 3 个 tab 切换正常
- [x] AdminLayout 菜单注册正常
- [x] 学生用户权限 guard 正常（ dashboard 不显示）

---

## 阶段 7：外部扩展层

> **目标**：当本地知识库无结果或置信度不足时，自动降级到 Bing 网页搜索
> **产出**：Bing MCP 工具 / 分级 Fallback / 站点白名单 / Web 引用卡片

### 7.1 配置扩展

| 操作 | 文件 | 说明 |
|------|------|------|
| 修改 | `backend/app/core/config.py` | 新增 7 个外部检索配置项 |
| 修改 | `backend/requirements.txt` | 确认 `newsapi-python`（后续迁移至 Bing MCP） |

**7 个新增配置项**：

| 配置项 | 默认值 | 用途 |
|--------|--------|------|
| `AGENT_WEB_SEARCH_ENABLED` | `False` | 外部检索开关（默认关闭，需显式开启） |
| `BING_SEARCH_URL` | — | Bing MCP 服务地址 |
| `FETCH_URL` | — | Fetch MCP 服务地址 |
| `FETCH_MAX_LENGTH` | `8000` | 单页最多抓取字符数 |
| `NEWSAPI_PAGE_SIZE` | `5` | 检索结果数量（复用此配置控制 Bing 页大小） |
| `GOVERNMENT_SITES` | `.gov.cn,.edu.cn,...` | 政务站点白名单 |
| `JOB_SITES` | `lagou.com,zhipin.com,...` | 招聘站点白名单 |

---

### 7.2 Bing 检索工具

| 操作 | 文件 | 说明 |
|------|------|------|
| 修改 | `backend/app/agent/tools.py` | 新增 `bing_search()` + `fetch_webpage()` |

#### 7.2.1 `bing_search(query, page_size, site_filter)`

- 调用 Bing MCP 服务
- 标准化输出格式（与本地 ChromaDB 结果结构一致）
- 元数据包含：`source_type=web`, `url`, `source`, `published_at`, `author`
- 失败时返回 `[]`（非阻塞）

#### 7.2.2 `fetch_webpage(url, max_length)`

- 调用 Fetch MCP 获取文章正文
- 20 秒超时
- 失败时返回 `None`（降级使用 snippet）

#### 7.2.3 检索工具名称兼容

Bing MCP 工具名在不同提供方可能不同（`bing_search` / `bing-cn_search` / `web_search`），代码通过 `find_tool()` 多候选匹配解决。

---

### 7.3 分级 Fallback 策略

| 条件 | 策略 |
|------|------|
| 本地有检索结果 + 最高分 ≥ 阈值 | 正常走本地流程，不触发 Fallback |
| 本地无结果 OR 最高分 < 阈值 | 触发 `bing_search()` |
| `bing_search` 结果为空 | 走拒答/Fallback 流程 |
| `bing_search` 有结果 | top 1-2 条同步 `fetch_webpage()` 抓正文，替换 snippet |

#### 7.3.1 意图路由白名单

| 意图类型 | 站点白名单 | 说明 |
|----------|-----------|------|
| `web_query` | 政务站点 | 政策类问题优先权威来源 |
| `job_query` | 招聘站点 + 本地知识库合并 | 求职相关问题 |
| `kb_query` | 无限制 | 纯知识库查询 |

---

### 7.4 引用追踪扩展

| 操作 | 文件 | 说明 |
|------|------|------|
| 修改 | `backend/app/agent/citation_tracker.py` | 增加 `source_type`, `url`, `source`, `published_at`, `author` 字段 |

**来源类型**：
- `source_type=local` — 本地知识库来源（蓝色卡片）
- `source_type=web` — 网页来源（黄色卡片 + 外部链接）

---

### 7.5 前端展示扩展

| 操作 | 文件 | 说明 |
|------|------|------|
| 修改 | `frontend/src/types/chat.ts` | `Reference` 类型增加 web 相关字段 |
| 修改 | `frontend/src/components/chat/ReferenceCard.vue` | 双区布局：蓝色本地 + 黄色网页 |
| 修改 | `frontend/src/components/chat/MessageItem.vue` | 增加事实核验红标区域 |

---

### 阶段 7 验收清单

- [x] `bind_search()` 返回标准化命中结果
- [x] `fetch_webpage()` 正常获取正文
- [x] `/ask/agent` 返回 HTTP 200
- [x] 本地无结果时触发 Bing 检索
- [x] 前端 ReferenceCard 双色渲染正常
- [x] `AGENT_WEB_SEARCH_ENABLED=false` 时跳过外部检索

---

## 模块依赖关系图

```
                        ┌──────────────────┐
                        │  前端展示层       │
                        │  (Vue 3 SPA)     │
                        └────────┬─────────┘
                                 │ 消费 API
                        ┌────────▼─────────┐
                        │  接口规范层       │
                        │  schemas + routers│
                        └────────┬─────────┘
                                 │
          ┌──────────────────────┼──────────────────────┐
          │                      │                      │
┌─────────▼──────────┐  ┌───────▼────────┐  ┌────────▼────────┐
│  服务接入层        │  │  监控告警层     │  │  外部扩展层     │
│  qa_service       │  │  monitor/*      │  │  bing_search    │
│  /ask/agent       │  │  6 monitoring   │  │  fetch_webpage  │
└─────────┬──────────┘  │  tables         │  └────────┬────────┘
          │             └──────────────────┘           │
          │               ┌──────────────────┐         │
          │               │  幻觉防御层        │         │
          │               │  hallucination    │         │
          │               │  citation_tracker │         │
          │               │  temporal_retriever│        │
          │               │  refusal_handler  │         │
          │               └────────┬───────────┘         │
          │                        │                     │
          │               ┌────────▼───────────┐         │
          │               │  Agent 核心层        │         │
          │               │  graph.py           │         │
          │               │  nodes.py           │         │
          │               │  state.py           │         │
          │               │  sqlite_checkpoint   │         │
          │               │  semantic_cache     │         │
          │               └────────┬───────────┘         │
          │                        │                     │
          │               ┌────────▼───────────┐         │
          │               │  基础设施层          │         │
          │               │  core/config        │         │
          │               │  core/database      │         │
          │               │  core/llm           │         │
          │               │  core/embedding     │         │
          │               │  core/vectorstore   │         │
          │               │  24 tables (MySQL)  │         │
          │               │  LangSmith          │         │
          │               └─────────────────────┘         │
          │                                               │
          │     ← ← ← ←  ← ← ← ← ← ← ← ← ←             │
          │        前端通过 API 调用后端所有模块            │
          └──────────────────────────────────────────────┘
```

---

## 增量优化项

> 阶段 7 完成后（2026-06-26）追加的增量优化，不需新的阶段，穿插在各模块中完成。

| 序号 | 优化项 | 涉及模块 | 说明 |
|------|--------|----------|------|
| 1 | Bing 分级 Fallback | 外部扩展层 | `search_knowledge` 按 intent 选择站点白名单，top 1-2 条同步抓取正文 |
| 2 | 前端传历史消息 | 前端展示层 | `sendAgent()` 传最近 6 轮历史，`check_consistency` 跨轮矛盾检测生效 |
| 3 | 前端展示 `fact_issues` | 前端展示层 | `MessageItem.vue` 增加事实核验提示区，标红未找到依据的事实 |
| 4 | Graph 编译缓存 | Agent 核心层 | `AgentGraph.compile()` 缓存 compiled graph，避免重复构建 |
| 5 | ChatInput 终止按钮 | 前端展示层 | 请求进行中显示红色"终止"按钮，Enter 在 sending 时触发 cancel |
| 6 | ChatStore AbortController | 前端展示层 | `cancelSend()` 调用 `abort()` 中断 pending 请求 |
| 7 | SearchBox 纯检索模式 | 前端展示层 | 调用 `POST /search`，命中片段以助手消息展示 |
| 8 | MonitorView 扩展 | 前端展示层 | 月度成本年月选择器 + 手动健康检查按钮 + 响应式布局 |

---

## 快速查阅索引

| 我想... | 查阅 |
|---------|------|
| 了解某个模块的实现细节 | [模块速查](./module-reference.md) |
| 执行数据库迁移 | [迁移指南](./migration.md) |
| 排查阶段 0 环境问题 | [phase-0-environment.md](../progress/phase-0-environment.md) |
| 理解 Agent 工作流设计 | [phase-1-agent-core.md](../progress/phase-1-agent-core.md) + [设计文档](../Agent模块设计文档.md) |
| 了解幻觉防御机制 | [phase-2-hallucination-defense.md](../progress/phase-2-hallucination-defense.md) |
| 配置监控告警 | [phase-3-monitoring.md](../progress/phase-3-monitoring.md) |
| 对接问答服务 | [phase-4-qa-upgrade.md](../progress/phase-4-qa-upgrade.md) |
| 前端对接实施 | [phase-6-frontend.md](../progress/phase-6-frontend.md) |
| 外部检索兜底 | [phase-7-web-search-fallback.md](../progress/phase-7-web-search-fallback.md) |
| 多智能体架构设计 | [multi-agent-architecture.md](./multi-agent-architecture.md) | V4.0 升级评估参考 |

---

## 单智能体扩展能力说明

> **核心结论**：当前单 Agent（12 节点 LangGraph 工作流）**已足够覆盖 Phase 0-7 的全部功能**。前端实施方案中规划的所有 Phase 1-5 页面，都可以通过单 Agent + 工具扩展 + 意图分流升级来实现，无需引入多智能体架构。

### 可扩展的工具清单

当前 `agent/tools.py` 有 3 个工具，可通过新增工具扩展覆盖更多场景：

| 新工具 | 覆盖页面 | 实现复杂度 | 说明 |
|--------|---------|-----------|------|
| `generate_resume` | 简历助手 | 中 | 调用 LLM 链式生成 + 模板渲染 |
| `recommend_jobs` | 职位推荐 | 中 | RAG 检索 + 向量匹配 + 规则过滤 |
| `add_calendar_event` | 面试日程 | 低 | 调用日程 API，生成 ICS |
| `batch_operation` | 批量操作 | 低 | 封装批量 API 调用 |
| `fetch_announcement` | 公告展示 | 低 | 读取公告表 |
| `toggle_faq_status` | FAQ 管理 | 低 | 复用现有 PUT 接口 |

### 意图分流升级路径

`route_query` 节点的 3 类意图可细化为 6 类：

| 当前意图 | 可扩展子意图 | 说明 |
|----------|-------------|------|
| `kb_query` | `policy_query` / `faq_query` / `document_query` | 知识库内部细分 |
| `job_query` | `resume_query` / `interview_query` / `salary_query` | 求职相关细分 |
| `web_query` | `news_query` / `policy_web_query` | 网页检索细分 |

### 适用边界

**单 Agent 够用的场景**：
- 业务逻辑是"检索+生成"的变体
- 工具之间共享上下文（用户对话历史）
- 防御逻辑统一（一致性、事实核验、拒答）
- 团队规模 < 5 人，快速迭代期

**需要升级为多 Agent 的信号**：
- 出现 3+ 个**独立子流程**（如简历生成需要"生成→预览→修改"的独立状态机）
- Agent 工具数量 > 8 个导致单 Prompt 超过 4k tokens
- 不同业务域需要**完全不同的提示词策略**或**不同模型**
- 团队 > 10 人且各业务域有独立负责人

---

## 何时需要升级为多智能体

> 详细的多智能体架构设计见 [multi-agent-architecture.md](./multi-agent-architecture.md)

### 触发条件检查表

| 检查点 | 触发条件 | 建议架构 |
|--------|----------|----------|
| **Checkpoint 1** | 补齐前端页面后，单 Agent 是否稳定？工具 < 8？ | ✅ 保持单 Agent |
| **Checkpoint 2** | 做简历助手前，生成流程是否需要 3+ 步链式编排？ | ⚠️ 引入 ResumeSubgraph |
| **Checkpoint 3** | 做职位推荐前，推荐逻辑是否需要独立状态？ | ❌ 单 Agent + 工具 |
| **Checkpoint 4** | V4.0 评审时，是否有需要隔离的上下文？ | ⚠️ 引入 Supervisor |

### 推荐的决策路径

```
Phase 8：保持单 Agent
├── 工具扩展至 6-8 个
├── route_query 细化为 6 类意图
└── 补齐所有前端页面

Phase 9（条件触发）：引入 Subgraph
├── ResumeSubgraph（简历生成流程）
├── RecommendationSubgraph（职位推荐流程）
└── QAAgent 保持不变，Supervisor 路由

Phase 10（远期，不建议当前考虑）
└── 仅在团队 > 10 人、各域独立负责时有价值
```

### 当前不需要多智能体的理由

1. **工具数量不足**：当前仅 3 个工具，远未达到 8 个的上限
2. **业务逻辑同构**：问答、检索、职位匹配都是"检索+生成"模式
3. **状态可共享**：扁平 AgentState 足够，无需隔离
4. **团队规模小**：小型团队维护多 Agent 系统成本过高
5. **渐进式可行**：LangGraph 的 subgraph API 在 1.2.x 已可用，可随时升级

