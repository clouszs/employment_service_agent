# 当前能力清单

> 反映 2026-06-28 去债务重构**之后**，截至 2026-07-02 的最新状态。原始阶段记录见 [docs/progress/](../progress/)，决策依据见 [../architecture/ARCHITECTURE_DECISIONS.md](../architecture/ARCHITECTURE_DECISIONS.md)。

---

## 表 1：检索类能力（Agent 工具）

文件 [backend/app/agent/tools.py](../../backend/app/agent/tools.py)。经三层定位重构后，agent 工具回归为「检索」本职，共 3 个：

| 工具 | 类型 | 实现/依赖 |
|---|---|---|
| `knowledge_search` | 进程内 RAG | 复用 `rag_service.search()`，ChromaDB `kb_chunks` 向量检索 + FAQ 命中 + 时效调整 |
| `bing_search` | 外部检索（MCP） | 外部 Bing 搜索 MCP 服务（`bing_search_url`），支持按意图走站点白名单 |
| `fetch_webpage` | 外部抓取（MCP） | 外部 Fetch MCP 服务（`fetch_url`），抓取网页正文 |

> 变更记录：Phase 9 曾在 `TOOLS` 注册表挂 8 个工具，但其中 5 个业务工具未接线。2026-06-28 重构删除 `TOOLS` 注册表及 `generate_resume / recommend_jobs / toggle_faq_status / add_calendar_event` 死代码，`fetch_announcement` 收编进 `announcement_service`。简历/职位/日历改为 REST（见表 4）。

---

## 表 2：管理/运营类端点（前缀 `/api/v1`）

| 模块 | 路由前缀 | 说明 |
|---|---|---|
| 认证 | `/auth` | 登录 / me / 改密 |
| 用户 / 角色 | `/users`、`/roles` | 账号与角色管理（admin） |
| 知识库 | `/categories`、`/documents`、`/index-tasks`、`/faqs`、`/synonyms` | 分类/文档/索引任务/FAQ/同义词 |
| 检索 / 问答 | `/search`、`/ask`、`/agent` | 纯向量检索 / 问答 / Agent 对话 |
| 会话 / 消息 | `/conversations`、`/messages` | 用户会话与消息 |
| 管理端对话 | `/admin/conversations` | 全站对话列表/详情/强制删除（Phase 11） |
| 安全 / 日志 | `/sensitive-words`、`/logs` | 敏感词 / 查询日志 |
| 运营 | `/feedback`、`/unanswered`、`/eval-cases` | 反馈 / 无答案 / 评测集 |
| 系统配置 / 收藏 / 公告 / 学生服务 | `/app-configs`、`/favorites`、`/announcements`、`/career` | QA 配置以 `qa_` 前缀区分（Phase 11）；`/career` 学生生涯服务见 Table 4 |

> 端点数明细见 `phase-5-routing-schema.md` 验收路由表。

---

## 表 3：监控端点（前缀 `/api/v1`，权限 admin/editor）

| 端点 | 说明 |
|---|---|
| `/kb-health/latest`、`/history`、`/run` | KB 健康度快照 / 历史 / 手动触发 |
| `/llm-cost/daily`、`/monthly`、`/history` | LLM 成本日/月/历史 |
| `/refusal/list`、`/stats` | 拒答记录 / 统计摘要 |
| `/stats` | 仪表盘统计聚合 |

> 另有 LangSmith Dashboard 作为外部 LLM 调用追踪层（非本服务 HTTP 端点）。

---

## 表 4：学生生涯服务（新增，service + REST）

文件 [backend/app/routers/career.py](../../backend/app/routers/career.py) + `app/services/{resume,job,calendar}_service.py`。用户主动触发的确定性业务，**不经过 Agent 工作流**；LLM 用量经 `llm_usage.log_feature_usage` 审计。

| 端点 | 方法 | service | 说明 |
|---|---|---|---|
| `/career/resume` | POST | `resume_service.generate_resume` | 基于用户档案 + 目标岗位生成结构化简历 JSON（LLM） |
| `/career/jobs` | POST | `job_service.recommend_jobs` | 基于知识库 RAG 检索推荐职位（确定性，无 LLM） |
| `/career/calendar/ics` | POST | `calendar_service.build_ics` | 生成面试日程 ICS 文本（纯计算） |

前端对接：[frontend/src/views/student/ResumeView.vue](../../frontend/src/views/student/ResumeView.vue)、[JobsView.vue](../../frontend/src/views/student/JobsView.vue)、[CalendarView.vue](../../frontend/src/views/student/CalendarView.vue)，API 封装 [frontend/src/api/career.ts](../../frontend/src/api/career.ts)。

> 学生生涯服务的就业数据看板、面试日历前端入口已就位（`CalendarView.vue`、`EmploymentDataView.vue`），由 `/student/calendar` 和 `/student/employment` 路由承载。
