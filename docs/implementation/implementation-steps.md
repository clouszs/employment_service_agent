# 实施步骤总览（精简版）

> 本文件为阶段 0-11 的极简汇总，完整历史记录见 [docs/archive/implementation-steps.md](../archive/implementation-steps.md)。
> **更新时间**：2026-07-02
> **当前阶段**：Batch C 待规划

---

## 12 阶段演进时间线

| 阶段 | 状态 | 时间 | 核心产出 |
|------|------|------|----------|
| 0 环境准备 | ✅ | 2026-06-23 | 24 表 / Embedding 三级缓存 / LangSmith / Docker |
| 1 Agent 核心 | ✅ | 2026-06-24 | LangGraph 12 节点 / SqliteSaver / 语义缓存 |
| 2 幻觉防御 | ✅ | 2026-06-25 | 五层防御 / 拒答模板 / 引用追踪 / 时效检索 |
| 3 监控告警 | ✅ | 2026-06-25 | KB 健康度 / LLM 成本 / 引用质量 / 4 cron job |
| 4 问答升级 | ✅ | 2026-06-25 | agent_chat() 集成 + /ask/agent 端点 |
| 5 路由 Schema | ✅ | 2026-06-25 | Schema 抽离 + 3 个监控路由 |
| 6 前端对接 | ✅ | 2026-06-26 | 三栏布局 / Agent 组件 / 监控中心 |
| 7 外部检索 | ✅ | 2026-06-26 | Bing MCP + 站点白名单 + web 引用卡片 |
| 8 单智能体稳固 | ✅ | 2026-06-27 | verify_facts 增强 / AgentState 标准化 / 14 单测 |
| 9 单智能体扩展 | ✅ | 2026-06-27 | 5→3 工具（去债务）/ 9 类意图 / 公告后端接管 |
| 10 多智能体评估 | ✅ | 2026-06-27 | 5 检查点全未触发 → 无需多 Agent |
| 11 复杂业务域 | ✅ | 2026-06-27 | Batch A 收藏+公告 / Batch B 系统设置+QA配置+对话管理 |

---

## 当前技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 后端 | FastAPI + SQLAlchemy | 异步 Web 框架，30+ 路由 |
| Agent | LangGraph 1.2.6 | 12 节点固定流水线，SqliteSaver checkpoint |
| LLM | 通义千问 qwen3.7-max | DashScope OpenAI 兼容接口 |
| 向量 | ChromaDB 嵌入式 | kb_chunks collection，cosine 距离 |
| 缓存 | Redis（可选）+ 内存 LRU | Embedding 三级缓存（L1/L2/L3） |
| 数据库 | MySQL 8.x utf8mb4 | 24 张表 |
| 监控 | APScheduler + LangSmith | 4 个定时任务（KB 健康/成本/引用/一致性） |
| 前端 | Vue 3 + TypeScript + Vite | Pinia 状态管理，Element Plus，ECharts |

---

## 阶段 11 完成情况

### Batch A：我的收藏 + 公告管理（`ea020dd`）

| 模块 | 后端 | 前端 | 路由 |
|------|------|------|------|
| UserFavorite | 4 个文件 | FavoritesView + API | `/chat/favorites` |
| Announcement | 4 个文件 | AnnouncementsView + ChatView Banner | `/admin/announcements` |
| AppConfig | 4 个文件 | — | `/app-configs` |

### Batch B：系统设置 + QA 配置 + 对话管理（`8706193` / `d5f9d3e` / `48ecdc3`）

| 页面 | 路由 | 后端 API | 核心交互 |
|------|------|----------|----------|
| 系统设置 | `/admin/settings` | 复用 `/app-configs` | 4 分组 Tab / 行内编辑 / 统一保存 |
| 智能问答配置 | `/admin/qa-config` | 复用 `/app-configs`（qa_ 前缀） | 4 QA 分组 / 行内编辑 |
| 对话管理 | `/admin/conversations` | `/admin/conversations/*` | 跨用户列表 / 强制删除 / 详情弹窗 |

---

## Batch C 待规划

| 模块 | 复杂度 | 说明 | 依赖 |
|------|--------|------|------|
| 企业管理 + 职位 CRUD | 高 | 新建 companies + job_postings 表 | DB 迁移 |
| 招聘会管理 | 高 | 新建 job_fairs + registrations 表 | DB 迁移 |
| 就业数据报表 | 中 | 数据聚合 + ECharts 可视化 | 后端聚合接口 |

> **原则**：工具数已封顶 8 个，Batch C 新模块必须走 REST API，不新增 Agent 工具。

---

## 关键架构决策（详见 ADR）

- **检索**：ChromaDB 单路向量 + 时效调整，不引入 BM25/ES/Rerank
- **Agent**：单智能体 + 固定流水线，5 检查点触发才引入多智能体
- **三层定位法**：对话推理 → graph 节点；我方业务 → service+REST；外部 → MCP
- **去债务**：tools.py 注册表删除，5 个业务工具改为 REST

---

## 相关文档

| 文档 | 用途 |
|------|------|
| [implementation/README.md](./README.md) | 实施总览（本文上级） |
| [implementation/module-reference.md](./module-reference.md) | 模块文件清单 + 职责 |
| [implementation/migration.md](./migration.md) | 数据库迁移脚本 |
| [architecture/ARCHITECTURE_DECISIONS.md](../../architecture/ARCHITECTURE_DECISIONS.md) | 关键架构决策（ADR） |
| [progress/README.md](../progress/README.md) | 阶段完成状态 |
| [progress/phase-10.md](../progress/phase-10.md) | 多智能体评估 |
| [progress/phase-11.md](../progress/phase-11.md) | 复杂业务域开发 |
| [modules/CURRENT_CAPABILITIES.md](../../modules/CURRENT_CAPABILITIES.md) | 当前能力清单 |
