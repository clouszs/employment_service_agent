# 实施指南总览

> **前置阅读**：[architecture/ARCHITECTURE_DECISIONS.md](../../architecture/ARCHITECTURE_DECISIONS.md)（理解关键决策）
> 历史阶段详细记录（phase-0~9）已归档：[docs/archive/](../../archive/)

---

## 目录结构

| 文件 | 内容 |
|------|------|
| [README.md](./README.md) | 实施总览（本文件）+ 阶段总览表 + 技术栈 |
| [implementation-steps.md](./implementation-steps.md) | 12 阶段演进时间线 + Batch C 规划 |
| [module-reference.md](./module-reference.md) | 全模块文件清单、职责（精简，无代码片段）|
| [migration.md](./migration.md) | 数据库迁移：表结构、迁移脚本、执行验证 |
| 历史阶段文档 | [docs/archive/](../../archive/)（phase-0~9、bugfixes、project-assessment）|

---

## 实施阶段总览

| 阶段 | 名称 | 时间 | 核心产出 |
|------|------|------|----------|
| 0 | 环境准备 | 2026-06-23 | 24 表 / 三级缓存 / LangSmith / Docker |
| 1 | Agent 核心构建 | 2026-06-24 | LangGraph 12 节点 / SqliteSaver / 语义缓存 |
| 2 | 幻觉防御集成 | 2026-06-25 | 五层防御 / 拒答模板 / 引用追踪 / 时效检索 |
| 3 | 监控告警模块 | 2026-06-25 | KB 健康度 / LLM 成本 / 引用质量 / 4 cron |
| 4 | 问答服务升级 | 2026-06-25 | agent_chat() 集成 + /ask/agent 端点 |
| 5 | 路由 + Schema | 2026-06-25 | Schema 抽离 + 3 个监控路由 |
| 6 | 前端对接 | 2026-06-26 | 三栏布局 / Agent 组件 / 监控中心 |
| 7 | 外部检索扩展 | 2026-06-26 | Bing MCP + 站点白名单 + web 引用卡片 |
| 8 | 单智能体稳固期 | 2026-06-27 | verify_facts 增强 / AgentState 标准化 / 14 单测 |
| 9 | 单智能体扩展期 | 2026-06-27 | 5→3 工具（去债务）/ 9 类意图 / 公告后端接管 |
| 10 | 多智能体触发评估 | 2026-06-27 | 5 检查点全未触发 → 无需多 Agent |
| 11 | 复杂业务域开发 | 2026-06-27 | Batch A 收藏+公告 / Batch B 系统设置+QA配置+对话管理 |

---

## 当前技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 后端 | FastAPI + SQLAlchemy | 异步 Web 框架，30+ 路由 |
| Agent | LangGraph 1.2.6 | 12 节点固定流水线，SqliteSaver checkpoint |
| LLM | 通义千问 qwen3.7-max | DashScope OpenAI 兼容接口 |
| 向量 | ChromaDB 嵌入式 | kb_chunks collection，cosine 距离 |
| 缓存 | Redis（可选）+ 内存 LRU | Embedding 三级缓存（L1/L2/L3）|
| 数据库 | MySQL 8.x utf8mb4 | 24 张表 |
| 监控 | APScheduler + LangSmith | 4 个定时任务（KB 健康/成本/引用/一致性）|
| 前端 | Vue 3 + TypeScript + Vite | Pinia 状态管理，Element Plus，ECharts |

---

## 关键架构决策（详见 ADR）

- **检索**：ChromaDB 单路向量 + 时效调整，不引入 BM25/ES/Rerank
- **Agent**：单智能体 + 固定流水线，5 检查点触发才引入多智能体
- **三层定位法**：对话推理 → graph 节点；我方业务 → service+REST；外部 → MCP
- **去债务**：tools.py 注册表删除，5 个业务工具改为 REST

---

## 按场景查阅

| 需求 | 查阅 |
|------|------|
| 了解各模块文件职责 | [module-reference.md](./module-reference.md) |
| 执行数据库迁移 | [migration.md](./migration.md) |
| 理解 12 阶段演进 | [implementation-steps.md](./implementation-steps.md) |
| 历史阶段详细记录 | [docs/archive/](../../archive/) |
| 架构决策（Why）| [../../architecture/ARCHITECTURE_DECISIONS.md](../../architecture/ARCHITECTURE_DECISIONS.md) |
| 当前系统能力 | [../../modules/CURRENT_CAPABILITIES.md](../../modules/CURRENT_CAPABILITIES.md) |
| 最新业务域开发 | [../../progress/phase-11.md](../../progress/phase-11.md) |

---

## 文档来源

本实施指南的内容来源于：
- 设计架构：[../../architecture/ARCHITECTURE_DECISIONS.md](../../architecture/ARCHITECTURE_DECISIONS.md)
- 模块速查：[module-reference.md](./module-reference.md)（已精简，删除旧代码片段）
- 历史文档归档：[docs/archive/](../../archive/)（Agent模块融合实施方案.md、功能模块实现文档.md 等原始大文档）

