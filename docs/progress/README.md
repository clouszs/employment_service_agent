# 项目进度追踪 — 索引

> 项目：高校智慧就业服务平台 — RAG + Agent 融合开发
> 创建时间：2026-06-23
> 最后更新：2026-07-02
> 关联文档：[implementation/README.md](../implementation/README.md) · [architecture/ARCHITECTURE_DECISIONS.md](../architecture/ARCHITECTURE_DECISIONS.md) · [modules/CURRENT_CAPABILITIES.md](../modules/CURRENT_CAPABILITIES.md)
> 历史文档（phase-0~9、bugfixes、project-assessment）已归档至 [docs/archive/](../archive/)，不再更新。

---

## 进度概览

| 阶段 | 状态 | 开始时间 | 完成时间 | 备注 |
|------|------|----------|----------|------|
| 阶段 0：环境准备 | ✅ 完成 | 2026-06-23 | 2026-06-23 | Alembic+3迁移(24表)/Embedding三级缓存/LangSmith全局 |
| 阶段 1：Agent 核心构建 | ✅ 完成 | 2026-06-24 | 2026-06-24 | P0 骨架 + P1 持久化/缓存/跑通 + Docker 部署文件，默认 agent_enabled=true |
| 阶段 2：幻觉防御集成 | ✅ 完成 | 2026-06-25 | 2026-06-25 | 动态阈值/一致性/事实核验/拒答模板/引用追踪/时效感知检索 |
| 阶段 3：监控告警模块 | ✅ 完成 | 2026-06-25 | 2026-06-25 | KB 健康度 + LLM 成本 + 引用质量 + APScheduler（4 个定时任务） |
| 阶段 4：问答服务升级 | ✅ 完成 | 2026-06-25 | 2026-06-25 | qa_service.agent_chat() 集成 Agent + /ask/agent 端点 |
| 阶段 5：路由 + Schema | ✅ 完成 | 2026-06-25 | 2026-06-25 | schemas 抽离 + 3 个监控路由 + qa 响应对齐 |
| 阶段 6：前端对接 | ✅ 完成 | 2026-06-25 | 2026-06-26 | 三栏布局 + Agent 组件 + 监控中心 + 样式升级 + bugfixes |
| 阶段 7：外部检索兜底 | ✅ 完成 | 2026-06-26 | 2026-06-26 | Bing MCP + 站点白名单 + 引用溯源 + 前端 web 来源展示 |
| 阶段 8：单智能体稳固期 | ✅ 完成 | 2026-06-27 | 2026-06-27 | verify_facts 基础验证增强 / AgentState TypedDict 标准化 / 14 个单元测试 |
| 阶段 9：单智能体扩展期 | ✅ 完成 | 2026-06-27 | 2026-06-27 | 5 个新工具（后瘦身为 3）+ 9 类意图 + direct_response 公告展示 |
| 阶段 10：多智能体触发评估 | ✅ 完成 | 2026-06-27 | 2026-06-27 | 5 项检查点全未触发，无需引入多智能体 |
| 阶段 11：复杂业务域开发 | ✅ 完成 | 2026-06-27 | 2026-06-27 | Batch A（收藏+公告）/ Batch B（系统设置+QA配置+对话管理），Batch C 待排期 |
| 增量优化 | ✅ 完成 | 2026-06-26 | 2026-06-26 | 终止按钮 / AbortController / 纯检索模式 / MonitorView 扩展 / Graph 缓存 |

---

## 已知风险与待确认事项

| 风险/问题 | 状态 | 说明 |
|-----------|------|------|
| Redis 可用性 | ✅ 已处理 | 本机未装 Redis；代码 Redis-ready，自动降级到 内存+MySQL，不影响功能 |
| langgraph API 兼容性 | ⚠️ 注意 | 实际安装 1.2.6（已内置 checkpoint）；固定大版本，关注 changelog |
| LangSmith API Key | ✅ 已处理 | 从环境变量 `LANGSMITH_API_KEY` 读取，凭证校验通过，project=myproject |
| 迁移方式选择 | ✅ 已定 | 采用 **Alembic**，脚本输出到 `backend/migrations/` |
| NewsAPI 免费版限制 | ✅ 已处理 | 已迁移到 Bing MCP，无此限制 |
| Agent 工具数封顶 | ⚠️ 注意 | 当前 8 个，触发阈值。阶段 11 新增工具必须先评估，见 phase-10.md |
| 多智能体引入时机 | ✅ 已定 | 阶段 10 评估完成，当前无需引入。触发条件见 phase-10.md |

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
| 阶段 6 | [phase-6-frontend.md](./phase-6-frontend.md) | 前端对接：三栏布局 + Agent 组件 + 监控中心 + 样式升级 + bugfixes |
| 阶段 7 | [phase-7-web-search-fallback.md](./phase-7-web-search-fallback.md) | 外部检索兜底：Bing MCP + 分级站点白名单 + 引用溯源 + 前端 web 来源展示 |
| Bug 修复 | [bugfixes.md](./bugfixes.md) | 修复 1-7 + 优化 8 + 修复后验证汇总 |
| 项目评估 | [project-assessment.md](./project-assessment.md) | V4.0 实施前的全面评估：幻觉/溯源/时效性/准确性分析 + 优化建议 |
| 阶段 10 | [phase-10.md](./phase-10.md) | 多智能体触发评估：5 项检查点清单 + 结论（无需引入）+ 触发信号监控 |
| 阶段 11 | [phase-11.md](./phase-11.md) | 复杂业务域开发：先 REST API 层，再前端页面 |
