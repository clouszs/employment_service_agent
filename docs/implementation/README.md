# 实施指南总览

> 目录：`docs/implementation/`
> 适用：开发工程师执行 Agent 模块融合实施
> 前置阅读：[Agent模块设计文档](../Agent模块设计文档.md)

---

## 目录结构

| 文件 | 内容 |
|------|------|
| [README.md](./README.md) | 实施总览（本文件）+ 阶段快速入口 |
| [module-reference.md](./module-reference.md) | 模块速查：全模块文件清单、职责、代码片段 |
| [migration.md](./migration.md) | 数据库迁移：表结构、迁移脚本、执行验证 |
| [phase-0-environment.md](../progress/phase-0-environment.md) | 阶段 0：环境准备（依赖、迁移、缓存、LangSmith） |
| [phase-1-agent-core.md](../progress/phase-1-agent-core.md) | 阶段 1：Agent 核心（P0 骨架、P1 持久化/缓存/跑通、Docker） |
| [phase-2-hallucination-defense.md](../progress/phase-2-hallucination-defense.md) | 阶段 2：幻觉防御（动态阈值、一致性、事实核验、拒答模板） |
| [phase-3-monitoring.md](../progress/phase-3-monitoring.md) | 阶段 3：监控（知识库健康度、LLM 成本、引用质量评估） |
| [phase-4-qa-upgrade.md](../progress/phase-4-qa-upgrade.md) | 阶段 4：问答服务升级（Agent 工作流集成、`/ask/agent` 端点） |
| [phase-5-routing-schema.md](../progress/phase-5-routing-schema.md) | 阶段 5：路由 + Schema 补齐（监控路由、qa 响应对齐） |
| [phase-6-frontend.md](../progress/phase-6-frontend.md) | 阶段 6：前端对接（三栏布局、Agent 组件、监控中心） |
| [project-assessment.md](../progress/project-assessment.md) | 项目评估报告（幻觉/溯源/时效性/准确性分析 + 优化建议） |

---

## 实施阶段总览

| 阶段 | 状态 | 时间 | 核心产出 |
|------|------|------|----------|
| 阶段 0：环境准备 | ✅ 完成 | 2026-06-23 | Alembic 迁移(24表) / Embedding 三级缓存 / LangSmith 全局配置 |
| 阶段 1：Agent 核心构建 | ✅ 完成 | 2026-06-24 | P0 骨架 + P1 持久化/缓存/跑通 + Docker 部署 |
| 阶段 2：幻觉防御集成 | ✅ 完成 | 2026-06-25 | 动态阈值 / 一致性 / 事实核验 / 拒答模板 / 引用追踪 / 时效感知检索 |
| 阶段 3：监控告警模块 | ✅ 完成 | 2026-06-25 | 知识库健康度监控 + LLM 成本监控 + 引用质量评估 + APScheduler |
| 阶段 4：问答服务升级 | ✅ 完成 | 2026-06-25 | `qa_service.agent_chat()` 集成 Agent 工作流 + `/ask/agent` 端点 |
| 阶段 5：路由 + Schema | ✅ 完成 | 2026-06-25 | Schema 抽离 + 3 个监控路由（kb_health/llm_cost/refusal）+ qa.py 响应对齐 |
| 阶段 6：前端对接 | ✅ 完成 | 2026-06-25 ~ 2026-06-26 | 三栏布局 + Agent 组件 + 监控中心 + 样式升级 + bugfixes |
| 阶段 7：集成测试 + 灰度 | 🔄 进行中 | 2026-06-26 | 联调验证 / 学生端权限修复 / 问答显示修复 / 视觉样式升级 |

---

## 快速导航

### 按阶段阅读

```
阶段 0 → phase-0-environment.md
阶段 1 → phase-1-agent-core.md
阶段 2 → phase-2-hallucination-defense.md
阶段 3 → phase-3-monitoring.md
阶段 4 → phase-4-qa-upgrade.md
阶段 5 → phase-5-routing-schema.md
阶段 6 → phase-6-frontend.md
```

### 按任务查阅

| 任务 | 查阅文档 |
|------|----------|
| 了解某个模块的实现细节 | [module-reference.md](./module-reference.md) |
| 执行数据库迁移 | [migration.md](./migration.md) |
| 排查阶段 0 环境问题 | [phase-0-environment.md](../progress/phase-0-environment.md) |
| 理解 Agent 工作流设计 | [phase-1-agent-core.md](../progress/phase-1-agent-core.md) + [设计文档](../Agent模块设计文档.md) |
| 了解幻觉防御机制 | [phase-2-hallucination-defense.md](../progress/phase-2-hallucination-defense.md) |
| 配置监控告警 | [phase-3-monitoring.md](../progress/phase-3-monitoring.md) |
| 对接问答服务 | [phase-4-qa-upgrade.md](../progress/phase-4-qa-upgrade.md) |
| 前端对接实施 | [phase-6-frontend.md](../progress/phase-6-frontend.md) |

---

## 技术选型确认

| 技术 | 用途 | 状态 |
|------|------|------|
| **LangGraph** | Agent 状态机工作流 | ✅ 已安装 1.2.6 |
| **LangSmith** | LLM 调用追踪 + Prompt 管理 | ✅ 已全局配置 |
| **ChromaDB** | 向量存储 | ✅ 已存在 |
| **通义千问** | LLM 推理 | ✅ 已存在 |
| **MySQL** | 业务数据 | ✅ 已存在 |
| **Redis** | 缓存 + 向量库元数据 | ⚠️ 可选，无 Redis 自动降级 |
| **SQLAlchemy** | ORM | ✅ 已存在 |
| **FastAPI** | Web 框架 | ✅ 已存在 |
| **Alembic** | 数据库迁移 | ✅ 已配置 |
| **APScheduler** | 定时任务 | ✅ 已配置 |
| **Vue 3** | 前端框架 | ✅ 已存在 |
| **Pinia** | 前端状态管理 | ✅ 已存在 |
| **Element Plus** | UI 组件库 | ✅ 已存在 |
| **ECharts** | 前端图表 | ✅ 已安装（阶段 6 新增） |

---

## 文档来源说明

本实施指南的内容来源于：
- **原文档**：[Agent模块融合实施方案.md](../Agent模块融合实施方案.md)
- **提取内容**：[功能模块实现文档.md](../功能模块实现文档.md) 中的模块速查和迁移脚本

两份原文档合并后，实施相关内容统一归入 `docs/implementation/`，设计相关内容保留在 `Agent模块设计文档.md`。
