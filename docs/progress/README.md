# 项目进度追踪 — 索引

> 项目：高校智慧就业服务平台 — RAG + Agent 融合开发
> 创建时间：2026-06-23
> 最后更新：2026-06-25
> 关联文档：[Agent模块融合实施方案](../Agent模块融合实施方案.md) · [功能模块实现文档](../功能模块实现文档.md) · [产品介绍文档](../产品介绍文档.md)

---

## 进度概览

| 阶段 | 状态 | 开始时间 | 完成时间 | 备注 |
|------|------|----------|----------|------|
| 阶段 0：环境准备 | ✅ 完成 | 2026-06-23 | 2026-06-23 | Alembic+3迁移(24表)/Embedding三级缓存/LangSmith全局，详见文末权威记录 |
| 阶段 1：Agent 核心构建 | ✅ 完成 | 2026-06-24 | 2026-06-24 | P0 骨架 + P1 持久化/缓存/跑通 + Docker 部署文件，默认 agent_enabled=true（测试环境） |
| 阶段 2：幻觉防御集成 | ✅ 完成 | 2026-06-25 | 2026-06-25 | 动态阈值/一致性/事实核验/拒答模板/引用追踪/时效感知检索集成到节点流程 |
| 阶段 3：监控告警模块 | ✅ 完成 | 2026-06-25 | 2026-06-25 | 知识库健康度监控 + LLM 成本监控 + 引用质量评估 + APScheduler 定时任务 |
| 阶段 4：问答服务升级 | ✅ 完成 | 2026-06-25 | 2026-06-25 | qa_service.agent_chat() 集成 Agent 工作流 + routers/qa.py 新增 /ask/agent 端点 |
| 阶段 5：路由 + Schema | ✅ 完成 | 2026-06-25 | 2026-06-25 | schemas 抽离 + 3 个监控路由（kb_health/llm_cost/refusal）+ qa.py 响应对齐 |
| 阶段 6：前端对接 | 🔄 进行中 | 2026-06-25 | 三栏布局 + Agent 组件 + 监控中心 + 文档更新 |
| 阶段 7：集成测试 + 灰度 | ⏸️ 等待阶段 6 | — | — | |

---

## 已知风险与待确认事项

| 风险/问题 | 状态 | 说明 |
|-----------|------|------|
| Redis 可用性 | ✅ 已处理 | 本机未装 Redis；代码 Redis-ready，自动降级到 内存+MySQL，不影响功能 |
| langgraph API 兼容性 | ⚠️ 注意 | 实际安装 1.2.6（已内置 checkpoint）；固定大版本，关注 changelog |
| LangSmith API Key | ✅ 已处理 | 从环境变量 `LANGSMITH_API_KEY` 读取，凭证校验通过，project=myproject |
| 迁移方式选择 | ✅ 已定 | 采用 **Alembic**，脚本输出到 `backend/migrations/` |

---

## 各阶段详细文档

| 阶段 | 文件 | 说明 |
|------|------|------|
| 阶段 0 | [phase-0-environment.md](./phase-0-environment.md) | 环境准备：依赖管理、Alembic 迁移、Embedding 三级缓存、LangSmith 全局追踪 |
| 阶段 1 | [phase-1-agent-core.md](./phase-1-agent-core.md) | Agent 核心构建：P0 骨架、P1 持久化/缓存、跑通测试、Docker 部署、代码质量优化 |
| 阶段 2 | [phase-2-hallucination-defense.md](./phase-2-hallucination-defense.md) | 幻觉防御集成：拒答模板、引用追踪、时效感知检索、五重防护节点集成 |
| 阶段 3 | [phase-3-monitoring.md](./phase-3-monitoring.md) | 监控告警模块：知识库健康度、LLM 成本监控、引用质量评估、APScheduler 定时任务 |
| 阶段 4 | [phase-4-qa-upgrade.md](./phase-4-qa-upgrade.md) | 问答服务升级：qa_service.agent_chat() 集成 Agent 工作流 + /ask/agent 端点 |
| 阶段 5 | [phase-5-routing-schema.md](./phase-5-routing-schema.md) | Schema 补齐 + 监控路由（kb_health/llm_cost/refusal）+ qa.py 响应对齐 |
| Bug 修复 | [bugfixes.md](./bugfixes.md) | 修复 1-7 + 优化 8 + 修复后验证汇总 |
